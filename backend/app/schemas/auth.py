from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class UserRegister(BaseModel):
    email: str
    password: str
    role: Optional[str] = "consumer"  # consumer or provider

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    email: str

class UserOut(BaseModel):
    id: str
    email: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
