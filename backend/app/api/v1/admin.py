from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.user import User
from app.models.node import Node
from app.models.job import InferenceJob
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/stats")
def get_admin_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    users_count = db.query(func.count(User.id)).scalar() or 0
    online_nodes = db.query(func.count(Node.id)).filter(Node.status == "online").scalar() or 0
    total_nodes = db.query(func.count(Node.id)).scalar() or 0
    jobs_count = db.query(func.count(InferenceJob.id)).scalar() or 0
    total_tokens = db.query(func.sum(InferenceJob.prompt_tokens + InferenceJob.completion_tokens)).scalar() or 0
    platform_revenue = db.query(func.sum(InferenceJob.platform_cut)).filter(InferenceJob.status == "completed").scalar() or 0.0

    return {
        "total_users": users_count,
        "online_nodes": online_nodes,
        "total_nodes": total_nodes,
        "total_jobs": jobs_count,
        "total_tokens_processed": total_tokens,
        "platform_revenue_credits": round(platform_revenue, 4),
    }

@router.get("/nodes")
def get_admin_nodes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Node, User.email).join(User, Node.provider_id == User.id).all()
    return [
        {
            "id": node.id,
            "name": node.name,
            "gpu_name": node.gpu_name,
            "vram_mb": node.vram_mb,
            "status": node.status,
            "tokens_per_sec": node.tokens_per_sec_benchmark,
            "provider_email": email,
            "last_heartbeat": node.last_heartbeat,
            "created_at": node.created_at,
        }
        for node, email in rows
    ]
