from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.node import Node, NodeModel
from app.schemas.node import MarketplaceModelSummary

router = APIRouter(prefix="/models", tags=["models"])

@router.get("", response_model=List[MarketplaceModelSummary])
def list_marketplace_models(db: Session = Depends(get_db)):
    """Aggregates all actively served models across online nodes."""
    rows = (
        db.query(
            NodeModel.model_name,
            func.count(Node.id).label("active_providers_count"),
            func.min(NodeModel.price_per_million_prompt).label("min_prompt_price"),
            func.min(NodeModel.price_per_million_completion).label("min_completion_price"),
            func.avg(Node.tokens_per_sec_benchmark).label("avg_tokens_per_sec"),
        )
        .join(Node, Node.id == NodeModel.node_id)
        .filter(Node.status == "online", NodeModel.is_active == True)
        .group_by(NodeModel.model_name)
        .all()
    )
    
    summaries = []
    for r in rows:
        summaries.append(
            MarketplaceModelSummary(
                model_name=r.model_name,
                active_providers_count=r.active_providers_count or 0,
                min_prompt_price=round(r.min_prompt_price or 0.20, 4),
                min_completion_price=round(r.min_completion_price or 0.40, 4),
                avg_tokens_per_sec=round(r.avg_tokens_per_sec or 35.0, 1),
            )
        )
    return summaries

@router.get("/{model_name}/providers")
def get_model_providers(model_name: str, db: Session = Depends(get_db)):
    """Lists online provider nodes serving a specific model."""
    pairs = (
        db.query(Node, NodeModel)
        .join(NodeModel, Node.id == NodeModel.node_id)
        .filter(
            NodeModel.model_name == model_name,
            Node.status == "online",
            NodeModel.is_active == True
        )
        .all()
    )
    
    providers = []
    for node, model in pairs:
        providers.append({
            "node_id": node.id,
            "node_name": node.name,
            "gpu_name": node.gpu_name,
            "vram_mb": node.vram_mb,
            "tokens_per_sec": node.tokens_per_sec_benchmark,
            "prompt_price_m": model.price_per_million_prompt,
            "completion_price_m": model.price_per_million_completion,
        })
    return providers
