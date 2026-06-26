from __future__ import annotations

import os
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

from tradingagents.service.runner import (
    ReportRequest,
    ReportResult,
    run_report_job,
    validate_report_request,
)


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class CreateReportRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=32)
    analysis_date: str | None = None
    selected_analysts: list[str] = Field(
        default_factory=lambda: ["market", "social", "news", "fundamentals"]
    )
    llm_provider: str | None = None
    deep_think_llm: str | None = None
    quick_think_llm: str | None = None
    backend_url: str | None = None
    output_language: str | None = None
    max_debate_rounds: int | None = Field(default=None, ge=1)
    max_risk_discuss_rounds: int | None = Field(default=None, ge=1)
    checkpoint_enabled: bool | None = None
    user_id: str | None = Field(default=None, max_length=128)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("selected_analysts")
    @classmethod
    def normalize_analysts(cls, value: list[str]) -> list[str]:
        return [item.strip().lower() for item in value]


class CreateReportResponse(BaseModel):
    job_id: str
    status: JobStatus
    status_url: str
    pdf_url: str


class ReportJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    ticker: str
    analysis_date: str
    decision: Any | None = None
    error: str | None = None
    markdown_path: str | None = None
    pdf_path: str | None = None
    pdf_url: str | None = None


class JobRecord:
    def __init__(self, job_id: str, request: ReportRequest) -> None:
        self.job_id = job_id
        self.request = request
        self.status = JobStatus.queued
        self.result: ReportResult | None = None
        self.error: str | None = None
        self.future: Future[ReportResult] | None = None


app = FastAPI(
    title="TradingAgents Service API",
    version="0.1.0",
    description="Run TradingAgents analysis jobs and download generated PDF reports.",
)

executor = ThreadPoolExecutor(max_workers=int(os.getenv("TRADINGAGENTS_SERVICE_WORKERS", "1")))
jobs: dict[str, JobRecord] = {}


def require_service_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("TRADINGAGENTS_SERVICE_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid service API key",
        )


def _execute_job(record: JobRecord) -> ReportResult:
    record.status = JobStatus.running
    try:
        record.result = run_report_job(record.request, job_id=record.job_id)
        record.status = JobStatus.completed
        return record.result
    except Exception as exc:
        record.error = str(exc)
        record.status = JobStatus.failed
        raise


def _get_job(job_id: str) -> JobRecord:
    record = jobs.get(job_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    return record


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/v1/reports",
    response_model=CreateReportResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_service_key)],
)
def create_report(payload: CreateReportRequest) -> CreateReportResponse:
    analysis_date = payload.analysis_date or datetime.now().strftime("%Y-%m-%d")
    job_id = uuid4().hex
    request = ReportRequest(
        ticker=payload.ticker,
        analysis_date=analysis_date,
        selected_analysts=tuple(payload.selected_analysts),
        llm_provider=payload.llm_provider,
        deep_think_llm=payload.deep_think_llm,
        quick_think_llm=payload.quick_think_llm,
        backend_url=payload.backend_url,
        output_language=payload.output_language,
        max_debate_rounds=payload.max_debate_rounds,
        max_risk_discuss_rounds=payload.max_risk_discuss_rounds,
        checkpoint_enabled=payload.checkpoint_enabled,
        user_id=payload.user_id,
    )
    try:
        validate_report_request(request)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    record = JobRecord(job_id, request)
    jobs[job_id] = record
    record.future = executor.submit(_execute_job, record)

    return CreateReportResponse(
        job_id=job_id,
        status=record.status,
        status_url=f"/v1/reports/{job_id}",
        pdf_url=f"/v1/reports/{job_id}/pdf",
    )


@app.get(
    "/v1/reports/{job_id}",
    response_model=ReportJobResponse,
    dependencies=[Depends(require_service_key)],
)
def get_report(job_id: str) -> ReportJobResponse:
    record = _get_job(job_id)
    result = record.result
    return ReportJobResponse(
        job_id=record.job_id,
        status=record.status,
        ticker=record.request.ticker,
        analysis_date=record.request.analysis_date,
        decision=result.decision if result else None,
        error=record.error,
        markdown_path=str(result.markdown_path) if result else None,
        pdf_path=str(result.pdf_path) if result else None,
        pdf_url=f"/v1/reports/{job_id}/pdf" if result else None,
    )


@app.get("/v1/reports/{job_id}/pdf", dependencies=[Depends(require_service_key)])
def download_report_pdf(job_id: str) -> FileResponse:
    record = _get_job(job_id)
    if record.status != JobStatus.completed or record.result is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"job is {record.status}",
        )

    pdf_path = Path(record.result.pdf_path)
    if not pdf_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="pdf not found",
        )

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name,
    )
