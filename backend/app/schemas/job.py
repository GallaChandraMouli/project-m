from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class InferenceJobOut(BaseModel):
    id: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_cost: float
    provider_cut: float
    platform_cut: float
    latency_ms: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
