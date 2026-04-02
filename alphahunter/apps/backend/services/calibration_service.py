"""Decision calibration and drift monitoring helpers."""
from __future__ import annotations

import datetime as dt
import json
from typing import Any

from sqlalchemy.orm import Session

from models.db import Decision, SystemSetting


def _upsert_setting(db: Session, *, key: str, value: str, description: str) -> None:
    existing = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if existing:
        existing.value = value
        existing.description = description
        existing.updated_at = dt.datetime.utcnow()
        return
    db.add(SystemSetting(key=key, value=value, description=description))


def compute_decision_calibration_metrics(db: Session, *, lookback_days: int = 90) -> dict[str, Any]:
    cutoff = dt.datetime.utcnow() - dt.timedelta(days=lookback_days)
    recent = (
        db.query(Decision)
        .filter(Decision.decided_at >= cutoff)
        .order_by(Decision.decided_at.desc())
        .all()
    )
    measured = [decision for decision in recent if decision.outcome_measured]

    metrics: dict[str, Any] = {
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        "lookback_days": lookback_days,
        "sample_size": len(recent),
        "measured_sample_size": len(measured),
        "overall_hit_rate": 0.0,
        "avg_measured_return_pct": 0.0,
        "stop_loss_breach_rate": 0.0,
        "confidence_calibration_gap": 0.0,
        "buckets": [],
        "recommended_thresholds": {
            "buy": 70.0,
            "watch": 50.0,
        },
    }

    if not recent:
        return metrics

    wins = 0
    measured_returns = []
    stop_loss_breaches = 0
    weighted_gap = 0.0
    weighted_count = 0

    for bucket_min in range(0, 100, 10):
        bucket_max = bucket_min + 9.99 if bucket_min < 90 else 100.0
        bucket_items = [
            decision for decision in measured
            if bucket_min <= float(decision.confidence or 0) <= bucket_max
        ]
        if not bucket_items:
            continue

        bucket_wins = sum(1 for decision in bucket_items if (decision.outcome_result or "").upper() == "WIN")
        bucket_returns = [float(decision.outcome_return_pct) for decision in bucket_items if decision.outcome_return_pct is not None]
        bucket_avg_return = round(sum(bucket_returns) / len(bucket_returns), 3) if bucket_returns else 0.0
        bucket_win_rate = round(bucket_wins / len(bucket_items), 4)
        confidence_mid = ((bucket_min + bucket_max) / 2) / 100.0
        weighted_gap += abs(confidence_mid - bucket_win_rate) * len(bucket_items)
        weighted_count += len(bucket_items)

        metrics["buckets"].append(
            {
                "bucket_min": bucket_min,
                "bucket_max": bucket_max,
                "count": len(bucket_items),
                "win_rate": bucket_win_rate,
                "avg_return_pct": bucket_avg_return,
            }
        )

    for decision in measured:
        if (decision.outcome_result or "").upper() == "WIN":
            wins += 1
        if decision.outcome_return_pct is not None:
            measured_returns.append(float(decision.outcome_return_pct))
        if (
            decision.stop_loss is not None
            and decision.outcome_exit_price is not None
            and float(decision.outcome_exit_price) <= float(decision.stop_loss)
        ):
            stop_loss_breaches += 1

    metrics["overall_hit_rate"] = round(wins / len(measured), 4) if measured else 0.0
    metrics["avg_measured_return_pct"] = round(sum(measured_returns) / len(measured_returns), 3) if measured_returns else 0.0
    metrics["stop_loss_breach_rate"] = round(stop_loss_breaches / len(measured), 4) if measured else 0.0
    metrics["confidence_calibration_gap"] = round(weighted_gap / weighted_count, 4) if weighted_count else 0.0

    buy_candidates = [
        bucket["bucket_min"]
        for bucket in metrics["buckets"]
        if bucket["count"] >= 3 and bucket["win_rate"] >= 0.55 and bucket["avg_return_pct"] > 0
    ]
    watch_candidates = [
        bucket["bucket_min"]
        for bucket in metrics["buckets"]
        if bucket["count"] >= 3 and bucket["win_rate"] >= 0.5
    ]
    if buy_candidates:
        metrics["recommended_thresholds"]["buy"] = float(max(buy_candidates))
    if watch_candidates:
        metrics["recommended_thresholds"]["watch"] = float(max(watch_candidates))

    return metrics


def persist_decision_calibration_snapshot(db: Session, *, lookback_days: int = 90) -> dict[str, Any]:
    metrics = compute_decision_calibration_metrics(db, lookback_days=lookback_days)
    _upsert_setting(
        db,
        key="decision_calibration_metrics_json",
        value=json.dumps(metrics, separators=(",", ":")),
        description="Latest decision calibration metrics snapshot",
    )
    _upsert_setting(
        db,
        key="decision_calibration_last_computed_at",
        value=metrics["generated_at"],
        description="UTC timestamp of the latest calibration snapshot",
    )
    _upsert_setting(
        db,
        key="recommended_confidence_buy_threshold",
        value=str(metrics["recommended_thresholds"]["buy"]),
        description="Recommended BUY threshold from recent measured outcomes",
    )
    _upsert_setting(
        db,
        key="recommended_confidence_watch_threshold",
        value=str(metrics["recommended_thresholds"]["watch"]),
        description="Recommended WATCH threshold from recent measured outcomes",
    )
    db.commit()
    return metrics
