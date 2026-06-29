"""Reusable report-tree writer shared by the CLI and the programmatic API.

Writes a run's per-section markdown (analysts, research, trading, risk,
portfolio) plus a consolidated ``complete_report.md`` under ``save_path``. The
CLI and ``TradingAgentsGraph.save_reports`` both call this, so a headless / API
run produces the same on-disk report tree a CLI run does.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
from pathlib import Path
from typing import Any

from tradingagents.validation import DashboardModel, ValidationResult, build_dashboard_model, validate_final_state


def finalize_validation_artifacts(
    final_state: dict,
    *,
    validation_result: ValidationResult | None = None,
    dashboard_model: DashboardModel | None = None,
    expected_analysts: tuple[str, ...] | list[str] | None = None,
    strict_validation: bool = False,
) -> tuple[ValidationResult, DashboardModel]:
    """Build and validate publication artifacts in final-gate order."""
    if validation_result is None:
        validation_result = validate_final_state(
            final_state,
            expected_analysts=expected_analysts,
            strict_mode=strict_validation,
        )

    dashboard_model = dashboard_model or build_dashboard_model(final_state, validation_result)
    final_state["dashboard_model"] = dashboard_model.model_dump(mode="json")
    validation_result = validate_final_state(
        final_state,
        expected_analysts=expected_analysts,
        strict_mode=strict_validation,
    )

    rebuilt_dashboard = build_dashboard_model(final_state, validation_result)
    if rebuilt_dashboard != dashboard_model:
        dashboard_model = rebuilt_dashboard
        final_state["dashboard_model"] = dashboard_model.model_dump(mode="json")
        validation_result = validate_final_state(
            final_state,
            expected_analysts=expected_analysts,
            strict_mode=strict_validation,
        )

    return validation_result, dashboard_model


def write_report_tree(
    final_state: dict,
    ticker: str,
    save_path,
    *,
    validation_result: ValidationResult | None = None,
    dashboard_model: DashboardModel | None = None,
    expected_analysts: tuple[str, ...] | list[str] | None = None,
    strict_validation: bool = False,
) -> Path:
    """Save a completed run's reports to ``save_path``; return the complete-report path."""
    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)

    validation_result, dashboard_model = finalize_validation_artifacts(
        final_state,
        validation_result=validation_result,
        dashboard_model=dashboard_model,
        expected_analysts=expected_analysts,
        strict_validation=strict_validation,
    )
    write_validation_report(save_path, validation_result)
    write_dashboard_report(save_path, dashboard_model)

    if strict_validation and validation_result.has_blocking_issues:
        codes = ", ".join(issue.code for issue in validation_result.blocking_issues)
        raise ValueError(f"Report validation blocked publication: {codes}")

    sections = []

    # 1. Analysts
    analysts_dir = save_path / "1_analysts"
    analyst_parts = []
    if final_state.get("market_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "market.md").write_text(final_state["market_report"], encoding="utf-8")
        analyst_parts.append(("Market Analyst", final_state["market_report"]))
    if final_state.get("sentiment_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "sentiment.md").write_text(final_state["sentiment_report"], encoding="utf-8")
        analyst_parts.append(("Sentiment Analyst", final_state["sentiment_report"]))
    if final_state.get("news_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "news.md").write_text(final_state["news_report"], encoding="utf-8")
        analyst_parts.append(("News Analyst", final_state["news_report"]))
    if final_state.get("fundamentals_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "fundamentals.md").write_text(final_state["fundamentals_report"], encoding="utf-8")
        analyst_parts.append(("Fundamentals Analyst", final_state["fundamentals_report"]))
    if analyst_parts:
        content = "\n\n".join(f"### {name}\n{text}" for name, text in analyst_parts)
        sections.append(f"## I. Analyst Team Reports\n\n{content}")

    # 2. Research
    if final_state.get("investment_debate_state"):
        research_dir = save_path / "2_research"
        debate = final_state["investment_debate_state"]
        research_parts = []
        if debate.get("bull_history"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "bull.md").write_text(debate["bull_history"], encoding="utf-8")
            research_parts.append(("Bull Researcher", debate["bull_history"]))
        if debate.get("bear_history"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "bear.md").write_text(debate["bear_history"], encoding="utf-8")
            research_parts.append(("Bear Researcher", debate["bear_history"]))
        if debate.get("judge_decision"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "manager.md").write_text(debate["judge_decision"], encoding="utf-8")
            research_parts.append(("Research Manager", debate["judge_decision"]))
        if research_parts:
            content = "\n\n".join(f"### {name}\n{text}" for name, text in research_parts)
            sections.append(f"## II. Research Team Decision\n\n{content}")

    # 3. Trading
    if final_state.get("trader_investment_plan"):
        trading_dir = save_path / "3_trading"
        trading_dir.mkdir(exist_ok=True)
        (trading_dir / "trader.md").write_text(final_state["trader_investment_plan"], encoding="utf-8")
        sections.append(f"## III. Trading Team Plan\n\n### Trader\n{final_state['trader_investment_plan']}")

    # 4. Risk Management
    if final_state.get("risk_debate_state"):
        risk_dir = save_path / "4_risk"
        risk = final_state["risk_debate_state"]
        risk_parts = []
        if risk.get("aggressive_history"):
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "aggressive.md").write_text(risk["aggressive_history"], encoding="utf-8")
            risk_parts.append(("Aggressive Analyst", risk["aggressive_history"]))
        if risk.get("conservative_history"):
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "conservative.md").write_text(risk["conservative_history"], encoding="utf-8")
            risk_parts.append(("Conservative Analyst", risk["conservative_history"]))
        if risk.get("neutral_history"):
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "neutral.md").write_text(risk["neutral_history"], encoding="utf-8")
            risk_parts.append(("Neutral Analyst", risk["neutral_history"]))
        if risk_parts:
            content = "\n\n".join(f"### {name}\n{text}" for name, text in risk_parts)
            sections.append(f"## IV. Risk Management Team Decision\n\n{content}")

        # 5. Portfolio Manager
        if risk.get("judge_decision"):
            portfolio_dir = save_path / "5_portfolio"
            portfolio_dir.mkdir(exist_ok=True)
            (portfolio_dir / "decision.md").write_text(risk["judge_decision"], encoding="utf-8")
            sections.append(f"## V. Portfolio Manager Decision\n\n### Portfolio Manager\n{risk['judge_decision']}")

    # Write consolidated report
    header = f"# Trading Analysis Report: {ticker}\n\nGenerated: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report_path = save_path / "complete_report.md"
    report_path.write_text(header + "\n\n".join(sections), encoding="utf-8")
    return report_path


def save_report_to_disk(final_state: dict[str, Any], ticker: str, save_path: Path) -> Path:
    """Save a complete analysis report to disk with organized subfolders."""
    return write_report_tree(final_state, ticker, save_path)


def generate_pdf_from_markdown(
    md_path: Path,
    ticker: str,
    output_path: Path,
    *,
    validation_result: ValidationResult | None = None,
    dashboard_model: DashboardModel | None = None,
) -> Path:
    """Generate a PDF report from an existing markdown report."""
    MarkdownPDFGenerator = _load_markdown_pdf_generator()

    content = md_path.read_text(encoding="utf-8")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generator = MarkdownPDFGenerator(
        ticker=ticker,
        date_str=dt.datetime.now().strftime("%B %d, %Y"),
        status_label=(
            validation_result.status_label
            if validation_result is not None
            else "RESEARCH_OUTPUT"
        ),
    )
    generator.add_highlights_page(
        content,
        dashboard_metrics=dashboard_model.pdf_metrics() if dashboard_model is not None else None,
    )
    generator.add_markdown_content(content)
    generator.save(str(output_path))
    return output_path


def write_validation_report(save_path: Path, validation_result: ValidationResult) -> None:
    report_path = save_path / "validation_report.json"
    report_path.write_text(
        json.dumps(validation_result.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )


def write_dashboard_report(save_path: Path, dashboard_model: DashboardModel) -> None:
    report_path = save_path / "dashboard.json"
    report_path.write_text(
        json.dumps(dashboard_model.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )


def _load_markdown_pdf_generator() -> type:
    try:
        from scripts.generate_full_report_pdf import MarkdownPDFGenerator

        return MarkdownPDFGenerator
    except ModuleNotFoundError:
        script_path = Path(__file__).resolve().parent.parent / "scripts" / "generate_full_report_pdf.py"
        if not script_path.exists():
            raise

        spec = importlib.util.spec_from_file_location(
            "tradingagents_generate_full_report_pdf",
            script_path,
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load PDF generator from {script_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.MarkdownPDFGenerator
