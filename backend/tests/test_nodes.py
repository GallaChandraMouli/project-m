from app.models.node import Node, NodeModel

def test_register_and_list_node(client, provider_headers):
    # Register Node
    res = client.post("/api/v1/provider/nodes/register", json={"name": "Homelab-3090"}, headers=provider_headers)
    assert res.status_code == 200
    node = res.json()
    assert node["name"] == "Homelab-3090"
    assert node["node_token"].startswith("nx-node-")
    assert node["status"] == "offline"

    # List Nodes
    list_res = client.get("/api/v1/provider/nodes", headers=provider_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

def test_configure_model_pricing(client, provider_headers):
    # 1. Register node
    node_res = client.post("/api/v1/provider/nodes/register", json={"name": "Rig-Dual-4090"}, headers=provider_headers)
    node_id = node_res.json()["id"]

    # 2. Configure model pricing
    price_res = client.post(
        f"/api/v1/provider/nodes/{node_id}/models",
        json={
            "model_name": "llama3:8b",
            "price_per_million_prompt": 0.18,
            "price_per_million_completion": 0.35
        },
        headers=provider_headers
    )
    assert price_res.status_code == 200
    m_data = price_res.json()
    assert m_data["model_name"] == "llama3:8b"
    assert m_data["price_per_million_prompt"] == 0.18
    assert m_data["price_per_million_completion"] == 0.35

def test_delete_node(client, provider_headers):
    node_res = client.post("/api/v1/provider/nodes/register", json={"name": "Temp-Node"}, headers=provider_headers)
    node_id = node_res.json()["id"]

    del_res = client.delete(f"/api/v1/provider/nodes/{node_id}", headers=provider_headers)
    assert del_res.status_code == 200

    # Verify not in list
    list_res = client.get("/api/v1/provider/nodes", headers=provider_headers)
    assert not any(n["id"] == node_id for n in list_res.json())

def test_marketplace_models_aggregation(db, client, provider_user):
    # Add active online node with model in DB
    node = Node(
        provider_id=provider_user.id,
        node_token="nx-node-active-test",
        name="Active Node",
        gpu_name="NVIDIA RTX 4090",
        vram_mb=24576,
        status="online",
        tokens_per_sec_benchmark=68.5
    )
    db.add(node)
    db.commit()
    db.refresh(node)

    nm = NodeModel(
        node_id=node.id,
        model_name="deepseek-r1:7b",
        price_per_million_prompt=0.20,
        price_per_million_completion=0.40,
        is_active=True
    )
    db.add(nm)
    db.commit()

    res = client.get("/api/v1/models")
    assert res.status_code == 200
    models = res.json()
    found = next((m for m in models if m["model_name"] == "deepseek-r1:7b"), None)
    assert found is not None
    assert found["active_providers_count"] >= 1
    assert found["min_prompt_price"] == 0.20
    assert found["min_completion_price"] == 0.40
    assert found["avg_tokens_per_sec"] == 68.5
