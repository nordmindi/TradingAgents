import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tradingagents.agents.schemas import (
    EvidenceBalance,
    ExecutionBias,
    PortfolioDecision,
    PortfolioRating,
    ResearchPlan,
    TraderProposal,
    render_pm_decision,
    render_research_plan,
    render_trader_proposal,
)
from tradingagents.reporting import write_report_tree
from tradingagents.validation import (
    bollinger_squeeze_valid,
    build_dashboard_model,
    bullish_divergence,
    check_market_data_freshness,
    detect_cross,
    macd_components_reconcile,
    resolve_instrument,
    validate_final_state,
    ValidationResult,
)


def _state(**overrides):
    base = {
        "company_of_interest": "NVDA",
        "trade_date": "2026-06-26",
        "market_report": "Market observations only.",
        "sentiment_report": "Sentiment observations only.",
        "news_report": "News observations only.",
        "fundamentals_report": "Fundamental observations only.",
        "investment_plan": "Research synthesis without an explicit rating.",
        "trader_investment_plan": "Trading synthesis without an explicit action.",
        "final_trade_decision": "**Rating**: Hold\n\n**Executive Summary**: Balanced.",
        "instrument_resolution": {
            "requested_query": "NVDA",
            "status": "resolved",
            "selected_instrument_id": "yf:NVDA",
            "candidates": [
                {
                    "instrument_id": "yf:NVDA",
                    "requested_query": "NVDA",
                    "canonical_symbol": "NVDA",
                    "exchange": "NMS",
                    "currency": "USD",
                    "quote_type": "EQUITY",
                    "instrument_type": "ordinary_share",
                    "listed": True,
                    "otc": False,
                    "share_class": None,
                    "status": "active",
                    "source": "yfinance",
                }
            ],
            "warnings": [],
            "user_confirmation_required": False,
        },
        "market_data_freshness": {
            "ticker": "NVDA",
            "requested_as_of": "2026-06-26",
            "provider": "yfinance",
            "market_data_session": "2026-06-26",
            "sessions_stale": 0,
            "freshness_status": "fresh",
            "max_completed_sessions_old": 2,
            "recommendation_allowed": True,
            "warnings": [],
        },
        "technical_validation": {},
    }
    base.update(overrides)
    return base


@pytest.mark.unit
class TestReportValidation:
    def test_clean_legacy_state_is_research_only_not_verified(self):
        result = validate_final_state(
            _state(),
            expected_analysts=("market", "social", "news", "fundamentals"),
        )
        assert result.status == "research_only"
        assert result.status_label == "RESEARCH_OUTPUT"
        assert result.issues == []

    def test_missing_required_agent_blocks(self):
        result = validate_final_state(
            _state(news_report=""),
            expected_analysts=("market", "social", "news", "fundamentals"),
        )
        assert result.status == "blocked"
        assert result.has_blocking_issues
        assert result.blocking_issues[0].code == "FAILED_REQUIRED_AGENT"
        assert result.blocking_issues[0].location == "news_report"

    def test_specialist_recommendation_blocks(self):
        result = validate_final_state(
            _state(market_report="**Recommendation**: Buy\nTrend is favorable."),
            expected_analysts=("market",),
        )
        assert result.status == "blocked"
        assert [issue.code for issue in result.blocking_issues] == [
            "UNAUTHORIZED_RECOMMENDATION"
        ]

    def test_multiple_decision_recommendations_warn_by_default(self):
        result = validate_final_state(
            _state(
                investment_plan="**Recommendation**: Buy",
                trader_investment_plan="**Action**: Buy",
                final_trade_decision="**Rating**: Buy",
            )
        )
        issue = next(issue for issue in result.issues if issue.code == "MULTIPLE_RECOMMENDATIONS")
        assert issue.severity == "warning"
        assert result.status == "research_only"

    def test_multiple_decision_recommendations_block_in_strict_mode(self):
        result = validate_final_state(
            _state(
                investment_plan="**Recommendation**: Buy",
                trader_investment_plan="**Action**: Buy",
                final_trade_decision="**Rating**: Buy",
            ),
            strict_mode=True,
        )
        issue = next(issue for issue in result.issues if issue.code == "MULTIPLE_RECOMMENDATIONS")
        assert issue.severity == "blocking"
        assert result.status == "blocked"
        assert any(issue.code == "UNAUTHORIZED_RECOMMENDATION" for issue in result.blocking_issues)

    def test_strict_mode_allows_only_final_trade_decision_rating(self):
        result = validate_final_state(
            _state(
                investment_plan="Research synthesis with no recommendation line.",
                trader_investment_plan="Trader execution context with no action line.",
                final_trade_decision="**Rating**: Hold\n\n**Executive Summary**: Balanced.",
            ),
            strict_mode=True,
        )
        assert not any(
            issue.code in {"UNAUTHORIZED_RECOMMENDATION", "MULTIPLE_RECOMMENDATIONS"}
            for issue in result.issues
        )

    def test_strict_mode_passes_rendered_non_authoritative_handoffs(self):
        investment_plan = render_research_plan(
            ResearchPlan(
                evidence_balance=EvidenceBalance.BALANCED,
                bull_case_summary="Supported positives are present.",
                bear_case_summary="Material risks remain.",
                uncertainties=["Fresh guidance is not available."],
                decision_permitted=True,
                trader_context="Neutral execution context for later review.",
            )
        )
        trader_context = render_trader_proposal(
            TraderProposal(
                execution_bias=ExecutionBias.NEUTRAL,
                reasoning="Execution context remains balanced.",
                entry_context="Wait for cleaner evidence before acting.",
                risk_context="Event risk remains unresolved.",
                sizing_context="Sizing should be deferred to final review.",
            )
        )
        final_decision = render_pm_decision(
            PortfolioDecision(
                rating=PortfolioRating.HOLD,
                executive_summary="Maintain current posture pending better evidence.",
                investment_thesis="The evidence is balanced and unresolved risks remain.",
            )
        )

        result = validate_final_state(
            _state(
                investment_plan=investment_plan,
                trader_investment_plan=trader_context,
                final_trade_decision=final_decision,
            ),
            strict_mode=True,
        )
        assert not result.has_blocking_issues

    def test_strict_mode_blocks_missing_final_rating(self):
        result = validate_final_state(
            _state(
                investment_plan="Research synthesis.",
                trader_investment_plan="Trader execution context.",
                final_trade_decision="Executive summary without rating.",
            ),
            strict_mode=True,
        )
        assert result.status == "blocked"
        assert any(issue.code == "FINAL_RECOMMENDATION_MISSING" for issue in result.blocking_issues)

    def test_dashboard_body_mismatch_blocks(self):
        result = validate_final_state(
            _state(
                final_trade_decision="**Rating**: Hold\n\n**Executive Summary**: Balanced.",
                dashboard_model={
                    "report_status": "research_only",
                    "recommendation": "Buy",
                    "action": "Use final Portfolio Manager rating: Buy",
                    "target_low": None,
                    "target_base": None,
                    "target_high": None,
                    "sentiment": None,
                    "current_price": None,
                    "price_currency": "USD",
                    "price_as_of": "2026-06-26",
                    "data_quality_score": 100,
                },
            )
        )
        assert result.status == "blocked"
        assert any(issue.code == "DASHBOARD_UNSAFE_RECOMMENDATION" for issue in result.blocking_issues)

    def test_corrupted_output_blocks(self):
        result = validate_final_state(_state(news_report="Valid words " + "\x00" * 20))
        assert result.status == "blocked"
        assert any(issue.code == "CORRUPTED_AGENT_OUTPUT" for issue in result.blocking_issues)

    def test_ambiguous_instrument_blocks(self):
        result = validate_final_state(
            _state(
                instrument_resolution={
                    "requested_query": "SAAB A",
                    "status": "ambiguous",
                    "candidates": [],
                    "warnings": ["Ticker appears to include a free-form share class."],
                    "user_confirmation_required": True,
                }
            )
        )
        assert result.status == "blocked"
        assert any(issue.code == "INSTRUMENT_AMBIGUOUS" for issue in result.blocking_issues)

    def test_stale_market_data_blocks(self):
        result = validate_final_state(
            _state(
                market_data_freshness={
                    "ticker": "NVDA",
                    "requested_as_of": "2026-06-26",
                    "provider": "yfinance",
                    "market_data_session": "2026-05-07",
                    "sessions_stale": 35,
                    "freshness_status": "blocked",
                    "max_completed_sessions_old": 2,
                    "recommendation_allowed": False,
                    "warnings": ["Market data are 35 completed sessions old."],
                }
            )
        )
        assert result.status == "blocked"
        assert any(issue.code == "STALE_MARKET_DATA" for issue in result.blocking_issues)

    def test_stale_status_is_hard_recommendation_blocker(self):
        result = validate_final_state(
            _state(
                market_data_freshness={
                    "ticker": "NVDA",
                    "requested_as_of": "2026-06-26",
                    "provider": "yfinance",
                    "market_data_session": "2026-06-24",
                    "sessions_stale": 2,
                    "freshness_status": "stale",
                    "max_completed_sessions_old": 2,
                    "recommendation_allowed": True,
                    "warnings": ["Market data are stale."],
                }
            )
        )
        assert result.status == "blocked"
        assert any(issue.code == "STALE_MARKET_DATA" for issue in result.blocking_issues)

    def test_directional_rating_requires_verified_fundamentals(self):
        result = validate_final_state(
            _state(
                final_trade_decision="**Rating**: Overweight\n\n**Executive Summary**: Constructive.",
                fundamentals_report="No verified fundamentals were provided.",
            )
        )
        assert result.status == "blocked"
        assert any(
            issue.code == "FUNDAMENTALS_MISSING_FOR_DIRECTIONAL_RATING"
            for issue in result.blocking_issues
        )

    def test_current_price_mismatch_blocks(self):
        result = validate_final_state(
            _state(
                market_data_freshness={
                    "ticker": "TSLA",
                    "requested_as_of": "2026-06-26",
                    "provider": "yfinance",
                    "market_data_session": "2026-06-26",
                    "sessions_stale": 0,
                    "freshness_status": "fresh",
                    "max_completed_sessions_old": 2,
                    "recommendation_allowed": True,
                    "analyzed_price": 340,
                    "current_price": 425,
                    "warnings": [],
                }
            )
        )
        assert result.status == "blocked"
        assert any(issue.code == "CURRENT_PRICE_MISMATCH" for issue in result.blocking_issues)

    def test_price_target_requires_valuation_method(self):
        result = validate_final_state(
            _state(
                final_trade_decision=(
                    "**Rating**: Hold\n\n"
                    "**Executive Summary**: Balanced.\n\n"
                    "**Price Target**: 425"
                )
            )
        )
        assert result.status == "blocked"
        assert any(issue.code == "VALUATION_METHOD_MISSING" for issue in result.blocking_issues)

    def test_vwma_absent_from_market_report_blocks(self):
        result = validate_final_state(
            _state(
                market_report="Market report covers RSI and MACD only.",
                final_trade_decision=(
                    "**Rating**: Hold\n\n"
                    "**Executive Summary**: VWMA confirms the setup."
                ),
            )
        )
        assert result.status == "blocked"
        assert any(
            issue.code == "METRIC_ABSENT_FROM_ACTIVE_REPORT"
            for issue in result.blocking_issues
        )

    def test_historical_lessons_require_auditable_evidence(self):
        result = validate_final_state(
            _state(
                final_trade_decision=(
                    "**Rating**: Hold\n\n"
                    "**Executive Summary**: Prior lessons support caution."
                )
            )
        )
        assert result.status == "blocked"
        assert any(
            issue.code == "HISTORICAL_LESSON_EVIDENCE_MISSING"
            for issue in result.blocking_issues
        )

    def test_historical_lessons_pass_with_structured_evidence(self):
        result = validate_final_state(
            _state(
                final_trade_decision=(
                    "**Rating**: Hold\n\n"
                    "**Executive Summary**: Prior lessons support caution."
                ),
                historical_lessons_evidence=[
                    {
                        "date": "2026-05-01",
                        "ticker": "NVDA",
                        "decision": "Hold",
                        "outcome": "No transaction",
                    }
                ],
            )
        )
        assert not any(
            issue.code == "HISTORICAL_LESSON_EVIDENCE_MISSING"
            for issue in result.issues
        )


@pytest.mark.unit
class TestReportWriterValidation:
    def test_writes_validation_report(self, tmp_path):
        report_path = write_report_tree(
            _state(),
            "NVDA",
            tmp_path,
            expected_analysts=("market", "social", "news", "fundamentals"),
        )
        assert report_path.exists()

        validation_path = tmp_path / "validation_report.json"
        assert validation_path.exists()
        payload = json.loads(validation_path.read_text(encoding="utf-8"))
        assert payload["status"] == "research_only"

        dashboard_path = tmp_path / "dashboard.json"
        assert dashboard_path.exists()
        dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
        assert dashboard["recommendation"] == "INSUFFICIENT_EVIDENCE"
        assert dashboard["action"] == "No current transaction"

    def test_strict_validation_blocks_publication(self, tmp_path):
        with pytest.raises(ValueError, match="Report validation blocked publication"):
            write_report_tree(
                _state(
                    investment_plan="**Recommendation**: Buy",
                    trader_investment_plan="**Action**: Buy",
                    final_trade_decision="**Rating**: Buy",
                ),
                "NVDA",
                tmp_path,
                strict_validation=True,
            )

        validation_path = tmp_path / "validation_report.json"
        assert validation_path.exists()
        payload = json.loads(validation_path.read_text(encoding="utf-8"))
        assert payload["status"] == "blocked"


@pytest.mark.unit
class TestDashboardModel:
    def test_verified_dashboard_uses_final_pm_rating_and_target(self):
        state = _state(
            final_trade_decision=(
                "**Rating**: Overweight\n\n"
                "**Executive Summary**: Constructive.\n\n"
                "**Investment Thesis**: Evidence supports upside.\n\n"
                "**Price Target**: 215.50"
            )
        )
        validation = ValidationResult(status="verified")
        dashboard = build_dashboard_model(state, validation)
        assert dashboard.recommendation == "Overweight"
        assert str(dashboard.target_base) == "215.50"
        assert dashboard.pdf_metrics()["Recommendation"] == "Overweight"
        assert dashboard.pdf_metrics()["Target"] == "215.5"

    def test_research_only_dashboard_suppresses_actionable_rating(self):
        state = _state(
            final_trade_decision=(
                "**Rating**: Overweight\n\n"
                "**Executive Summary**: Constructive but not fully verified."
            )
        )
        validation = validate_final_state(state)
        dashboard = build_dashboard_model(state, validation)
        assert validation.status == "research_only"
        assert dashboard.recommendation == "INSUFFICIENT_EVIDENCE"
        assert dashboard.action == "No current transaction"
        assert dashboard.target_base is None

    def test_stale_market_data_dashboard_blocks_transaction(self):
        state = _state(
            final_trade_decision=(
                "**Rating**: Overweight\n\n"
                "**Executive Summary**: Favorable if data were current."
            ),
            market_data_freshness={
                "ticker": "TSLA",
                "requested_as_of": "2026-06-26",
                "provider": "yfinance",
                "market_data_session": "2026-05-07",
                "sessions_stale": 35,
                "freshness_status": "blocked",
                "max_completed_sessions_old": 2,
                "recommendation_allowed": False,
                "warnings": ["Technical data are stale."],
            },
        )
        validation = validate_final_state(state)
        dashboard = build_dashboard_model(state, validation)
        assert validation.status == "blocked"
        assert dashboard.recommendation == "INSUFFICIENT_EVIDENCE"
        assert dashboard.action == "No current transaction"


@pytest.mark.unit
class TestInstrumentResolution:
    def test_freeform_share_class_is_ambiguous(self):
        result = resolve_instrument("SAAB A")
        assert result.status == "ambiguous"
        assert result.user_confirmation_required is True

    def test_provider_symbol_substitution_requires_confirmation(self):
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "symbol": "SAABY",
            "exchange": "PNK",
            "currency": "USD",
            "quoteType": "EQUITY",
        }
        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = resolve_instrument("SAAB-B.ST")
        assert result.status == "resolved"
        assert result.user_confirmation_required is True
        assert "SAABY" in result.warnings[0]


@pytest.mark.unit
class TestMarketDataFreshness:
    def test_weekend_after_completed_session_is_fresh(self):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame(
            {"Close": [100.0]},
            index=pd.to_datetime(["2026-06-26"]),
        )
        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = check_market_data_freshness("NVDA", "2026-06-27")
        assert result.market_data_session.isoformat() == "2026-06-26"
        assert result.sessions_stale == 0
        assert result.freshness_status == "fresh"

    def test_old_session_blocks(self):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame(
            {"Close": [100.0]},
            index=pd.to_datetime(["2026-05-07"]),
        )
        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = check_market_data_freshness("NVDA", "2026-06-26", max_completed_sessions_old=2)
        assert result.freshness_status == "blocked"
        assert result.recommendation_allowed is False


@pytest.mark.unit
class TestTechnicalValidationFunctions:
    def test_saab_values_are_not_bullish_divergence(self):
        assert not bullish_divergence(
            price_low_1=30.71,
            price_low_2=29.93,
            indicator_low_1=35.26,
            indicator_low_2=34.96,
        )

    def test_bullish_divergence_requires_lower_price_and_higher_indicator(self):
        assert bullish_divergence(
            price_low_1=30.71,
            price_low_2=29.93,
            indicator_low_1=35.26,
            indicator_low_2=38.10,
        )

    def test_macd_components_reconcile(self):
        assert macd_components_reconcile(macd_line=1.25, signal_line=0.75, histogram=0.5)
        assert not macd_components_reconcile(macd_line=1.25, signal_line=0.75, histogram=0.2)

    def test_detect_cross_returns_only_actual_event(self):
        golden = detect_cross([99, 101], [100, 100], dates=["2026-06-25", "2026-06-26"])
        static_above = detect_cross([101, 102], [100, 100], dates=["2026-06-25", "2026-06-26"])
        assert golden == {"event": "golden_cross", "event_date": "2026-06-26"}
        assert static_above == {"event": "no_new_cross", "event_date": None}

    def test_bollinger_squeeze_requires_full_band_width(self):
        assert bollinger_squeeze_valid(
            upper_band=110,
            middle_band=100,
            lower_band=90,
            width_percentile=0.08,
            threshold=0.10,
        )
        assert not bollinger_squeeze_valid(
            upper_band=110,
            middle_band=100,
            lower_band=None,
            width_percentile=0.08,
            threshold=0.10,
        )


@pytest.mark.unit
class TestTechnicalReportValidation:
    def test_bullish_divergence_claim_without_metadata_blocks(self):
        result = validate_final_state(
            _state(market_report="RSI shows a bullish divergence after the new low.")
        )
        assert result.status == "blocked"
        assert any(issue.code == "FALSE_DIVERGENCE_CLAIM" for issue in result.blocking_issues)

    def test_bullish_divergence_claim_with_validated_metadata_passes(self):
        result = validate_final_state(
            _state(
                market_report="RSI shows a bullish divergence after the new low.",
                technical_validation={
                    "rsi_divergence": {
                        "validated": True,
                        "event": "bullish_divergence",
                        "price_low_1": 30.71,
                        "price_low_2": 29.93,
                        "indicator_low_1": 35.26,
                        "indicator_low_2": 38.10,
                    }
                },
            )
        )
        assert not any(issue.code == "FALSE_DIVERGENCE_CLAIM" for issue in result.issues)

    def test_macd_mismatch_blocks(self):
        result = validate_final_state(
            _state(
                technical_validation={
                    "macd": {
                        "macd_line": 1.25,
                        "signal_line": 0.75,
                        "histogram": 0.20,
                    }
                }
            )
        )
        assert result.status == "blocked"
        assert any(issue.code == "MACD_COMPONENT_MISMATCH" for issue in result.blocking_issues)

    def test_bollinger_squeeze_claim_without_full_validation_blocks(self):
        result = validate_final_state(
            _state(market_report="The stock is in a Bollinger squeeze setup.")
        )
        assert result.status == "blocked"
        assert any(issue.code == "BOLLINGER_SQUEEZE_UNPROVEN" for issue in result.blocking_issues)

    def test_golden_cross_static_relationship_without_event_blocks(self):
        result = validate_final_state(
            _state(
                market_report="The chart has a golden cross configuration.",
                technical_validation={
                    "moving_average_cross": {
                        "event": "no_new_cross",
                        "event_date": None,
                    }
                },
            )
        )
        assert result.status == "blocked"
        assert any(issue.code == "MOVING_AVERAGE_CROSS_UNPROVEN" for issue in result.blocking_issues)

    def test_atr_optimized_stop_claim_blocks(self):
        result = validate_final_state(
            _state(market_report="The optimized stop is 2x ATR below entry.")
        )
        assert result.status == "blocked"
        assert any(issue.code == "ATR_SIZING_LOGIC_ERROR" for issue in result.blocking_issues)

    def test_bull_research_divergence_claim_blocks(self):
        result = validate_final_state(
            _state(
                investment_debate_state={
                    "bull_history": "RSI bullish divergence confirms upside.",
                    "bear_history": "",
                    "judge_decision": "",
                }
            )
        )
        assert result.status == "blocked"
        assert any(issue.code == "FALSE_DIVERGENCE_CLAIM" for issue in result.blocking_issues)

    def test_risk_volume_inference_claim_blocks(self):
        result = validate_final_state(
            _state(
                risk_debate_state={
                    "aggressive_history": "",
                    "conservative_history": "Volume shows institutional accumulation.",
                    "neutral_history": "",
                    "judge_decision": "",
                }
            )
        )
        assert result.status == "blocked"
        assert any(
            issue.code == "UNSUPPORTED_VOLUME_INFERENCE"
            for issue in result.blocking_issues
        )
