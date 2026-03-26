from sqlalchemy import Column, Integer, String, DateTime, Index, JSON
from .base import Base
import datetime

class MarketDataCache(Base):
    __tablename__ = "market_data_cache"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)
    data_type = Column(String(30), nullable=False)
    data_json = Column(JSON, nullable=False)
    fetched_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    source = Column(String(50), default='yfinance')

Index('idx_mdc_symbol_type', MarketDataCache.symbol, MarketDataCache.data_type)
