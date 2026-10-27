from app.models.node import Node, NodeModel
from app.services.router import select_best_worker
from app.api.ws.worker_hub import manager

def test_select_best_worker_no_online_nodes(db):
    worker = select_best_worker(db, "llama3:8b")
    assert worker is None

def test_select_best_worker_and_failover(db, provider_user):
    # Setup two nodes in DB
    node_cheap = Node(
        provider_id=provider_user.id,
        node_token="nx-node-cheap",
        name="Cheap Node",
        gpu_name="RTX 3080",
        vram_mb=10240,
        status="online",
        tokens_per_sec_benchmark=45.0
    )
    node_fast = Node(
        provider_id=provider_user.id,
        node_token="nx-node-fast",
        name="Fast Node",
        gpu_name="RTX 4090",
        vram_mb=24576,
        status="online",
        tokens_per_sec_benchmark=85.0
    )
    db.add_all([node_cheap, node_fast])
    db.commit()
    db.refresh(node_cheap)
    db.refresh(node_fast)

    # Models: cheap is $0.20, fast is $0.60
    m_cheap = NodeModel(
        node_id=node_cheap.id,
        model_name="mistral:7b",
        price_per_million_prompt=0.10,
        price_per_million_completion=0.20,
        is_active=True
    )
    m_fast = NodeModel(
        node_id=node_fast.id,
        model_name="mistral:7b",
        price_per_million_prompt=0.25,
        price_per_million_completion=0.60,
        is_active=True
    )
    db.add_all([m_cheap, m_fast])
    db.commit()

    # Mock active WebSocket connections in connection manager
    class MockWS:
        pass

    manager.active_connections[node_cheap.id] = MockWS()
    manager.active_connections[node_fast.id] = MockWS()

    try:
        # First choice should pick cheap node (best cost-efficiency)
        best = select_best_worker(db, "mistral:7b")
        assert best is not None
        assert best[0] == node_cheap.id
        assert best[1] == 0.10
        assert best[2] == 0.20

        # Simulate failover retry: exclude cheap node
        backup = select_best_worker(db, "mistral:7b", exclude_node_ids=[node_cheap.id])
        assert backup is not None
        assert backup[0] == node_fast.id
        assert backup[2] == 0.60

        # Exclude both -> None
        none_left = select_best_worker(db, "mistral:7b", exclude_node_ids=[node_cheap.id, node_fast.id])
        assert none_left is None

    finally:
        manager.active_connections.pop(node_cheap.id, None)
        manager.active_connections.pop(node_fast.id, None)
