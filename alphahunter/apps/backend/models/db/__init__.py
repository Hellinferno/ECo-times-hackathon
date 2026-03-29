"""ORM model registry — imports and re-exports every SQLAlchemy model.

Groups:
  Base                  — Declarative base shared by all models
  Core intelligence     — Stock, ScanRun/Result, Decision, BulkDeal, signals, cache
  User-facing           — WatchlistItem, Alert, SystemSetting, AuditLog
  Platform              — Organization, PlatformUser, Company, Workspace and children, ValuationRun
"""
# ── Base ───────────────────────────────────────────────────────────────────────
from .base import Base

# ── Core intelligence models ───────────────────────────────────────────────────
from .stock import Stock
from .scan_run import ScanRun
from .scan_result import ScanResult
from .decision import Decision
from .bulk_deal import BulkDeal
from .external_signal_event import ExternalSignalEvent
from .web_fetch_run import WebFetchRun
from .shadow_signal_diff import ShadowSignalDiff

# ── User-facing models ─────────────────────────────────────────────────────────
from .watchlist_item import WatchlistItem
from .alert import Alert
from .system_setting import SystemSetting
from .audit_log import AuditLog

# ── Platform models (multi-tenant research workspace) ──────────────────────────
from .organization import Organization
from .platform_user import PlatformUser
from .company import Company
from .workspace import Workspace
from .workspace_document import WorkspaceDocument
from .workspace_agent_run import WorkspaceAgentRun
from .workspace_task import WorkspaceTask
from .workspace_output import WorkspaceOutput
from .valuation_run import ValuationRun

__all__ = [
    # Base
    "Base",
    # Core intelligence
    "Stock",
    "ScanRun",
    "ScanResult",
    "Decision",
    "BulkDeal",
    "ExternalSignalEvent",
    "WebFetchRun",
    "ShadowSignalDiff",
    # User-facing
    "WatchlistItem",
    "Alert",
    "SystemSetting",
    "AuditLog",
    # Platform
    "Organization",
    "PlatformUser",
    "Company",
    "Workspace",
    "WorkspaceDocument",
    "WorkspaceAgentRun",
    "WorkspaceTask",
    "WorkspaceOutput",
    "ValuationRun",
]
