from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from api.router import api_router
from database import SessionLocal
from models.db import Stock
from agents import DataAgent

app = FastAPI(
    title="AlphaHunter AI",
    description="Autonomous Opportunity & Decision Engine",
    version="1.0.0"
)

scheduler = BackgroundScheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_allowed_origins,
    allow_origin_regex=settings.allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


def _prefetch_external_job():
    db = SessionLocal()
    try:
        symbols = [row[0] for row in db.query(Stock.symbol).filter(Stock.is_active == True).all()]
        if not symbols:
            return
        result = DataAgent(db).ensure_external_signals_prefetched(symbols=symbols, force=False)
        logger.info(f"Scheduled TinyFish prefetch result: {result}")
    except Exception as exc:
        logger.error(f"Scheduled TinyFish prefetch failed: {exc}")
    finally:
        db.close()


@app.on_event("startup")
def startup_event():
    if not scheduler.running:
        scheduler.add_job(_prefetch_external_job, "interval", minutes=5, id="tinyfish_prefetch", replace_existing=True)
        scheduler.start()


@app.on_event("shutdown")
def shutdown_event():
    if scheduler.running:
        scheduler.shutdown(wait=False)
