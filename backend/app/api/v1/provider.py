from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.security import generate_node_token
from app.models.user import User
from app.models.node import Node, NodeModel
from app.schemas.node import NodeRegister, NodeOut, NodeModelCreate, NodeModelOut
from app.api.v1.deps import get_current_user
from app.services.billing import get_or_create_wallet
from app.schemas.wallet import WalletOut, TransactionOut
from app.models.wallet import Transaction

router = APIRouter(prefix="/provider", tags=["provider"])

@router.get("/nodes", response_model=List[NodeOut])
def list_provider_nodes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Node)
        .filter(Node.provider_id == user.id)
        .order_by(desc(Node.created_at))
        .all()
    )

@router.post("/nodes/register", response_model=NodeOut)
def register_node(req: NodeRegister, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    node_token = generate_node_token()
    node = Node(
        provider_id=user.id,
        node_token=node_token,
        name=req.name,
        gpu_name="Pending Detection...",
        vram_mb=0,
        status="offline"
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    return node

@router.delete("/nodes/{node_id}")
def delete_node(node_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.id == node_id, Node.provider_id == user.id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    db.delete(node)
    db.commit()
    return {"message": "Node deleted successfully"}

@router.post("/nodes/{node_id}/models", response_model=NodeModelOut)
def configure_node_model(
    node_id: str,
    req: NodeModelCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Allows a provider to set custom pricing for a model they host."""
    node = db.query(Node).filter(Node.id == node_id, Node.provider_id == user.id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    model_obj = db.query(NodeModel).filter(NodeModel.node_id == node_id, NodeModel.model_name == req.model_name).first()
    if model_obj:
        model_obj.price_per_million_prompt = req.price_per_million_prompt
        model_obj.price_per_million_completion = req.price_per_million_completion
        model_obj.is_active = True
    else:
        model_obj = NodeModel(
            node_id=node_id,
            model_name=req.model_name,
            price_per_million_prompt=req.price_per_million_prompt,
            price_per_million_completion=req.price_per_million_completion
        )
        db.add(model_obj)
    
    db.commit()
    db.refresh(model_obj)
    return model_obj

@router.get("/earnings", response_model=WalletOut)
def get_provider_earnings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    wallet = get_or_create_wallet(db, user.id)
    transactions = (
        db.query(Transaction)
        .filter(Transaction.wallet_id == wallet.id, Transaction.type == "provider_earning")
        .order_by(desc(Transaction.created_at))
        .limit(20)
        .all()
    )
    
    return WalletOut(
        id=wallet.id,
        balance_credits=wallet.balance_credits,
        locked_credits=wallet.locked_credits,
        available_credits=wallet.balance_credits,
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
