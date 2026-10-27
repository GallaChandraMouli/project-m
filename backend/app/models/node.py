import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base

class Node(Base):
    __tablename__ = "nodes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    node_token = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(100), default="GPU-Node")
    gpu_name = Column(String(100), default="Generic GPU / CPU")
    vram_mb = Column(Integer, default=0)
    status = Column(String(20), default="offline")  # online, offline, busy
    tokens_per_sec_benchmark = Column(Float, default=0.0)
    last_heartbeat = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    provider = relationship("User", back_populates="nodes")
    models = relationship("NodeModel", back_populates="node", cascade="all, delete-orphan")
    jobs = relationship("InferenceJob", back_populates="node")

class NodeModel(Base):
    __tablename__ = "node_models"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    node_id = Column(String(36), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    model_name = Column(String(100), nullable=False, index=True)  # e.g., llama3:8b, mistral:7b
    price_per_million_prompt = Column(Float, default=0.20)  # $0.20 per 1M prompt tokens
    price_per_million_completion = Column(Float, default=0.40)  # $0.40 per 1M completion tokens
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    node = relationship("Node", back_populates="models")
