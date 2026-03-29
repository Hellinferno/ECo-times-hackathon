"""Runtime settings — merge DB SystemSetting rows over hard-coded defaults.

get_runtime_settings() returns a Dict[str, str] that callers read via the
three typed helpers:
  parse_int()    → int with fallback
  parse_float()  → float with fallback
  parse_bool()   → bool with fallback (accepts 1/true/yes/on and their negations)

DEFAULT_SYSTEM_SETTINGS provides sensible production defaults for all known
keys so the app works out-of-the-box without any DB rows.
"""
from typing import Any, Dict
from sqlalchemy.orm import Session

from models.db import SystemSetting


# ── Defaults ──────────────────────────────────────────────────────────────────

DEFAULT_SYSTEM_SETTINGS: Dict[str, str] = {
    "scan_interval_minutes": "15",
    "confidence_buy_threshold": "70.0",
    "confidence_watch_threshold": "50.0",
    "breakout_lookback_days": "30",
    "volume_spike_threshold": "2.0",
    "volume_avg_period": "20",
    "bulk_deal_lookback_days": "5",
    "backtest_lookback_years": "2",
    "backtest_outcome_days": "5",
    "default_alert_confidence_threshold": "65.0",
    "data_pipeline_mode": "legacy",
    "tinyfish_timeout_secs": "20",
    "tinyfish_max_concurrency": "20",
    "tinyfish_batch_size": "20",
    "tinyfish_fail_open": "true",
    "news_lookback_hours": "6",
    "social_lookback_hours": "6",
    "insider_lookback_days": "5",
    "macro_lookback_minutes": "60",
}


# ── Accessors ─────────────────────────────────────────────────────────────────


def get_runtime_settings(db: Session) -> Dict[str, str]:
    settings = db.query(SystemSetting).all()
    settings_map = {s.key: s.value for s in settings}
    merged = dict(DEFAULT_SYSTEM_SETTINGS)
    merged.update(settings_map)
    return merged


def parse_int(settings: Dict[str, Any], key: str, default: int) -> int:
    try:
        return int(settings.get(key, default))
    except (TypeError, ValueError):
        return default


def parse_float(settings: Dict[str, Any], key: str, default: float) -> float:
    try:
        return float(settings.get(key, default))
    except (TypeError, ValueError):
        return default


def parse_bool(settings: Dict[str, Any], key: str, default: bool) -> bool:
    value = str(settings.get(key, default)).strip().lower()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off"}:
        return False
    return default
