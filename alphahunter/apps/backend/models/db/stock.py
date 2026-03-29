"""Stock — NSE/BSE equity universe entry.

is_active = True means the stock is included in scheduled scans.
market_cap_cr stores market capitalisation in Indian crores.
nse_code / bse_code / isin provide exchange-specific identifiers for
data-feed lookups (yfinance uses symbol + ".NS" suffix).
"""
from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, func
from .base import Base
import datetime

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    sector = Column(String(100), index=True)
    market_cap_cr = Column(Numeric(15, 2))
    is_active = Column(Boolean, nullable=False, default=True)
    nse_code = Column(String(20))
    bse_code = Column(String(20))
    isin = Column(String(12))
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
