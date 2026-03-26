from fastapi import APIRouter

from api.endpoints import health, scan, opportunities, history, stock, watchlist, alerts, settings

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(scan.router, prefix="/scan", tags=["scan"])
api_router.include_router(opportunities.router, prefix="/opportunities", tags=["opportunities"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(stock.router, prefix="/stock", tags=["stock"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
