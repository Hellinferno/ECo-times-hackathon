"""Company — registry of listed and private companies.

Optionally linked to a Stock row via stock_id/symbol for exchange-traded
companies. Private companies have stock_id = NULL and listing_status = "private".
Used as the anchor for Workspaces (one workspace → one company).
"""
from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String

from .base import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=True, index=True)
    symbol = Column(String(20), nullable=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    sector = Column(String(120), nullable=True, index=True)
    listing_status = Column(String(40), nullable=False, default="listed")
    exchange = Column(String(20), nullable=True)
    country = Column(String(80), nullable=False, default="India")
    market_cap = Column(Numeric(16, 2), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
