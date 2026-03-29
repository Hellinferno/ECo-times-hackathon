"""NSEProvider — direct NSE bulk/block deal fetcher using NseIndiaApi.

Primary path uses BennyThadikaran/NseIndiaApi (pip install nse[server]) which
handles NSE session management, cookie warm-up, and HTTP/2 automatically.

Falls back to a raw requests.Session approach if the library is unavailable so
the pipeline keeps working without it.

Usage:
    provider = NSEProvider()
    events = provider.fetch_bulk_deals(symbols=["INFY", "TCS"])

Rate limit: NSE enforces ~3 req/s; the NseIndiaApi library adds polite delays.
"""
from __future__ import annotations

import hashlib
import tempfile
import time
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from loguru import logger

from .web_intel_provider import NormalizedSignalEvent

# ── Optional NseIndiaApi library ──────────────────────────────────────────────
try:
    from nse import NSE as _NseLib  # pip install nse[server]
    _HAS_NSE_LIB = True
    logger.debug("NSEProvider: NseIndiaApi library available — using managed session.")
except ImportError:
    _HAS_NSE_LIB = False
    logger.debug("NSEProvider: NseIndiaApi not installed — falling back to raw requests.")

# ── Fallback raw-requests constants ───────────────────────────────────────────
_NSE_BASE = "https://www.nseindia.com"
_NSE_BULK_DEALS_URL = f"{_NSE_BASE}/api/corporates-bulk-deals"
_NSE_BLOCK_DEALS_URL = f"{_NSE_BASE}/api/corporates-block-deals"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": f"{_NSE_BASE}/",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

_NSE_DOWNLOAD_DIR = Path(tempfile.gettempdir()) / "nse_data"


class NSEProvider:
    """
    Fetches bulk and block deal data directly from NSE.

    Uses the NseIndiaApi library when available (handles session/cookies
    automatically). Falls back to a raw requests.Session otherwise.
    """

    def __init__(self, timeout_secs: int = 15):
        self.timeout = timeout_secs
        # Fallback session state (used only when NseIndiaApi is absent)
        self._session: Optional[requests.Session] = None
        self._session_warmed_up = False

    # ── Public interface ──────────────────────────────────────────────────────

    def fetch_bulk_deals(
        self,
        symbols: Optional[List[str]] = None,
        lookback_days: int = 5,
    ) -> List[NormalizedSignalEvent]:
        """
        Fetch recent bulk + block deals from NSE as NormalizedSignalEvent objects.

        Args:
            symbols: If provided, filter to these symbols only (None = all).
            lookback_days: Discard deals older than this many calendar days.
        """
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)
        symbol_set = {s.upper() for s in symbols} if symbols else None

        if _HAS_NSE_LIB:
            bulk_rows, block_rows = self._fetch_via_lib()
        else:
            bulk_rows = self._fetch_raw(_NSE_BULK_DEALS_URL)
            block_rows = self._fetch_raw(_NSE_BLOCK_DEALS_URL)

        events: List[NormalizedSignalEvent] = []
        for row in bulk_rows:
            event = self._parse_deal_row(row, "bulk", cutoff, symbol_set)
            if event:
                events.append(event)
        for row in block_rows:
            event = self._parse_deal_row(row, "block", cutoff, symbol_set)
            if event:
                events.append(event)

        logger.info(f"NSEProvider: fetched {len(events)} bulk/block deal events.")
        return events

    # ── NseIndiaApi path ──────────────────────────────────────────────────────

    def _fetch_via_lib(self) -> Tuple[List[Dict], List[Dict]]:
        """Use NseIndiaApi to fetch bulk and block deals with managed session."""
        _NSE_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        nse = _NseLib(download_folder=_NSE_DOWNLOAD_DIR)
        try:
            bulk = nse.bulkDeals() or []
            block = nse.blockDeals() or []
            return bulk, block
        except Exception as exc:
            logger.warning(f"NSEProvider (NseIndiaApi): fetch failed — {exc}")
            return [], []
        finally:
            try:
                nse.exit()
            except Exception:
                pass

    # ── Raw-requests fallback path ────────────────────────────────────────────

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update(_HEADERS)
        return self._session

    def _warm_up_session(self) -> None:
        if self._session_warmed_up:
            return
        session = self._get_session()
        try:
            session.get(_NSE_BASE, timeout=self.timeout).raise_for_status()
            time.sleep(0.5)
            self._session_warmed_up = True
        except Exception as exc:
            logger.warning(f"NSEProvider: session warm-up failed — {exc}")

    def _fetch_raw(self, url: str) -> List[Dict[str, Any]]:
        """Fetch a single NSE endpoint via raw requests. Returns [] on error."""
        self._warm_up_session()
        session = self._get_session()
        try:
            resp = session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                return data.get("data", [])
            if isinstance(data, list):
                return data
            return []
        except Exception as exc:
            logger.warning(f"NSEProvider: raw fetch failed ({url}) — {exc}")
            self._session = None
            self._session_warmed_up = False
            return []

    # ── Shared parsing ────────────────────────────────────────────────────────

    def _parse_deal_row(
        self,
        row: Dict[str, Any],
        deal_category: str,
        cutoff: datetime,
        symbol_set: Optional[set],
    ) -> Optional[NormalizedSignalEvent]:
        """Parse one NSE deal row into a NormalizedSignalEvent (BUY side only)."""
        try:
            symbol = (
                row.get("symbol") or row.get("Symbol") or row.get("scrip_name") or ""
            ).upper().strip()
            if not symbol:
                return None
            if symbol_set and symbol not in symbol_set:
                return None

            date_str = row.get("date") or row.get("Date") or row.get("trade_date") or ""
            event_time = self._parse_nse_date(date_str)
            if not event_time or event_time < cutoff:
                return None

            client = (
                row.get("clientName") or row.get("client_name") or
                row.get("Client") or row.get("buyerName") or "Unknown"
            ).strip()

            deal_type_raw = (
                row.get("buyOrSell") or row.get("buysell") or
                row.get("buy_sell") or row.get("type") or "BUY"
            ).strip().upper()

            if deal_type_raw not in {"BUY", "B"}:
                return None  # only ingest buy-side signals

            qty = int(float(row.get("quantity") or row.get("Quantity") or row.get("qty") or 0))
            price = float(row.get("price") or row.get("Price") or row.get("trade_price") or 0.0)

            strength = min(Decimal(str(min(qty / 500_000, 1.0))), Decimal("1.0"))
            dedupe_hash = hashlib.sha256(
                f"{symbol}|{event_time.date()}|{client}|{qty}|{price}".encode()
            ).hexdigest()[:32]

            return NormalizedSignalEvent(
                symbol=symbol,
                event_type="bulk_deal",
                event_time=event_time,
                source=f"nse_{deal_category}_deal",
                payload_json={
                    "deal_type": "BUY",
                    "client_name": client,
                    "quantity": qty,
                    "price": price,
                    "category": deal_category,
                    "source": "nse_direct",
                },
                strength=strength,
                expires_at=event_time + timedelta(days=7),
                dedupe_hash=dedupe_hash,
            )
        except Exception as exc:
            logger.debug(f"NSEProvider: failed to parse row {row}: {exc}")
            return None

    @staticmethod
    def _parse_nse_date(date_str: str) -> Optional[datetime]:
        """Parse NSE date strings — handles DD-Mon-YYYY, YYYY-MM-DD, DD/MM/YYYY."""
        if not date_str:
            return None
        for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        return None
