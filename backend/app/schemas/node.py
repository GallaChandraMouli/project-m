from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

class NodeModelCreate(BaseModel):
    model_name: str
    price_per_million_prompt: Optional[float] = 0.20
    price_per_million_completion: Optional[float] = 0.40

class NodeModelOut(BaseModel):
    id: str
    model_name: str
    price_per_million_prompt: float
    price_per_million_completion: float
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class NodeRegister(BaseModel):
    name: str = "My GPU Node"

class NodeOut(BaseModel):
    id: str
    name: str
    gpu_name: str
    vram_mb: int
    status: str
    tokens_per_sec_benchmark: float
    node_token: str
    last_heartbeat: Optional[datetime] = None
    created_at: datetime
    models: List[NodeModelOut] = []

    model_config = ConfigDict(from_attributes=True)

class MarketplaceModelSummary(BaseModel):
    model_name: str
    active_providers_count: int
    min_prompt_price: float
    min_completion_price: float
    avg_tokens_per_sec: float
