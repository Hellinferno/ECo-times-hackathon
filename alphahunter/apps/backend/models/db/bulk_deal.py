"""BulkDeal — institutional bulk/block deal record from NSE/BSE.

deal_type: BUY | SELL.
A unique constraint on (symbol, deal_date, client_name, deal_type) prevents
duplicate imports when the same day's data is fetched more than once.
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, BigInteger, DateTime, UniqueConstraint, Index
from .base import Base
import datetime

class BulkDeal(Base):
    __tablename__ = "bulk_deals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    deal_date = Column(Date, nullable=False)
    client_name = Column(String(200))
    deal_type = Column(String(10))
    quantity = Column(BigInteger)
    price = Column(Numeric(10, 2))
    exchange = Column(String(10), default='NSE')
    fetched_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('symbol', 'deal_date', 'client_name', 'deal_type', name='uq_bulk_deal'),
    )

Index('idx_bulk_deals_date', BulkDeal.deal_date.desc())
