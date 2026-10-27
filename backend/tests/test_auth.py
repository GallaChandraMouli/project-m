def test_register_consumer_success(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "new_consumer@test.com",
        "password": "SecurePassword123",
        "role": "consumer"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "consumer"
    assert data["email"] == "new_consumer@test.com"

def test_register_provider_success(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "new_provider@test.com",
        "password": "SecurePassword123",
        "role": "provider"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "provider"

def test_register_duplicate_email(client, consumer_user):
    res = client.post("/api/v1/auth/register", json={
        "email": consumer_user.email,
        "password": "AnyPassword",
        "role": "consumer"
    })
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"].lower()

def test_login_success(client, consumer_user):
    res = client.post("/api/v1/auth/login", json={
        "email": consumer_user.email,
        "password": "Password123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user_id"] == consumer_user.id

def test_login_wrong_password(client, consumer_user):
    res = client.post("/api/v1/auth/login", json={
        "email": consumer_user.email,
        "password": "IncorrectPassword"
    })
    assert res.status_code == 401
    assert "invalid email or password" in res.json()["detail"].lower()

def test_login_nonexistent_email(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "ghost@doesnotexist.com",
        "password": "Password123!"
    })
    assert res.status_code == 401

def test_get_me_authenticated(client, consumer_headers, consumer_user):
    res = client.get("/api/v1/auth/me", headers=consumer_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == consumer_user.id
    assert data["email"] == consumer_user.email

def test_get_me_unauthorized(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
