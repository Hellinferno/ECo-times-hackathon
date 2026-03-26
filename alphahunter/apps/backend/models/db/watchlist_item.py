from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint, Index
from .base import Base
import datetime

class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, default='default', index=True)
    symbol = Column(String(20), nullable=False)
    added_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    notes = Column(Text)

    __table_args__ = (
        UniqueConstraint('user_id', 'symbol', name='uq_watchlist_item'),
    )
