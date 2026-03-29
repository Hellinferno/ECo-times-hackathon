"""Platform services — domain logic layer above the ORM.

Exports:
  DeterministicValuationEngine / valuation_engine — DCF / Comps / LBO models
  MacroIntelligenceService / macro_service        — WorldMonitor macro context
  DocumentParser / document_parser                — PDF / DOCX / XLSX parsing
  ExcelWriter / excel_writer                      — Output spreadsheet generation
  WorldMonitorClient / world_monitor_client       — Raw HTTP client for WorldMonitor
"""
# ── Valuation ──────────────────────────────────────────────────────────────────
from .valuation_engine import DeterministicValuationEngine, ValuationContext, valuation_engine

# ── Macro intelligence ─────────────────────────────────────────────────────────
from .macro_service import MacroIntelligenceService, macro_service

# ── Document processing ────────────────────────────────────────────────────────
from .document_parser import DocumentParser, document_parser

# ── Report generation ──────────────────────────────────────────────────────────
from .excel_writer import ExcelWriter, excel_writer

# ── External data ──────────────────────────────────────────────────────────────
from .world_monitor_client import WorldMonitorClient, world_monitor_client

__all__ = [
    # Valuation
    "DeterministicValuationEngine",
    "ValuationContext",
    "valuation_engine",
    # Macro intelligence
    "MacroIntelligenceService",
    "macro_service",
    # Document processing
    "DocumentParser",
    "document_parser",
    # Report generation
    "ExcelWriter",
    "excel_writer",
    # External data
    "WorldMonitorClient",
    "world_monitor_client",
]
