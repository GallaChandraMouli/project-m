import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base

class InferenceJob(Base):
    __tablename__ = "inference_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    consumer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    node_id = Column(String(36), ForeignKey("nodes.id", ondelete="SET NULL"), nullable=True, index=True)
    model_name = Column(String(100), nullable=False, index=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    provider_cut = Column(Float, default=0.0)
    platform_cut = Column(Float, default=0.0)
    latency_ms = Column(Integer, default=0)
    status = Column(String(30), default="pending")  # pending, streaming, completed, failed, timeout
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    consumer = relationship("User", back_populates="jobs")
    node = relationship("Node", back_populates="jobs")
