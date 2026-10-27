import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="consumer")  # consumer, provider, admin
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    wallet = relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    nodes = relationship("Node", back_populates="provider", cascade="all, delete-orphan")
    jobs = relationship("InferenceJob", back_populates="consumer", cascade="all, delete-orphan")
