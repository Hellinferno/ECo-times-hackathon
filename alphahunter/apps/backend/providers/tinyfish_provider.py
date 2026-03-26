from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any, Dict, List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from providers.web_intel_provider import (
    GoalSpec,
    NormalizedSignalEvent,
    SUPPORTED_EVENT_TYPES,
    WebIntelProvider,
)


class TinyFishProvider(WebIntelProvider):
    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        self.api_key = api_key or settings.MINO_API_KEY
        self.endpoint = endpoint or settings.TINYFISH_RUN_SSE_URL

    def run_goal_batch(
        self,
        goals: List[GoalSpec],
        timeout_secs: int = 20,
        max_concurrency: int = 20,
    ) -> List[NormalizedSignalEvent]:
        if not goals or not self.api_key:
            return []

        max_workers = max(1, min(max_concurrency, len(goals)))
        events: List[NormalizedSignalEvent] = []
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(self._run_single_goal, goal, timeout_secs) for goal in goals]
            for future in as_completed(futures):
                result = future.result()
                events.extend(result)

        return events

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
    def _run_single_goal(self, goal: GoalSpec, timeout_secs: int) -> List[NormalizedSignalEvent]:
        payload = {
            "url": goal.url,
            "goal": goal.goal,
            "metadata": goal.metadata or {},
        }
        if goal.symbol:
            payload["symbol"] = goal.symbol

        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            stream=True,
            timeout=timeout_secs,
        )
        response.raise_for_status()

        body = self._extract_terminal_payload(response)
        return self._normalize_payload(goal, body)

    def _extract_terminal_payload(self, response: requests.Response) -> Dict[str, Any]:
        last_json: Optional[Dict[str, Any]] = None
        for raw_line in response.iter_lines():
            if not raw_line:
                continue
            line = raw_line.decode("utf-8", errors="ignore").strip()
            if not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if data_str in {"[DONE]", "done", ""}:
                continue
            try:
                payload = json.loads(data_str)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                last_json = payload

        if last_json is not None:
            return last_json

        # Fallback for providers returning plain JSON instead of SSE.
        try:
            payload = response.json()
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    def _normalize_payload(self, goal: GoalSpec, payload: Dict[str, Any]) -> List[NormalizedSignalEvent]:
        source_type = goal.source_type if goal.source_type in SUPPORTED_EVENT_TYPES else "news_sentiment"
        source = "tinyfish"

        events_raw = self._extract_events(payload)
        normalized: List[NormalizedSignalEvent] = []
        for event in events_raw:
            symbol = str(event.get("symbol") or goal.symbol or "__GLOBAL__").upper()
            event_time = self._coerce_datetime(event.get("event_time") or event.get("timestamp")) or datetime.utcnow()
            strength = self._coerce_decimal(event.get("strength") or event.get("score"))
            sentiment = self._coerce_decimal(event.get("sentiment"))
            confidence = self._coerce_decimal(event.get("confidence"))
            dedupe_hash = self._build_hash(source_type, symbol, event_time, event)
            normalized.append(
                NormalizedSignalEvent(
                    symbol=symbol,
                    event_type=source_type,
                    event_time=event_time,
                    source=source,
                    payload_json=event,
                    strength=strength,
                    sentiment=sentiment,
                    confidence=confidence,
                    expires_at=event_time + timedelta(hours=24),
                    dedupe_hash=dedupe_hash,
                )
            )

        return normalized

    def _extract_events(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not payload:
            return []

        if isinstance(payload.get("events"), list):
            return [x for x in payload["events"] if isinstance(x, dict)]
        if isinstance(payload.get("data"), list):
            return [x for x in payload["data"] if isinstance(x, dict)]

        result = payload.get("result")
        if isinstance(result, list):
            return [x for x in result if isinstance(x, dict)]
        if isinstance(result, dict):
            if isinstance(result.get("events"), list):
                return [x for x in result["events"] if isinstance(x, dict)]
            return [result]

        if isinstance(result, str):
            try:
                decoded = json.loads(result)
                if isinstance(decoded, list):
                    return [x for x in decoded if isinstance(x, dict)]
                if isinstance(decoded, dict):
                    if isinstance(decoded.get("events"), list):
                        return [x for x in decoded["events"] if isinstance(x, dict)]
                    return [decoded]
            except json.JSONDecodeError:
                return []

        return []

    def _build_hash(self, event_type: str, symbol: str, event_time: datetime, event: Dict[str, Any]) -> str:
        payload_json = json.dumps(event, sort_keys=True, default=str)
        base = f"{event_type}|{symbol}|{event_time.isoformat()}|{payload_json}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    def _coerce_datetime(self, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            value = value.strip().replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(value)
                return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
            except ValueError:
                return None
        return None

    def _coerce_decimal(self, value: Any) -> Optional[Decimal]:
        if value is None or value == "":
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return None
