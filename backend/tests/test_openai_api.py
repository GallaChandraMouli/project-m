import asyncio
import json
import pytest
from app.models.node import Node, NodeModel
from app.api.ws.worker_hub import manager

def test_list_openai_models(client):
    res = client.get("/v1/models")
    assert res.status_code == 200
    data = res.json()
    assert data["object"] == "list"
    assert len(data["data"]) > 0
    assert "id" in data["data"][0]

def test_unauthenticated_chat_completion(client):
    res = client.post("/v1/chat/completions", json={
        "model": "llama3:8b",
        "messages": [{"role": "user", "content": "hello"}]
    })
    assert res.status_code == 401

def test_no_provider_available(client, consumer_headers):
    res = client.post(
        "/v1/chat/completions",
        json={"model": "nonexistent:model", "messages": [{"role": "user", "content": "hi"}]},
        headers=consumer_headers
    )
    assert res.status_code == 503
    assert "no online gpu providers" in res.json()["detail"].lower()

@pytest.mark.asyncio
async def test_non_streaming_chat_completion_with_worker(db, client, consumer_headers, provider_user):
    # 1. Setup online node in DB
    node = Node(
        provider_id=provider_user.id,
        node_token="nx-node-test-stream",
        name="Test Worker",
        status="online",
        tokens_per_sec_benchmark=60.0
    )
    db.add(node)
    db.commit()
    db.refresh(node)

    m = NodeModel(
        node_id=node.id,
        model_name="qwen2.5:7b",
        price_per_million_prompt=0.20,
        price_per_million_completion=0.40,
        is_active=True
    )
    db.add(m)
    db.commit()

    # 2. Mock Worker WebSocket in manager
    class MockWS:
        async def send_text(self, text):
            data = json.loads(text)
            if data.get("type") == "job_request":
                job_id = data["job_id"]
                # Push chunks into manager job stream
                await manager.push_chunk(job_id, {"type": "job_chunk", "delta": "Decentralized "})
                await manager.push_chunk(job_id, {"type": "job_chunk", "delta": "AI!"})
                await manager.push_chunk(job_id, {
                    "type": "job_done",
                    "job_id": job_id,
                    "prompt_tokens": 10,
                    "completion_tokens": 2,
                    "finish_reason": "stop"
                })

    manager.active_connections[node.id] = MockWS()

    try:
        # Request non-streaming completion
        res = client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen2.5:7b",
                "messages": [{"role": "user", "content": "Say AI"}],
                "stream": False
            },
            headers=consumer_headers
        )
        assert res.status_code == 200
        data = res.json()
        assert data["object"] == "chat.completion"
        assert data["choices"][0]["message"]["content"] == "Decentralized AI!"
        assert data["usage"]["completion_tokens"] == 2
    finally:
        manager.active_connections.pop(node.id, None)

@pytest.mark.asyncio
async def test_streaming_chat_completion_with_worker(db, client, consumer_headers, provider_user):
    node = Node(
        provider_id=provider_user.id,
        node_token="nx-node-test-stream-2",
        name="Stream Worker",
        status="online",
        tokens_per_sec_benchmark=75.0
    )
    db.add(node)
    db.commit()
    db.refresh(node)

    m = NodeModel(
        node_id=node.id,
        model_name="stream-model:7b",
        price_per_million_prompt=0.20,
        price_per_million_completion=0.40,
        is_active=True
    )
    db.add(m)
    db.commit()

    class MockStreamWS:
        async def send_text(self, text):
            data = json.loads(text)
            if data.get("type") == "job_request":
                job_id = data["job_id"]
                await manager.push_chunk(job_id, {"type": "job_chunk", "delta": "Hello "})
                await manager.push_chunk(job_id, {"type": "job_chunk", "delta": "World!"})
                await manager.push_chunk(job_id, {
                    "type": "job_done",
                    "job_id": job_id,
                    "prompt_tokens": 8,
                    "completion_tokens": 2,
                    "finish_reason": "stop"
                })

    manager.active_connections[node.id] = MockStreamWS()

    try:
        res = client.post(
            "/v1/chat/completions",
            json={
                "model": "stream-model:7b",
                "messages": [{"role": "user", "content": "Say Hello"}],
                "stream": True
            },
            headers=consumer_headers
        )
        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]
        
        # Verify SSE stream lines
        lines = [line for line in res.text.split("\n") if line.startswith("data: ")]
        assert len(lines) >= 3  # "Hello ", "World!", finish_reason stop, and [DONE]
        assert lines[-1] == "data: [DONE]"
    finally:
        manager.active_connections.pop(node.id, None)
