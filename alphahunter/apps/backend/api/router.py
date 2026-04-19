"""Central API router — mounts all endpoint sub-routers onto api_router.

Core intelligence: /health /scan /opportunities /history /stock /watchlist /alerts /settings
Platform layer:    /auth /companies /workspaces /valuations /outputs /macro
"""
from fastapi import APIRouter

from api.endpoints import (
    alerts,
    feedback,
    health,
    history,
    opportunities,
    platform as unified_platform,
    scan,
    settings,
    stock,
    watchlist,
)

api_router = APIRouter()

# ── Core intelligence endpoints ────────────────────────────────────────────────
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(scan.router, prefix="/scan", tags=["scan"])
api_router.include_router(opportunities.router, prefix="/opportunities", tags=["opportunities"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(stock.router, prefix="/stock", tags=["stock"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(feedback.router)

# ── Platform (auth / companies / workspaces / valuations / macro) ──────────────
api_router.include_router(unified_platform.auth_router)
api_router.include_router(unified_platform.companies_router)
api_router.include_router(unified_platform.workspaces_router)
api_router.include_router(unified_platform.valuations_router)
api_router.include_router(unified_platform.outputs_router)
api_router.include_router(unified_platform.macro_router)
