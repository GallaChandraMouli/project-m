def test_create_and_list_api_keys(client, consumer_headers):
    # 1. Create key
    create_res = client.post("/api/v1/consumer/api-keys", json={"name": "Production Service"}, headers=consumer_headers)
    assert create_res.status_code == 200
    created = create_res.json()
    assert "raw_api_key" in created
    assert created["raw_api_key"].startswith("nx-live-")
    assert created["name"] == "Production Service"
    raw_key = created["raw_api_key"]

    # 2. List keys
    list_res = client.get("/api/v1/consumer/api-keys", headers=consumer_headers)
    assert list_res.status_code == 200
    keys = list_res.json()
    assert len(keys) >= 1
    found = next((k for k in keys if k["id"] == created["id"]), None)
    assert found is not None
    assert "raw_api_key" not in found  # Security: raw key never returned in lists
    assert found["key_prefix"] == raw_key[:12]

def test_api_key_authentication(client, consumer_headers):
    # Create key
    create_res = client.post("/api/v1/consumer/api-keys", json={"name": "Auth Test Key"}, headers=consumer_headers)
    raw_key = create_res.json()["raw_api_key"]
    key_id = create_res.json()["id"]

    # Authenticate against /v1/chat/completions with API key
    # Even if no workers are online, auth should pass (and return 503 instead of 401)
    res = client.post(
        "/v1/chat/completions",
        json={"model": "llama3:8b", "messages": [{"role": "user", "content": "hello"}]},
        headers={"Authorization": f"Bearer {raw_key}"}
    )
    # 503 means authentication succeeded, but no provider is online for llama3:8b
    assert res.status_code == 503

    # Revoke key
    rev_res = client.delete(f"/api/v1/consumer/api-keys/{key_id}", headers=consumer_headers)
    assert rev_res.status_code == 200

    # Try again with revoked key -> should be 401 Unauthorized
    rev_auth_res = client.post(
        "/v1/chat/completions",
        json={"model": "llama3:8b", "messages": [{"role": "user", "content": "hello"}]},
        headers={"Authorization": f"Bearer {raw_key}"}
    )
    assert rev_auth_res.status_code == 401
