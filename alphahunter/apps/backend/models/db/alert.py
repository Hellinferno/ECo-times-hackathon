from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, DateTime, ForeignKey, Index, Uuid
from .base import Base
import datetime
import uuid

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Uuid, unique=True, nullable=False, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False)
    decision_id = Column(Uuid, ForeignKey('decisions.decision_id'))
    alert_type = Column(String(30), nullable=False)
    message = Column(Text, nullable=False)
    confidence = Column(Numeric(5, 2))
    action = Column(String(10))
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

Index('idx_alerts_created_at', Alert.created_at.desc())
