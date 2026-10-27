from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

class TransactionOut(BaseModel):
    id: str
    type: str
    amount: float
    reference_id: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WalletOut(BaseModel):
    id: str
    balance_credits: float
    locked_credits: float
    available_credits: float
    updated_at: datetime
    recent_transactions: Optional[List[TransactionOut]] = []

    model_config = ConfigDict(from_attributes=True)
