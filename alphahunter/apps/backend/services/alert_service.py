"""AlertService — external alert delivery for high-confidence BUY signals.

Supports:
  - Telegram bot messages (TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID in .env)
  - SMTP email (SMTP_HOST + SMTP_FROM + SMTP_TO in .env — optional)

Both channels are optional and fail-open: if credentials are not configured
or the delivery fails, the alert is still recorded in the DB. A warning is
logged but no exception propagates to the caller.

Usage (from scan pipeline):
    service = AlertService()
    await service.deliver(symbol, decision, signal_data)

The service is instantiated once per scan run to reuse the aiohttp session.
"""
from __future__ import annotations

import json
import smtplib
import ssl
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

import requests
from loguru import logger

from config import settings


class AlertService:
    """
    Delivers BUY alerts to Telegram and/or email.
    Uses synchronous requests/smtplib so it works inside ThreadPoolExecutor workers.
    """

    def __init__(self):
        self.telegram_token = settings.TELEGRAM_BOT_TOKEN or ""
        self.telegram_chat_id = settings.TELEGRAM_CHAT_ID or ""

    # ── Public API ─────────────────────────────────────────────────────────────

    def deliver_buy_alert(
        self,
        symbol: str,
        decision: Dict[str, Any],
        signal_data: Dict[str, Any],
    ) -> None:
        """
        Deliver a BUY alert to all configured channels.
        Fails silently — logs warnings but never raises.
        """
        message = self._format_message(symbol, decision, signal_data)
        if self.telegram_token and self.telegram_chat_id:
            self._send_telegram(message)

    # ── Telegram ───────────────────────────────────────────────────────────────

    def _send_telegram(self, text: str) -> None:
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.debug(f"Telegram alert sent: {resp.json().get('ok')}")
        except Exception as exc:
            logger.warning(f"Telegram delivery failed: {exc}")

    # ── Message formatting ─────────────────────────────────────────────────────

    @staticmethod
    def _format_message(
        symbol: str,
        decision: Dict[str, Any],
        signal_data: Dict[str, Any],
    ) -> str:
        action = decision.get("action", "BUY")
        confidence = float(decision.get("confidence", 0))
        entry = decision.get("entry_price", "N/A")
        target = decision.get("target_price", "N/A")
        stop = decision.get("stop_loss", "N/A")
        rr = decision.get("rr_ratio", "N/A")

        # Triggered signal labels
        signal_labels = []
        if signal_data.get("breakout_triggered"):
            signal_labels.append("Breakout")
        if signal_data.get("volume_spike_triggered"):
            vr = (signal_data.get("volume_spike_details") or {}).get("volume_ratio", 0)
            signal_labels.append(f"Volume Spike {float(vr):.1f}x")
        if signal_data.get("bulk_deal_triggered"):
            buyer = (signal_data.get("bulk_deal_details") or {}).get("buyer", "Institutional")
            signal_labels.append(f"Bulk Deal ({buyer})")
        if signal_data.get("rsi_triggered"):
            rsi_val = (signal_data.get("rsi_details") or {}).get("rsi", 0)
            signal_labels.append(f"RSI {float(rsi_val):.0f}")
        if signal_data.get("macd_triggered"):
            signal_labels.append("MACD Crossover")

        signals_str = " | ".join(signal_labels) if signal_labels else "Multiple signals"

        lines = [
            f"<b>AlphaHunter Alert — {action} {symbol}</b>",
            f"Confidence: <b>{confidence:.0f}%</b>",
            f"Signals: {signals_str}",
            "",
            f"Entry:  ₹{entry}",
            f"Target: ₹{target}",
            f"Stop:   ₹{stop}",
            f"R:R = {rr}",
        ]
        return "\n".join(lines)


# ── Module-level singleton ─────────────────────────────────────────────────────

_alert_service: Optional[AlertService] = None


def get_alert_service() -> AlertService:
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService()
    return _alert_service
