from app.models.node import Node, NodeModel
from app.models.job import InferenceJob

def test_root_and_health_endpoints(client):
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "NexusCompute" in res_root.json()["message"]

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

def test_consumer_wallet_endpoint(client, consumer_headers, consumer_user):
    res = client.get("/api/v1/consumer/wallet", headers=consumer_headers)
    assert res.status_code == 200
    data = res.json()
    assert "balance_credits" in data
    assert "locked_credits" in data
    assert "available_credits" in data
    assert data["balance_credits"] >= 25.0

def test_consumer_usage_history_endpoint(db, client, consumer_headers, consumer_user):
    job = InferenceJob(
        consumer_id=consumer_user.id,
        model_name="llama3:8b",
        prompt_tokens=15,
        completion_tokens=25,
        total_cost=0.001,
        provider_cut=0.0009,
        platform_cut=0.0001,
        latency_ms=120,
        status="completed"
    )
    db.add(job)
    db.commit()

    res = client.get("/api/v1/consumer/usage", headers=consumer_headers)
    assert res.status_code == 200
    jobs = res.json()
    assert len(jobs) >= 1
    assert jobs[0]["model_name"] == "llama3:8b"
    assert jobs[0]["prompt_tokens"] == 15
    assert jobs[0]["completion_tokens"] == 25

def test_provider_earnings_endpoint(client, provider_headers, provider_user):
    res = client.get("/api/v1/provider/earnings", headers=provider_headers)
    assert res.status_code == 200
    data = res.json()
    assert "balance_credits" in data
    assert "recent_transactions" in data

def test_model_providers_list(db, client, provider_user):
    node = Node(
        provider_id=provider_user.id,
        node_token="nx-node-specific-provider",
        name="Special Rig",
        gpu_name="RTX 4090",
        vram_mb=24576,
        status="online",
        tokens_per_sec_benchmark=95.0
    )
    db.add(node)
    db.commit()
    db.refresh(node)

    nm = NodeModel(
        node_id=node.id,
        model_name="special-model:7b",
        price_per_million_prompt=0.15,
        price_per_million_completion=0.30,
        is_active=True
    )
    db.add(nm)
    db.commit()

    res = client.get("/api/v1/models/special-model:7b/providers")
    assert res.status_code == 200
    providers = res.json()
    assert len(providers) >= 1
    assert providers[0]["node_name"] == "Special Rig"
    assert providers[0]["gpu_name"] == "RTX 4090"
    assert providers[0]["tokens_per_sec"] == 95.0
