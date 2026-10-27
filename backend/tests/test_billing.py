import pytest
from fastapi import HTTPException
from app.services.billing import hold_escrow, release_escrow, settle_job_billing, get_or_create_wallet
from app.models.wallet import Wallet
from app.models.node import Node

def test_wallet_initial_faucet(db, consumer_user):
    wallet = get_or_create_wallet(db, consumer_user.id)
    assert wallet.balance_credits == 25.0
    assert wallet.locked_credits == 0.0

def test_hold_and_release_escrow(db, consumer_user):
    wallet = get_or_create_wallet(db, consumer_user.id)
    assert wallet.locked_credits == 0.0

    # Hold escrow
    hold_escrow(db, consumer_user.id, estimated_amount=0.05)
    assert wallet.locked_credits == 0.05

    # Release escrow
    release_escrow(db, consumer_user.id, amount=0.05)
    assert wallet.locked_credits == 0.0

def test_hold_escrow_insufficient_funds(db, consumer_user):
    wallet = get_or_create_wallet(db, consumer_user.id)
    wallet.balance_credits = 0.01  # less than 0.05
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        hold_escrow(db, consumer_user.id, estimated_amount=0.05)
    assert exc_info.value.status_code == 402
    assert "insufficient credit balance" in exc_info.value.detail.lower()

def test_settle_job_billing_split_and_ledger(db, consumer_user, provider_user):
    # Setup node for provider
    node = Node(
        provider_id=provider_user.id,
        node_token="nx-node-test-123",
        name="Test Rig"
    )
    db.add(node)
    db.commit()
    db.refresh(node)

    # Consumer initial: 25.0, Provider initial: 25.0
    c_wallet = get_or_create_wallet(db, consumer_user.id)
    p_wallet = get_or_create_wallet(db, provider_user.id)
    
    # Pre-hold escrow
    hold_escrow(db, consumer_user.id, 0.05)

    # 10,000 prompt tokens @ $0.20/M = $0.002
    # 20,000 completion tokens @ $0.40/M = $0.008
    # Total cost = $0.010
    total_cost, prov_cut, plat_cut = settle_job_billing(
        db,
        consumer_id=consumer_user.id,
        node_id=node.id,
        prompt_tokens=10000,
        completion_tokens=20000,
        price_per_million_prompt=0.20,
        price_per_million_completion=0.40,
        job_id="test_job_1",
        escrow_held=0.05
    )

    assert total_cost == 0.01
    assert plat_cut == 0.001  # 10%
    assert prov_cut == 0.009  # 90%

    # Check balances
    assert round(c_wallet.balance_credits, 4) == 24.9900
    assert c_wallet.locked_credits == 0.0
    assert round(p_wallet.balance_credits, 4) == 25.0090

def test_claim_faucet_endpoint(client, consumer_headers, consumer_user):
    res = client.post("/api/v1/consumer/wallet/faucet", headers=consumer_headers)
    assert res.status_code == 200
    data = res.json()
    assert "new_balance" in data
    assert data["new_balance"] >= 50.0  # 25 initial + 25 claimed
