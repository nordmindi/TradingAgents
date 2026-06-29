from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

from tradingagents.agents.utils.rating import parse_rating

from .models import ValidationIssue, ValidationResult
from .dashboard import validate_dashboard_consistency
from .technical import validate_technical_claims


ANALYST_REPORT_KEYS = {
    "market": "market_report",
    "social": "sentiment_report",
    "news": "news_report",
    "fundamentals": "fundamentals_report",
}

SPECIALIST_REPORT_KEYS = set(ANALYST_REPORT_KEYS.values())

DECISION_FIELDS = (
    "investment_plan",
    "trader_investment_plan",
    "final_trade_decision",
)

RECOMMENDATION_LINE_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?"
    r"(recommendation|rating|action|final transaction proposal)"
    r"(?:\*\*)?\s*[:\-]\s*(?:\*\*)?"
    r"(buy|sell|hold|overweight|underweight|insufficient evidence|accumulate|reduce)"
)

FINAL_PROPOSAL_RE = re.compile(
    r"(?i)\bFINAL\s+TRANSACTION\s+PROPOSAL\s*:\s*(?:\*\*)?"
    r"(BUY|SELL|HOLD)"
)

DIRECTIONAL_RATINGS = {"Buy", "Overweight", "Underweight", "Sell"}

PRICE_TARGET_RE = re.compile(
    r"(?im)^\s*(?:\*\*)?(?:price\s+target|target\s+price)(?:\*\*)?\s*[:\-]\s*\$?[0-9]",
)

VALUATION_METHOD_RE = re.compile(
    r"(?i)\b(valuation|method|methodology|dcf|discounted cash flow|multiple|"
    r"p/e|ev/ebitda|sum-of-the-parts|fair value|scenario|comparable)\b",
)

UNVERIFIED_FUNDAMENTALS_RE = re.compile(
    r"(?i)\b(no verified fundamentals|fundamentals? (?:not available|unavailable|missing)|"
    r"unable to retrieve fundamentals|failed to retrieve fundamentals|insufficient fundamentals)\b",
)

AUDITABLE_LESSON_KEYS = {
    "historical_lessons_evidence",
    "memory_evidence",
    "auditable_lessons",
}

LESSON_REFERENCE_RE = re.compile(
    r"(?i)\b(prior decisions?|past decisions?|historical lessons?|prior lessons?|"
    r"memory|lessons? learned)\b",
)

TECHNICAL_METRICS_REQUIRING_ACTIVE_REPORT = {
    "VWMA": re.compile(r"(?i)\bVWMA\b|volume[-\s]?weighted moving average"),
}


def validate_final_state(
    final_state: dict,
    *,
    expected_analysts: Iterable[str] | None = None,
    strict_mode: bool = False,
) -> ValidationResult:
    """Validate a completed graph state before publication.

    The current application still stores canonical report content as Markdown
    strings. This validator is intentionally conservative: it catches known
    publication risks without requiring the larger structured-state migration.
    """
    issues: list[ValidationIssue] = []
    expected_keys = _expected_report_keys(expected_analysts)

    issues.extend(_validate_required_agent_outputs(final_state, expected_keys))
    issues.extend(_validate_instrument_resolution(final_state))
    issues.extend(_validate_market_data_freshness(final_state))
    issues.extend(_validate_current_price_alignment(final_state))
    issues.extend(validate_technical_claims(final_state))
    issues.extend(_validate_dashboard_body_consistency(final_state))
    issues.extend(_validate_output_integrity(final_state))
    issues.extend(_validate_recommendation_authority(final_state))
    issues.extend(_validate_decision_recommendations(final_state, strict_mode=strict_mode))
    issues.extend(_validate_directional_decision_evidence(final_state))
    issues.extend(_validate_price_target_methodology(final_state))
    issues.extend(_validate_metrics_exist_in_active_report(final_state))
    issues.extend(_validate_historical_lessons_are_auditable(final_state))

    if any(issue.severity == "blocking" for issue in issues):
        status = "blocked"
    elif issues:
        status = "verified_with_warnings" if strict_mode else "research_only"
    else:
        # Full verification requires structured evidence, sources, freshness,
        # and renderer type guards. Until those exist, avoid ANALYST_VERIFIED.
        status = "research_only"

    return ValidationResult(
        status=status,
        strict_mode=strict_mode,
        issues=issues,
        metadata=_validation_metadata(final_state),
    )


def _expected_report_keys(expected_analysts: Iterable[str] | None) -> set[str]:
    if expected_analysts is None:
        return set()
    return {
        ANALYST_REPORT_KEYS[name]
        for name in expected_analysts
        if name in ANALYST_REPORT_KEYS
    }


def _validate_required_agent_outputs(
    final_state: dict,
    expected_report_keys: set[str],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    for key in sorted(expected_report_keys):
        if not str(final_state.get(key, "")).strip():
            issues.append(
                ValidationIssue(
                    code="FAILED_REQUIRED_AGENT",
                    severity="blocking",
                    location=key,
                    message=f"Required report field '{key}' is empty.",
                )
            )

    if not str(final_state.get("final_trade_decision", "")).strip():
        issues.append(
            ValidationIssue(
                code="FAILED_REQUIRED_AGENT",
                severity="blocking",
                location="final_trade_decision",
                message="Final portfolio decision is empty.",
            )
        )

    return issues


def _validate_dashboard_body_consistency(final_state: dict) -> list[ValidationIssue]:
    return [
        ValidationIssue(
            code=issue["code"],
            severity="blocking",
            location=issue["location"],
            message=issue["message"],
        )
        for issue in validate_dashboard_consistency(final_state)
    ]


def _validate_instrument_resolution(final_state: dict) -> list[ValidationIssue]:
    resolution = _as_dict(final_state.get("instrument_resolution"))
    if not resolution:
        return [
            ValidationIssue(
                code="INSTRUMENT_METADATA_MISSING",
                severity="warning",
                location="instrument_resolution",
                message="Instrument resolution metadata is missing.",
            )
        ]

    status = resolution.get("status")
    warnings = "; ".join(resolution.get("warnings") or [])
    if status == "resolved" and not resolution.get("user_confirmation_required"):
        return []

    if status == "ambiguous":
        code = "INSTRUMENT_AMBIGUOUS"
    elif status == "unlisted":
        code = "UNLISTED_INSTRUMENT_ANALYZED_AS_LISTED"
    elif resolution.get("user_confirmation_required"):
        code = "INSTRUMENT_SUBSTITUTED_WITHOUT_CONFIRMATION"
    else:
        code = "INSTRUMENT_AMBIGUOUS"

    return [
        ValidationIssue(
            code=code,
            severity="blocking",
            location="instrument_resolution",
            message=warnings or f"Instrument resolution status is '{status}'.",
        )
    ]


def _validate_market_data_freshness(final_state: dict) -> list[ValidationIssue]:
    freshness = _as_dict(final_state.get("market_data_freshness"))
    if not freshness:
        return [
            ValidationIssue(
                code="MARKET_DATA_FRESHNESS_MISSING",
                severity="warning",
                location="market_data_freshness",
                message="Market-data freshness metadata is missing.",
            )
        ]

    status = freshness.get("freshness_status")
    if status == "fresh" and freshness.get("recommendation_allowed") is not False:
        return []

    message = "; ".join(freshness.get("warnings") or [])
    if not message:
        message = f"Market-data freshness status is '{status}'."
    return [
        ValidationIssue(
            code="STALE_MARKET_DATA",
            severity="blocking",
            location="market_data_freshness",
            message=message,
        )
    ]


def _validate_current_price_alignment(final_state: dict) -> list[ValidationIssue]:
    freshness = _as_dict(final_state.get("market_data_freshness")) or {}
    delta_pct = _coerce_float(
        freshness.get("price_delta_percent")
        or freshness.get("price_delta_pct")
        or freshness.get("current_price_delta_pct")
    )

    analyzed_price = _coerce_float(
        freshness.get("analyzed_price")
        or freshness.get("market_data_price")
        or freshness.get("analysis_price")
    )
    current_price = _coerce_float(
        freshness.get("current_price")
        or freshness.get("latest_price")
    )
    if delta_pct is None and analyzed_price not in (None, 0) and current_price is not None:
        delta_pct = abs(current_price - analyzed_price) / abs(analyzed_price) * 100

    if delta_pct is None or abs(delta_pct) < 3:
        return []

    return [
        ValidationIssue(
            code="CURRENT_PRICE_MISMATCH",
            severity="blocking",
            location="market_data_freshness",
            message=(
                "Current price differs materially from the analyzed price "
                f"({delta_pct:.2f}%)."
            ),
        )
    ]


def _validate_directional_decision_evidence(final_state: dict) -> list[ValidationIssue]:
    final_decision = str(final_state.get("final_trade_decision", ""))
    rating = parse_rating(final_decision, default="NOT_AVAILABLE")
    if rating not in DIRECTIONAL_RATINGS:
        return []

    fundamentals = str(final_state.get("fundamentals_report", "")).strip()
    if not fundamentals or UNVERIFIED_FUNDAMENTALS_RE.search(fundamentals):
        return [
            ValidationIssue(
                code="FUNDAMENTALS_MISSING_FOR_DIRECTIONAL_RATING",
                severity="blocking",
                location="fundamentals_report",
                message=(
                    f"Directional Portfolio Manager rating '{rating}' requires "
                    "current verified fundamentals."
                ),
            )
        ]
    return []


def _validate_price_target_methodology(final_state: dict) -> list[ValidationIssue]:
    final_decision = str(final_state.get("final_trade_decision", ""))
    if not PRICE_TARGET_RE.search(final_decision):
        return []
    if VALUATION_METHOD_RE.search(final_decision):
        return []
    return [
        ValidationIssue(
            code="VALUATION_METHOD_MISSING",
            severity="blocking",
            location="final_trade_decision",
            message="Price targets require a documented valuation method or scenario basis.",
        )
    ]


def _validate_metrics_exist_in_active_report(final_state: dict) -> list[ValidationIssue]:
    market_report = str(final_state.get("market_report", ""))
    issues: list[ValidationIssue] = []
    for metric, pattern in TECHNICAL_METRICS_REQUIRING_ACTIVE_REPORT.items():
        if pattern.search(market_report):
            continue
        for key, text in _iter_text_fields(final_state):
            if key == "market_report":
                continue
            if pattern.search(text):
                issues.append(
                    ValidationIssue(
                        code="METRIC_ABSENT_FROM_ACTIVE_REPORT",
                        severity="blocking",
                        location=key,
                        message=f"{metric} was referenced outside the active market report.",
                    )
                )
                break
    return issues


def _validate_historical_lessons_are_auditable(final_state: dict) -> list[ValidationIssue]:
    final_decision = str(final_state.get("final_trade_decision", ""))
    if not LESSON_REFERENCE_RE.search(final_decision):
        return []

    has_structured_evidence = any(final_state.get(key) for key in AUDITABLE_LESSON_KEYS)
    if has_structured_evidence:
        return []

    return [
        ValidationIssue(
            code="HISTORICAL_LESSON_EVIDENCE_MISSING",
            severity="blocking",
            location="final_trade_decision",
            message="Historical lessons require structured, auditable evidence before use.",
        )
    ]


def _validate_output_integrity(final_state: dict) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for key, text in _iter_text_fields(final_state):
        if not text.strip():
            continue

        if _printable_ratio(text) < 0.95:
            issues.append(
                ValidationIssue(
                    code="CORRUPTED_AGENT_OUTPUT",
                    severity="blocking",
                    location=key,
                    message="Output contains too many non-printable characters.",
                )
            )

        if _repeated_ngram_ratio(text, n=4) > 0.20:
            issues.append(
                ValidationIssue(
                    code="INCOHERENT_AGENT_OUTPUT",
                    severity="blocking",
                    location=key,
                    message="Output contains excessive repeated token sequences.",
                )
            )

        if _unmatched_markup_count(text) > 10:
            issues.append(
                ValidationIssue(
                    code="MALFORMED_MARKUP",
                    severity="blocking",
                    location=key,
                    message="Output contains excessive unmatched Markdown markup.",
                )
            )

    return issues


def _validation_metadata(final_state: dict) -> dict:
    metadata = {}
    for key in ("instrument_resolution", "market_data_freshness", "technical_validation", "dashboard_model"):
        value = final_state.get(key)
        if value is not None:
            metadata[key] = _as_dict(value)
    return metadata


def _as_dict(value):
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    return None


def _validate_recommendation_authority(final_state: dict) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for key in SPECIALIST_REPORT_KEYS:
        text = str(final_state.get(key, ""))
        if not text.strip():
            continue
        match = RECOMMENDATION_LINE_RE.search(text)
        if match:
            issues.append(
                ValidationIssue(
                    code="UNAUTHORIZED_RECOMMENDATION",
                    severity="blocking",
                    location=key,
                    message=(
                        f"Specialist report '{key}' contains a recommendation "
                        f"line: {match.group(0).strip()}"
                    ),
                )
            )
    return issues


def _validate_decision_recommendations(
    final_state: dict,
    *,
    strict_mode: bool,
) -> list[ValidationIssue]:
    recommendations: list[tuple[str, str]] = []
    for key in DECISION_FIELDS:
        text = str(final_state.get(key, ""))
        for match in RECOMMENDATION_LINE_RE.finditer(text):
            recommendations.append((key, match.group(2).upper()))

    if not recommendations:
        return [
            ValidationIssue(
                code="FINAL_RECOMMENDATION_MISSING",
                severity="blocking" if strict_mode else "warning",
                location="final_trade_decision",
                message="No final Portfolio Manager rating was found.",
            )
        ]

    if strict_mode:
        final_recommendations = [
            recommendation
            for recommendation in recommendations
            if recommendation[0] == "final_trade_decision"
        ]
        unauthorized = [
            recommendation
            for recommendation in recommendations
            if recommendation[0] != "final_trade_decision"
        ]
        issues: list[ValidationIssue] = []
        if len(final_recommendations) != 1:
            issues.append(
                ValidationIssue(
                    code="FINAL_RECOMMENDATION_MISSING",
                    severity="blocking",
                    location="final_trade_decision",
                    message="Strict mode requires exactly one Portfolio Manager rating.",
                )
            )
        if unauthorized:
            locations = ", ".join(f"{key}={value}" for key, value in unauthorized)
            issues.append(
                ValidationIssue(
                    code="UNAUTHORIZED_RECOMMENDATION",
                    severity="blocking",
                    location=";".join(key for key, _ in unauthorized),
                    message=(
                        "Strict mode permits recommendations only in "
                        f"final_trade_decision. Found: {locations}."
                    ),
                )
            )
        if len(recommendations) > 1:
            locations = ", ".join(f"{key}={value}" for key, value in recommendations)
            issues.append(
                ValidationIssue(
                    code="MULTIPLE_RECOMMENDATIONS",
                    severity="blocking",
                    location=";".join(key for key, _ in recommendations),
                    message=f"Multiple internal recommendation lines found: {locations}.",
                )
            )
        return issues

    if len(recommendations) <= 1:
        return []

    locations = ", ".join(f"{key}={value}" for key, value in recommendations)
    return [
        ValidationIssue(
            code="MULTIPLE_RECOMMENDATIONS",
            severity="warning",
            location=";".join(key for key, _ in recommendations),
            message=f"Multiple internal recommendation lines found: {locations}.",
        )
    ]


def _iter_text_fields(final_state: dict) -> list[tuple[str, str]]:
    fields = [
        (key, str(final_state.get(key, "")))
        for key in (
            "market_report",
            "sentiment_report",
            "news_report",
            "fundamentals_report",
            "investment_plan",
            "trader_investment_plan",
            "final_trade_decision",
        )
    ]

    debate = final_state.get("investment_debate_state") or {}
    if isinstance(debate, dict):
        for key in ("bull_history", "bear_history", "judge_decision"):
            fields.append((f"investment_debate_state.{key}", str(debate.get(key, ""))))

    risk = final_state.get("risk_debate_state") or {}
    if isinstance(risk, dict):
        for key in (
            "aggressive_history",
            "conservative_history",
            "neutral_history",
            "judge_decision",
        ):
            fields.append((f"risk_debate_state.{key}", str(risk.get(key, ""))))

    return fields


def _printable_ratio(text: str) -> float:
    if not text:
        return 1.0
    printable = sum(1 for char in text if char.isprintable() or char in "\r\n\t")
    return printable / len(text)


def _repeated_ngram_ratio(text: str, n: int) -> float:
    tokens = re.findall(r"\w+", text.lower())
    if len(tokens) < n * 3:
        return 0.0
    ngrams = [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]
    counts = Counter(ngrams)
    repeated = sum(count - 1 for count in counts.values() if count > 1)
    return repeated / len(ngrams)


def _unmatched_markup_count(text: str) -> int:
    return abs(text.count("**") % 2) + abs(text.count("```") % 2) * 3


def _coerce_float(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
