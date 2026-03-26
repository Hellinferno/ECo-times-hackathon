from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

import yfinance as yf
from loguru import logger
from sqlalchemy import desc
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

from models.db.bulk_deal import BulkDeal
from models.db.external_signal_event import ExternalSignalEvent
from services.web_intel_service import WebIntelService
from utils.runtime_settings import get_runtime_settings, parse_int


class DataAgent:
    def __init__(self, db: Session):
        self.db = db

    def get_pipeline_mode(self) -> str:
        settings = get_runtime_settings(self.db)
        mode = str(settings.get("data_pipeline_mode", "legacy")).strip().lower()
        if mode not in {"legacy", "shadow", "active"}:
            return "legacy"
        return mode

    def ensure_external_signals_prefetched(self, symbols: List[str], force: bool = False) -> Dict[str, Any]:
        service = WebIntelService(self.db)
        try:
            return service.prefetch(symbols=symbols, force=force) if force else service.prefetch_if_stale(symbols=symbols)
        except Exception as exc:
            logger.warning(f"External prefetch failed, continuing in fail-open mode: {exc}")
            return {"failed": True, "fail_open": True, "error": str(exc)}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_market_data(self, symbol: str, lookback_days: int = 60, lookback_years: int = 2):
        """
        Fetches normalized OHLCV data using yfinance.
        Note: Indian stocks on Yahoo Finance need the .NS extension.
        """
        yf_symbol = f"{symbol}.NS"
        try:
            ticker = yf.Ticker(yf_symbol)
            short_term_data = ticker.history(period=f"{lookback_days}d")

            if short_term_data.empty:
                return None

            current_price = float(short_term_data["Close"].iloc[-1])
            volume_today = int(short_term_data["Volume"].iloc[-1])

            ohlcv_short = []
            for date, row in short_term_data.iterrows():
                ohlcv_short.append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": int(row["Volume"]),
                    }
                )

            return {
                "symbol": symbol,
                "current_price": current_price,
                "volume_today": volume_today,
                "ohlcv_short": ohlcv_short,
            }
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_historical_data_for_backtest(self, symbol: str, lookback_years: int = 2):
        """Fetch historical data for backtesting."""
        yf_symbol = f"{symbol}.NS"
        try:
            ticker = yf.Ticker(yf_symbol)
            hist_data = ticker.history(period=f"{lookback_years}y")
            if hist_data.empty:
                return []

            ohlcv = []
            for date, row in hist_data.iterrows():
                ohlcv.append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": int(row["Volume"]),
                    }
                )
            return ohlcv
        except Exception as e:
            logger.error(f"Error fetching backtest history for {symbol}: {str(e)}")
            return []

    def get_bulk_deals(self, symbol: str, as_of: Optional[datetime.datetime] = None, prefer_live: bool = True):
        """
        Fetch bulk deals using normalized external events first (if requested),
        then fallback to local seeded table.
        """
        settings = get_runtime_settings(self.db)
        lookback_days = parse_int(settings, "bulk_deal_lookback_days", 5)
        as_of = as_of or datetime.datetime.utcnow()
        cutoff_dt = as_of - datetime.timedelta(days=lookback_days)

        live_deals: List[Dict[str, Any]] = []
        if prefer_live:
            try:
                external_rows = (
                    self.db.query(ExternalSignalEvent)
                    .filter(
                        ExternalSignalEvent.symbol == symbol.upper(),
                        ExternalSignalEvent.event_type == "bulk_deal",
                        ExternalSignalEvent.event_time >= cutoff_dt,
                        ExternalSignalEvent.expires_at >= datetime.datetime.utcnow(),
                    )
                    .order_by(desc(ExternalSignalEvent.event_time))
                    .all()
                )
                for row in external_rows:
                    payload = row.payload_json or {}
                    deal_type = str(payload.get("deal_type") or payload.get("type") or "").upper() or "BUY"
                    live_deals.append(
                        {
                            "date": row.event_time.strftime("%Y-%m-%d"),
                            "client_name": payload.get("client_name")
                            or payload.get("client")
                            or payload.get("buyer")
                            or "Unknown",
                            "deal_type": deal_type,
                            "quantity": int(payload.get("quantity") or payload.get("qty") or 0),
                            "price": float(payload.get("price") or 0.0),
                            "source": row.source,
                        }
                    )
                if live_deals:
                    return live_deals
            except Exception as exc:
                logger.warning(f"Live bulk deal lookup unavailable; using local fallback for {symbol}: {exc}")

        cutoff_date = (as_of.date() - datetime.timedelta(days=max(lookback_days, 60)))
        deals = (
            self.db.query(BulkDeal)
            .filter(BulkDeal.symbol == symbol.upper(), BulkDeal.deal_date >= cutoff_date)
            .order_by(desc(BulkDeal.deal_date))
            .all()
        )
        return [
            {
                "date": d.deal_date.strftime("%Y-%m-%d"),
                "client_name": d.client_name,
                "deal_type": d.deal_type,
                "quantity": d.quantity,
                "price": float(d.price) if d.price is not None else 0.0,
                "source": "local_db",
            }
            for d in deals
        ]

    def get_external_context(self, symbol: str, as_of: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """
        Aggregate external normalized events into signal-ready context.
        """
        settings = get_runtime_settings(self.db)
        as_of = as_of or datetime.datetime.utcnow()

        lookbacks = {
            "news_sentiment": datetime.timedelta(hours=parse_int(settings, "news_lookback_hours", 6)),
            "social_sentiment": datetime.timedelta(hours=parse_int(settings, "social_lookback_hours", 6)),
            "insider_filing": datetime.timedelta(days=parse_int(settings, "insider_lookback_days", 5)),
            "macro_indicator": datetime.timedelta(minutes=parse_int(settings, "macro_lookback_minutes", 60)),
        }

        type_rows: Dict[str, List[ExternalSignalEvent]] = {}
        for event_type, delta in lookbacks.items():
            try:
                rows = (
                    self.db.query(ExternalSignalEvent)
                    .filter(
                        ExternalSignalEvent.symbol == symbol.upper(),
                        ExternalSignalEvent.event_type == event_type,
                        ExternalSignalEvent.event_time >= (as_of - delta),
                        ExternalSignalEvent.expires_at >= datetime.datetime.utcnow(),
                    )
                    .order_by(desc(ExternalSignalEvent.event_time))
                    .all()
                )
            except Exception as exc:
                logger.warning(f"External context query failed for {symbol}/{event_type}: {exc}")
                rows = []
            type_rows[event_type] = rows

        summary = {
            "symbol": symbol.upper(),
            "news_sentiment": self._summarize_news(type_rows["news_sentiment"]),
            "social_sentiment": self._summarize_social(type_rows["social_sentiment"]),
            "insider_filing": self._summarize_insider(type_rows["insider_filing"]),
            "macro_indicator": self._summarize_macro(type_rows["macro_indicator"]),
            "source_health": self._source_health(type_rows),
        }
        return summary

    def get_external_health_snapshot(self) -> Dict[str, Any]:
        service = WebIntelService(self.db)
        try:
            return service.get_health_snapshot()
        except Exception as exc:
            logger.warning(f"External health snapshot unavailable: {exc}")
            return {
                "provider": "disabled",
                "last_prefetch_at": None,
                "last_prefetch_status": "missing",
                "source_status": {},
                "source_freshness_minutes": {},
            }

    def _summarize_news(self, rows: List[ExternalSignalEvent]) -> Dict[str, Any]:
        if not rows:
            return {
                "available": False,
                "article_count": 0,
                "weighted_sentiment": None,
                "avg_confidence": None,
            }

        weighted_num = 0.0
        weighted_den = 0.0
        confidences: List[float] = []
        for row in rows:
            sentiment = float(row.sentiment) if row.sentiment is not None else 0.0
            confidence = float(row.confidence) if row.confidence is not None else 0.5
            weighted_num += sentiment * confidence
            weighted_den += confidence
            confidences.append(confidence)

        weighted_sentiment = (weighted_num / weighted_den) if weighted_den > 0 else 0.0
        return {
            "available": True,
            "article_count": len(rows),
            "weighted_sentiment": round(weighted_sentiment, 4),
            "avg_confidence": round(sum(confidences) / len(confidences), 4),
            "latest_at": rows[0].event_time.isoformat(),
        }

    def _summarize_social(self, rows: List[ExternalSignalEvent]) -> Dict[str, Any]:
        if not rows:
            return {
                "available": False,
                "sample_count": 0,
                "mention_zscore": None,
                "positive_ratio": None,
                "weighted_sentiment": None,
            }

        zscores: List[float] = []
        positive_ratios: List[float] = []
        sentiments: List[float] = []
        for row in rows:
            payload = row.payload_json or {}
            if payload.get("mention_zscore") is not None:
                zscores.append(float(payload.get("mention_zscore")))
            elif row.strength is not None:
                zscores.append(float(row.strength))

            if payload.get("positive_ratio") is not None:
                positive_ratios.append(float(payload.get("positive_ratio")))
            elif row.sentiment is not None:
                positive_ratios.append(0.5 + (float(row.sentiment) / 2.0))

            if row.sentiment is not None:
                sentiments.append(float(row.sentiment))

        return {
            "available": True,
            "sample_count": len(rows),
            "mention_zscore": round(sum(zscores) / len(zscores), 4) if zscores else None,
            "positive_ratio": round(sum(positive_ratios) / len(positive_ratios), 4) if positive_ratios else None,
            "weighted_sentiment": round(sum(sentiments) / len(sentiments), 4) if sentiments else None,
            "latest_at": rows[0].event_time.isoformat(),
        }

    def _summarize_insider(self, rows: List[ExternalSignalEvent]) -> Dict[str, Any]:
        if not rows:
            return {
                "available": False,
                "filing_count": 0,
                "positive_filing_score": None,
            }

        scores: List[float] = []
        for row in rows:
            payload = row.payload_json or {}
            if payload.get("filing_score") is not None:
                scores.append(float(payload.get("filing_score")))
            elif row.strength is not None:
                scores.append(float(row.strength))

        best_score = max(scores) if scores else 0.0
        return {
            "available": True,
            "filing_count": len(rows),
            "positive_filing_score": round(best_score, 4),
            "latest_at": rows[0].event_time.isoformat(),
        }

    def _summarize_macro(self, rows: List[ExternalSignalEvent]) -> Dict[str, Any]:
        if not rows:
            return {
                "available": False,
                "sample_count": 0,
                "sector_macro_score": None,
                "freshness_minutes": None,
            }

        scores: List[float] = []
        for row in rows:
            payload = row.payload_json or {}
            if payload.get("score") is not None:
                scores.append(float(payload.get("score")))
            elif row.strength is not None:
                scores.append(float(row.strength))

        latest = rows[0].event_time
        freshness = (datetime.datetime.utcnow() - latest).total_seconds() / 60.0
        return {
            "available": True,
            "sample_count": len(rows),
            "sector_macro_score": round(sum(scores) / len(scores), 4) if scores else None,
            "freshness_minutes": round(freshness, 2),
            "latest_at": latest.isoformat(),
        }

    def _source_health(self, type_rows: Dict[str, List[ExternalSignalEvent]]) -> Dict[str, Any]:
        status: Dict[str, Any] = {}
        now = datetime.datetime.utcnow()
        for event_type, rows in type_rows.items():
            if not rows:
                status[event_type] = {"status": "missing", "count": 0, "freshness_minutes": None}
                continue
            latest = rows[0].event_time
            freshness = (now - latest).total_seconds() / 60.0
            state = "fresh" if freshness <= 60 else "stale"
            status[event_type] = {
                "status": state,
                "count": len(rows),
                "freshness_minutes": round(freshness, 2),
            }
        return status
