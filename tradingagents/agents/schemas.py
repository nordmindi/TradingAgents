"""Pydantic schemas used by agents that produce structured output.

The framework's primary artifact is still prose: each agent's natural-language
reasoning is what users read in the saved markdown reports and what the
downstream agents read as context.  Structured output is layered onto the
three decision-making agents (Research Manager, Trader, Portfolio Manager)
so that:

- Their outputs follow consistent section headers across runs and providers
- Each provider's native structured-output mode is used (json_schema for
  OpenAI/xAI, response_schema for Gemini, tool-use for Anthropic)
- Schema field descriptions become the model's output instructions, freeing
  the prompt body to focus on context and the rating-scale guidance
- A render helper turns the parsed Pydantic instance back into the same
  markdown shape the rest of the system already consumes, so display,
  memory log, and saved reports keep working unchanged
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared rating types
# ---------------------------------------------------------------------------


class PortfolioRating(str, Enum):
    """Final Portfolio Manager rating."""

    BUY = "Buy"
    OVERWEIGHT = "Overweight"
    HOLD = "Hold"
    UNDERWEIGHT = "Underweight"
    SELL = "Sell"
    INSUFFICIENT_EVIDENCE = "Insufficient Evidence"


class EvidenceBalance(str, Enum):
    """Non-authoritative research synthesis used before the final decision."""

    BULL_CASE_STRONGER = "Bull case stronger"
    BALANCED = "Balanced"
    BEAR_CASE_STRONGER = "Bear case stronger"
    INSUFFICIENT_EVIDENCE = "Insufficient evidence"


class ExecutionBias(str, Enum):
    """Non-final trading desk context handed to the Portfolio Manager."""

    CONSTRUCTIVE = "Constructive"
    NEUTRAL = "Neutral"
    DEFENSIVE = "Defensive"
    INSUFFICIENT_EVIDENCE = "Insufficient evidence"


# ---------------------------------------------------------------------------
# Research Manager
# ---------------------------------------------------------------------------


class ResearchPlan(BaseModel):
    """Structured research synthesis produced by the Research Manager.

    The Research Manager no longer issues a recommendation. Its job is to
    summarize the bull/bear evidence and identify whether the evidence is
    complete enough for later decision stages.
    """

    evidence_balance: EvidenceBalance = Field(
        description=(
            "Non-final balance of evidence. Do not use Buy, Sell, Hold, "
            "Overweight, or Underweight."
        ),
    )
    bull_case_summary: str = Field(
        description="Concise summary of the strongest supported bull arguments.",
    )
    bear_case_summary: str = Field(
        description="Concise summary of the strongest supported bear arguments.",
    )
    uncertainties: list[str] = Field(
        default_factory=list,
        description="Material unresolved questions, missing evidence, or contradictions.",
    )
    decision_permitted: bool = Field(
        description="Whether the evidence set is complete enough for later decision review.",
    )
    trader_context: str = Field(
        description="Non-final execution context for the Trader. Do not recommend a transaction.",
    )


def render_research_plan(plan: ResearchPlan) -> str:
    """Render a ResearchPlan to markdown for storage and the trader's prompt context."""
    parts = [
        f"**Evidence Balance**: {plan.evidence_balance.value}",
        "",
        f"**Bull Case Summary**: {plan.bull_case_summary}",
        "",
        f"**Bear Case Summary**: {plan.bear_case_summary}",
        "",
        f"**Decision Permitted**: {'Yes' if plan.decision_permitted else 'No'}",
        "",
        f"**Trader Context**: {plan.trader_context}",
    ]
    if plan.uncertainties:
        parts.extend(["", "**Uncertainties**:"])
        parts.extend(f"- {item}" for item in plan.uncertainties)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Trader
# ---------------------------------------------------------------------------


class TraderProposal(BaseModel):
    """Structured execution context produced by the Trader.

    The Trader no longer issues a final transaction proposal. It translates
    the research synthesis into execution context for the Portfolio Manager.
    """

    execution_bias: ExecutionBias = Field(
        description=(
            "Non-final execution bias. Do not use Buy, Sell, Hold, Overweight, "
            "or Underweight."
        ),
    )
    reasoning: str = Field(
        description=(
            "The case for this execution context, anchored in the analysts' "
            "reports and the research synthesis. Two to four sentences."
        ),
    )
    entry_context: Optional[str] = Field(
        default=None,
        description="Optional entry context without issuing a transaction command.",
    )
    risk_context: Optional[str] = Field(
        default=None,
        description="Optional stop/risk context without presenting an optimized stop.",
    )
    sizing_context: Optional[str] = Field(
        default=None,
        description="Optional sizing context, not a final position-size instruction.",
    )


def render_trader_proposal(proposal: TraderProposal) -> str:
    """Render a TraderProposal to markdown for downstream context."""
    parts = [
        f"**Execution Bias**: {proposal.execution_bias.value}",
        "",
        f"**Reasoning**: {proposal.reasoning}",
    ]
    if proposal.entry_context is not None:
        parts.extend(["", f"**Entry Context**: {proposal.entry_context}"])
    if proposal.risk_context is not None:
        parts.extend(["", f"**Risk Context**: {proposal.risk_context}"])
    if proposal.sizing_context:
        parts.extend(["", f"**Sizing Context**: {proposal.sizing_context}"])
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Portfolio Manager
# ---------------------------------------------------------------------------


class PortfolioDecision(BaseModel):
    """Structured output produced by the Portfolio Manager.

    The model fills every field as part of its primary LLM call; no separate
    extraction pass is required. Field descriptions double as the model's
    output instructions, so the prompt body only needs to convey context and
    the rating-scale guidance.
    """

    rating: PortfolioRating = Field(
        description=(
            "The final position rating. Use Insufficient Evidence when market "
            "data are stale, current fundamentals are missing, required evidence "
            "is not auditable, or a price target lacks a valuation method. "
            "Otherwise use exactly one of Buy / Overweight / Hold / Underweight / Sell."
        ),
    )
    executive_summary: str = Field(
        description=(
            "A concise action plan covering entry strategy, position sizing, "
            "key risk levels, and time horizon. Two to four sentences."
        ),
    )
    investment_thesis: str = Field(
        description=(
            "Detailed reasoning anchored in specific evidence from the analysts' "
            "debate. If prior lessons are referenced in the prompt context, "
            "incorporate them; otherwise rely solely on the current analysis."
        ),
    )
    price_target: Optional[float] = Field(
        default=None,
        description=(
            "Optional target price in the instrument's quote currency. Include "
            "only when the investment thesis documents a valuation method or "
            "scenario basis."
        ),
    )
    valuation_method: Optional[str] = Field(
        default=None,
        description=(
            "Required when price_target is present. State the valuation method, "
            "scenario basis, or comparable-multiple basis used for the target."
        ),
    )
    time_horizon: Optional[str] = Field(
        default=None,
        description="Optional recommended holding period, e.g. '3-6 months'.",
    )


def render_pm_decision(decision: PortfolioDecision) -> str:
    """Render a PortfolioDecision back to the markdown shape the rest of the system expects.

    Memory log, CLI display, and saved report files all read this markdown,
    so the rendered output preserves the exact section headers (``**Rating**``,
    ``**Executive Summary**``, ``**Investment Thesis**``) that downstream
    parsers and the report writers already handle.
    """
    parts = [
        f"**Rating**: {decision.rating.value}",
        "",
        f"**Executive Summary**: {decision.executive_summary}",
        "",
        f"**Investment Thesis**: {decision.investment_thesis}",
    ]
    if decision.price_target is not None:
        parts.extend(["", f"**Price Target**: {decision.price_target}"])
    if decision.valuation_method:
        parts.extend(["", f"**Valuation Method**: {decision.valuation_method}"])
    if decision.time_horizon:
        parts.extend(["", f"**Time Horizon**: {decision.time_horizon}"])
    return "\n".join(parts)
