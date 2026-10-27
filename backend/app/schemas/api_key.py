from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class ApiKeyCreate(BaseModel):
    name: Optional[str] = "Default API Key"

class ApiKeyOut(BaseModel):
    id: str
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ApiKeyCreatedResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    raw_api_key: str  # Only returned once upon creation!
    created_at: datetime
