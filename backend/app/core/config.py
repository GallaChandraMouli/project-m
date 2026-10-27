import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "NexusCompute"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "nexus-compute-super-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Modern, zero-deadlock SQLite configuration for instant local dev & high concurrency
    DATABASE_URL: str = "sqlite:///./nexuscompute.db"
    
    # Financial economics
    PLATFORM_FEE_PERCENT: float = 0.10  # 10% platform fee
    INITIAL_FAUCET_CREDITS: float = 25.00  # $25.00 free credits for testing
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()
