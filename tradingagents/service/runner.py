from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.reporting import generate_pdf_from_markdown

logger = logging.getLogger(__name__)

VALID_ANALYSTS = {"market", "social", "news", "fundamentals"}


@dataclass(frozen=True)
class ReportRequest:
    ticker: str
    analysis_date: str
    selected_analysts: tuple[str, ...] = ("market", "social", "news", "fundamentals")
    llm_provider: str | None = None
    deep_think_llm: str | None = None
    quick_think_llm: str | None = None
    backend_url: str | None = None
    output_language: str | None = None
    max_debate_rounds: int | None = None
    max_risk_discuss_rounds: int | None = None
    checkpoint_enabled: bool | None = None
    user_id: str | None = None


@dataclass(frozen=True)
class ReportResult:
    job_id: str
    ticker: str
    analysis_date: str
    decision: Any
    report_dir: Path
    markdown_path: Path
    pdf_path: Path


def validate_report_request(request: ReportRequest) -> None:
    if not request.ticker.strip():
        raise ValueError("ticker is required")

    try:
        analysis_date = datetime.strptime(request.analysis_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("analysis_date must use YYYY-MM-DD format") from exc

    if analysis_date > datetime.now().date():
        raise ValueError("analysis_date cannot be in the future")

    if not request.selected_analysts:
        raise ValueError("at least one analyst is required")

    invalid = set(request.selected_analysts) - VALID_ANALYSTS
    if invalid:
        raise ValueError(f"unknown analysts: {', '.join(sorted(invalid))}")

    if request.max_debate_rounds is not None and request.max_debate_rounds < 1:
        raise ValueError("max_debate_rounds must be at least 1")

    if request.max_risk_discuss_rounds is not None and request.max_risk_discuss_rounds < 1:
        raise ValueError("max_risk_discuss_rounds must be at least 1")


def build_config(request: ReportRequest, job_id: str) -> dict[str, Any]:
    config = DEFAULT_CONFIG.copy()

    report_root = Path(os.getenv("TRADINGAGENTS_SERVICE_REPORTS_DIR", "reports/api")).resolve()
    cache_root = Path(os.getenv("TRADINGAGENTS_SERVICE_CACHE_DIR", ".tradingagents_service/cache")).resolve()
    memory_root = Path(os.getenv("TRADINGAGENTS_SERVICE_MEMORY_DIR", ".tradingagents_service/memory")).resolve()

    config["results_dir"] = str(report_root / "_logs" / job_id)
    config["data_cache_dir"] = str(cache_root)
    config["memory_log_path"] = str(memory_root / "trading_memory.md")

    overrides = {
        "llm_provider": request.llm_provider,
        "deep_think_llm": request.deep_think_llm,
        "quick_think_llm": request.quick_think_llm,
        "backend_url": request.backend_url,
        "output_language": request.output_language,
        "max_debate_rounds": request.max_debate_rounds,
        "max_risk_discuss_rounds": request.max_risk_discuss_rounds,
        "checkpoint_enabled": request.checkpoint_enabled,
    }
    for key, value in overrides.items():
        if value is not None:
            config[key] = value

    logger.debug(
        f"Config built | Job: {job_id} | "
        f"LLM: {config.get('llm_provider')} | "
        f"Deep Think: {config.get('deep_think_llm')} | "
        f"Quick Think: {config.get('quick_think_llm')}"
    )

    return config


def run_report_job(request: ReportRequest, job_id: str | None = None) -> ReportResult:
    """Run TradingAgents and produce markdown plus PDF artifacts."""
    load_dotenv()
    load_dotenv(".env.enterprise", override=False)
    validate_report_request(request)

    job_id = job_id or uuid4().hex
    ticker = request.ticker.strip().upper()
    
    logger.info(f"Building config | Job: {job_id} | Ticker: {ticker}")
    config = build_config(request, job_id)

    logger.info(f"Initializing TradingAgentsGraph | Job: {job_id} | Analysts: {request.selected_analysts}")
    graph = TradingAgentsGraph(
        selected_analysts=list(request.selected_analysts),
        debug=False,
        config=config,
    )
    
    logger.info(f"Starting propagation | Job: {job_id} | Ticker: {ticker} | Date: {request.analysis_date}")
    try:
        final_state, decision = graph.propagate(ticker, request.analysis_date)
        logger.info(f"Propagation completed | Job: {job_id} | Decision: {decision}")
    except Exception as exc:
        logger.error(f"Propagation failed | Job: {job_id} | Error: {str(exc)}", exc_info=True)
        raise

    report_root = Path(os.getenv("TRADINGAGENTS_SERVICE_REPORTS_DIR", "reports/api")).resolve()
    report_dir = report_root / job_id
    
    logger.info(f"Saving report to disk | Job: {job_id} | Directory: {report_dir}")
    markdown_path = graph.save_reports(final_state, ticker, report_dir)
    logger.info(f"Markdown report saved | Job: {job_id} | Path: {markdown_path}")
    
    logger.info(f"Generating PDF | Job: {job_id} | Ticker: {ticker}")
    pdf_path = generate_pdf_from_markdown(
        markdown_path,
        ticker,
        report_dir / f"TradingAgents_Report_{ticker}_{job_id}.pdf",
    )
    logger.info(f"PDF generated | Job: {job_id} | Path: {pdf_path}")

    return ReportResult(
        job_id=job_id,
        ticker=ticker,
        analysis_date=request.analysis_date,
        decision=decision,
        report_dir=report_dir,
        markdown_path=markdown_path,
        pdf_path=pdf_path,
    )

