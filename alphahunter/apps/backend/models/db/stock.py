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
