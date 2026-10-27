from app.models.node import Node

def test_admin_stats_endpoint(client, consumer_headers):
    res = client.get("/api/v1/admin/stats", headers=consumer_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_users" in data
    assert "online_nodes" in data
    assert "total_nodes" in data
    assert "total_jobs" in data
    assert "total_tokens_processed" in data
    assert "platform_revenue_credits" in data
    assert data["total_users"] >= 1

def test_admin_nodes_endpoint(db, client, consumer_headers, provider_user):
    # Add a node for provider
    node = Node(
        provider_id=provider_user.id,
        node_token="nx-node-admin-test",
        name="Admin Monitored Rig",
        gpu_name="NVIDIA A100",
        vram_mb=81920,
        status="online",
        tokens_per_sec_benchmark=110.0
    )
    db.add(node)
    db.commit()
    db.refresh(node)

    res = client.get("/api/v1/admin/nodes", headers=consumer_headers)
    assert res.status_code == 200
    nodes = res.json()
    assert len(nodes) >= 1
    found = next((n for n in nodes if n["id"] == node.id), None)
    assert found is not None
    assert found["name"] == "Admin Monitored Rig"
    assert found["provider_email"] == provider_user.email
    assert found["gpu_name"] == "NVIDIA A100"
    assert found["vram_mb"] == 81920
