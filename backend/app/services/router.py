from typing import Optional, Tuple, List
from sqlalchemy.orm import Session

from app.models.node import Node, NodeModel
from app.api.ws.worker_hub import manager

def select_best_worker(
    db: Session,
    model_name: str,
    exclude_node_ids: Optional[List[str]] = None
) -> Optional[Tuple[str, float, float]]:
    """Selects the optimal active worker based on price, benchmark speed, and current concurrency.
    Returns (node_id, price_per_million_prompt, price_per_million_completion)."""
    exclude = set(exclude_node_ids or [])
    
    # 1. Get currently connected nodes that serve this model
    online_candidate_ids = [
        nid for nid in manager.active_connections.keys()
        if nid not in exclude
    ]
    
    if not online_candidate_ids:
        return None

    # 2. Query their database records and pricing
    candidates = (
        db.query(Node, NodeModel)
        .join(NodeModel, Node.id == NodeModel.node_id)
        .filter(
            Node.id.in_(online_candidate_ids),
            NodeModel.model_name == model_name,
            NodeModel.is_active == True,
            Node.status == "online"
        )
        .all()
    )
    
    if not candidates:
        return None

    # 3. Score candidates: lower concurrency, higher benchmark speed, lower completion price
    scored_nodes = []
    for node, model in candidates:
        concurrency = manager.node_concurrency.get(node.id, 0)
        speed = max(1.0, node.tokens_per_sec_benchmark)
        # Score formula: minimize cost & concurrency, maximize speed
        score = (model.price_per_million_completion * 1.5) + (concurrency * 0.5) - (speed * 0.01)
        scored_nodes.append((score, node.id, model.price_per_million_prompt, model.price_per_million_completion))

    scored_nodes.sort(key=lambda x: x[0])
    best = scored_nodes[0]
    return (best[1], best[2], best[3])
