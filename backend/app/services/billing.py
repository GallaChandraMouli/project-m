from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.config import settings
from app.models.wallet import Wallet, Transaction
from app.models.node import Node

def get_or_create_wallet(db: Session, user_id: str) -> Wallet:
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        wallet = Wallet(user_id=user_id, balance_credits=settings.INITIAL_FAUCET_CREDITS)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
        
        # Log initial welcome faucet transaction
        tx = Transaction(
            wallet_id=wallet.id,
            type="faucet",
            amount=settings.INITIAL_FAUCET_CREDITS,
            description="Welcome credit faucet bonus"
        )
        db.add(tx)
        db.commit()
    return wallet

def hold_escrow(db: Session, user_id: str, estimated_amount: float = 0.05) -> bool:
    """Pre-authorizes a small credit hold to prevent negative balance abuse."""
    wallet = get_or_create_wallet(db, user_id)
    available = wallet.balance_credits - wallet.locked_credits
    if available < estimated_amount:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credit balance ({available:.4f} credits available, required minimum {estimated_amount:.4f}). Claim test credits in the consumer dashboard."
        )
    wallet.locked_credits += estimated_amount
    db.commit()
    return True

def release_escrow(db: Session, user_id: str, amount: float = 0.05):
    """Releases escrow hold in case of job error/cancellation."""
    wallet = get_or_create_wallet(db, user_id)
    wallet.locked_credits = max(0.0, wallet.locked_credits - amount)
    db.commit()

def settle_job_billing(
    db: Session,
    consumer_id: str,
    node_id: str,
    prompt_tokens: int,
    completion_tokens: int,
    price_per_million_prompt: float,
    price_per_million_completion: float,
    job_id: str,
    escrow_held: float = 0.05
):
    """Calculates final billing, credits provider (90%), takes platform cut (10%), and settles consumer balance."""
    prompt_cost = (prompt_tokens / 1_000_000.0) * price_per_million_prompt
    completion_cost = (completion_tokens / 1_000_000.0) * price_per_million_completion
    total_cost = max(0.0001, prompt_cost + completion_cost)  # Minimum micro-transaction $0.0001
    
    platform_cut = round(total_cost * settings.PLATFORM_FEE_PERCENT, 6)
    provider_cut = round(total_cost - platform_cut, 6)

    # 1. Deduct consumer wallet
    consumer_wallet = get_or_create_wallet(db, consumer_id)
    consumer_wallet.locked_credits = max(0.0, consumer_wallet.locked_credits - escrow_held)
    consumer_wallet.balance_credits = max(0.0, consumer_wallet.balance_credits - total_cost)

    consumer_tx = Transaction(
        wallet_id=consumer_wallet.id,
        type="inference_spend",
        amount=-total_cost,
        reference_id=job_id,
        description=f"Inference job {job_id[:8]} ({prompt_tokens}p + {completion_tokens}c tokens)"
    )
    db.add(consumer_tx)

    # 2. Credit provider wallet
    if node_id:
        node = db.query(Node).filter(Node.id == node_id).first()
        if node and node.provider_id:
            provider_wallet = get_or_create_wallet(db, node.provider_id)
            provider_wallet.balance_credits += provider_cut
            provider_tx = Transaction(
                wallet_id=provider_wallet.id,
                type="provider_earning",
                amount=provider_cut,
                reference_id=job_id,
                description=f"Earnings from job {job_id[:8]}"
            )
            db.add(provider_tx)

    db.commit()
    return total_cost, provider_cut, platform_cut
