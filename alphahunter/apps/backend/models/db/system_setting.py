"""SystemSetting — runtime-editable key/value configuration store.

Used by the Settings API endpoint and read by `utils/runtime_settings.py`
to supply tunable parameters (thresholds, cadence, pipeline mode) without
requiring a server restart. All values are stored as Text and parsed by
the reader (int/float/bool coercion happens at the call site).
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from .base import Base
import datetime

class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
