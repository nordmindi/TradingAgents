"""Report validation helpers for publication gating."""

from .dashboard import DashboardModel, build_dashboard_model, validate_dashboard_consistency
from .instrument import InstrumentRecord, InstrumentResolution, resolve_instrument
from .market_data import MarketDataFreshness, check_market_data_freshness
from .report_validator import validate_final_state
from .models import ValidationIssue, ValidationResult
from .technical import (
    bearish_divergence,
    bollinger_squeeze_valid,
    bullish_divergence,
    detect_cross,
    macd_components_reconcile,
    validate_technical_claims,
)

__all__ = [
    "InstrumentRecord",
    "InstrumentResolution",
    "MarketDataFreshness",
    "DashboardModel",
    "ValidationIssue",
    "ValidationResult",
    "bearish_divergence",
    "bollinger_squeeze_valid",
    "build_dashboard_model",
    "bullish_divergence",
    "check_market_data_freshness",
    "detect_cross",
    "macd_components_reconcile",
    "resolve_instrument",
    "validate_technical_claims",
    "validate_dashboard_consistency",
    "validate_final_state",
]
