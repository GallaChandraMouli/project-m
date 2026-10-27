from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.security import generate_api_key
from app.models.user import User
from app.models.wallet import Wallet, Transaction
from app.models.api_key import ApiKey
from app.models.job import InferenceJob
from app.schemas.wallet import WalletOut, TransactionOut
from app.schemas.api_key import ApiKeyCreate, ApiKeyOut, ApiKeyCreatedResponse
from app.schemas.job import InferenceJobOut
from app.api.v1.deps import get_current_user
from app.services.billing import get_or_create_wallet

router = APIRouter(prefix="/consumer", tags=["consumer"])

@router.get("/wallet", response_model=WalletOut)
def get_wallet(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    wallet = get_or_create_wallet(db, user.id)
    transactions = (
        db.query(Transaction)
        .filter(Transaction.wallet_id == wallet.id)
        .order_by(desc(Transaction.created_at))
        .limit(20)
        .all()
    )
    
    return WalletOut(
        id=wallet.id,
        balance_credits=wallet.balance_credits,
        locked_credits=wallet.locked_credits,
        available_credits=max(0.0, wallet.balance_credits - wallet.locked_credits),
        updated_at=wallet.updated_at,
        recent_transactions=[
            TransactionOut(
                id=t.id,
                type=t.type,
                amount=t.amount,
                reference_id=t.reference_id,
                description=t.description,
                created_at=t.created_at
            ) for t in transactions
        ]
    )

@router.post("/wallet/faucet")
def claim_faucet(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Dispenses test credits to test inference jobs."""
    wallet = get_or_create_wallet(db, user.id)
    amount = 25.0
    wallet.balance_credits += amount
    
    tx = Transaction(
        wallet_id=wallet.id,
        type="faucet",
        amount=amount,
        description="Testnet faucet top-up"
    )
    db.add(tx)
    db.commit()
    db.refresh(wallet)
    return {"message": f"Successfully claimed {amount} test credits!", "new_balance": wallet.balance_credits}

@router.get("/api-keys", response_model=List[ApiKeyOut])
def list_api_keys(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(ApiKey).filter(ApiKey.user_id == user.id).order_by(desc(ApiKey.created_at)).all()

@router.post("/api-keys", response_model=ApiKeyCreatedResponse)
def create_api_key(req: ApiKeyCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    raw_key, key_hash, prefix = generate_api_key(req.name)
    api_key_obj = ApiKey(
        user_id=user.id,
        key_hash=key_hash,
        key_prefix=prefix,
        name=req.name
    )
    db.add(api_key_obj)
    db.commit()
    db.refresh(api_key_obj)
    
    return ApiKeyCreatedResponse(
        id=api_key_obj.id,
        name=api_key_obj.name,
        key_prefix=api_key_obj.key_prefix,
        raw_api_key=raw_key,
        created_at=api_key_obj.created_at
    )

@router.delete("/api-keys/{key_id}")
def revoke_api_key(key_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    key_obj = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.user_id == user.id).first()
    if not key_obj:
        raise HTTPException(status_code=404, detail="API key not found")
    
    db.delete(key_obj)
    db.commit()
    return {"message": "API key revoked successfully"}

@router.get("/usage", response_model=List[InferenceJobOut])
def get_usage_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(InferenceJob)
        .filter(InferenceJob.consumer_id == user.id)
        .order_by(desc(InferenceJob.created_at))
        .limit(50)
        .all()
    )
