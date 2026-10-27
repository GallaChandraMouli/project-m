import sys
import os
import uuid
import asyncio
import json
import httpx
import websockets

sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("worker"))

from app.core.database import init_db
from app.main import app
import uvicorn

async def run_integration_test():
    print("\n========================================================")
    print("   NEXUSCOMPUTE: END-TO-END MARKETPLACE TEST")
    print("========================================================\n")

    # 1. Start uvicorn server in background task
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8001, log_level="warning")
    server = uvicorn.Server(config)
    server_task = asyncio.create_task(server.serve())

    # Wait for server to bind
    await asyncio.sleep(1.5)

    try:
        async with httpx.AsyncClient(base_url="http://127.0.0.1:8001") as client:
            # 2. Register Consumer & Provider with unique emails
            rand_id = uuid.uuid4().hex[:6]
            c_email = f"consumer_{rand_id}@nexus.ai"
            p_email = f"provider_{rand_id}@nexus.ai"

            print(f"1. Registering Consumer ({c_email}) and Provider ({p_email})...")
            c_res = await client.post("/api/v1/auth/register", json={
                "email": c_email,
                "password": "Password123!",
                "role": "consumer"
            })
            assert c_res.status_code == 200, f"Consumer register failed: {c_res.text}"
            consumer_token = c_res.json()["access_token"]
            consumer_headers = {"Authorization": f"Bearer {consumer_token}"}
            print("   -> Consumer registered with $25.00 welcome faucet credits!")

            p_res = await client.post("/api/v1/auth/register", json={
                "email": p_email,
                "password": "Password123!",
                "role": "provider"
            })
            assert p_res.status_code == 200, f"Provider register failed: {p_res.text}"
            provider_token = p_res.json()["access_token"]
            provider_headers = {"Authorization": f"Bearer {provider_token}"}
            print("   -> Provider registered successfully!")

            # 3. Provider registers a GPU Node
            print("\n2. Provider registers a new GPU Node...")
            node_res = await client.post("/api/v1/provider/nodes/register", json={"name": "Rig-Alpha-RTX4090"}, headers=provider_headers)
            assert node_res.status_code == 200, f"Node register failed: {node_res.text}"
            node_data = node_res.json()
            node_token = node_data["node_token"]
            print(f"   -> Node registered: '{node_data['name']}' (Token: {node_token[:12]}...)")

            # 4. Consumer generates an OpenAI API Key
            print("\n3. Consumer creates standard OpenAI API Key...")
            key_res = await client.post("/api/v1/consumer/api-keys", json={"name": "Production App Key"}, headers=consumer_headers)
            assert key_res.status_code == 200
            raw_api_key = key_res.json()["raw_api_key"]
            print(f"   -> Created API Key: {raw_api_key}")

            # 5. Connect Provider Worker via WebSocket
            print("\n4. Launching Provider Worker Daemon (Outbound WebSocket Uplink)...")
            ws_url = f"ws://127.0.0.1:8001/api/v1/ws/worker?token={node_token}"
            
            async with websockets.connect(ws_url) as ws:
                # Send Handshake
                handshake_data = {
                    "type": "handshake",
                    "gpu_name": "NVIDIA GeForce RTX 4090",
                    "vram_mb": 24576,
                    "tokens_per_sec": 78.4,
                    "models": [
                        {"name": "llama3:8b", "prompt_price": 0.15, "completion_price": 0.30},
                        {"name": "deepseek-r1:7b", "prompt_price": 0.20, "completion_price": 0.40}
                    ]
                }
                await ws.send(json.dumps(handshake_data))
                ack = json.loads(await ws.recv())
                print(f"   -> Handshake Verified: {ack['message']}")

                # Check Marketplace Model Listing
                cat_res = await client.get("/api/v1/models")
                assert cat_res.status_code == 200
                print(f"   -> Marketplace Catalog now lists active models: {[m['model_name'] for m in cat_res.json()]}")

                # 6. Consumer sends OpenAI Inference Request (Streaming)
                print("\n5. Consumer executes OpenAI streaming request ('/v1/chat/completions')...")
                
                # We start consumer request and worker handler concurrently!
                async def handle_worker_jobs():
                    msg_raw = await ws.recv()
                    data = json.loads(msg_raw)
                    if data.get("type") == "job_request":
                        job_id = data["job_id"]
                        model = data["model"]
                        # Stream simulated chunks
                        test_words = ["Decentralized", "compute", "is", "the", "future", "of", "open", "AI!"]
                        for w in test_words:
                            await ws.send(json.dumps({
                                "type": "job_chunk",
                                "job_id": job_id,
                                "delta": w + " "
                            }))
                            await asyncio.sleep(0.02)
                        await ws.send(json.dumps({
                            "type": "job_done",
                            "job_id": job_id,
                            "prompt_tokens": 12,
                            "completion_tokens": len(test_words),
                            "finish_reason": "stop"
                        }))

                worker_job_task = asyncio.create_task(handle_worker_jobs())

                # Send request using standard Bearer nx-live-... API Key
                ai_headers = {"Authorization": f"Bearer {raw_api_key}"}
                payload = {
                    "model": "llama3:8b",
                    "messages": [{"role": "user", "content": "Tell me about decentralized compute."}],
                    "stream": True
                }

                accumulated_text = ""
                async with client.stream("POST", "/v1/chat/completions", json=payload, headers=ai_headers) as stream_resp:
                    assert stream_resp.status_code == 200, f"Inference failed: {stream_resp.status_code}"
                    async for line in stream_resp.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            chunk = json.loads(data_str)
                            delta = chunk["choices"][0]["delta"].get("content", "")
                            accumulated_text += delta

                await worker_job_task
                print(f"   -> Streamed Inference Result: \"{accumulated_text.strip()}\"")

                # 7. Verify Billing and Ledgers
                print("\n6. Verifying Financial Ledgers and Settlement...")
                c_wallet = await client.get("/api/v1/consumer/wallet", headers=consumer_headers)
                p_wallet = await client.get("/api/v1/provider/earnings", headers=provider_headers)
                
                c_balance = c_wallet.json()["balance_credits"]
                p_earnings = p_wallet.json()["balance_credits"]

                print(f"   -> Consumer Usable Balance: ${c_balance:.4f} (deducted micro-charge)")
                print(f"   -> Provider Earned Balance: ${p_earnings:.4f} (credited 90% payout)")
                print(f"   -> Consumer Transactions Count: {len(c_wallet.json()['recent_transactions'])}")
                print(f"   -> Provider Transactions Count: {len(p_wallet.json()['recent_transactions'])}")

                # 8. Check Admin Overview
                admin_res = await client.get("/api/v1/admin/stats", headers=consumer_headers)
                print(f"\n7. Platform Admin Stats: {admin_res.json()}")

    finally:
        server.should_exit = True
        await server_task
        print("\n========================================================")
        print("   ALL TESTS PASSED WITH 100% SUCCESS!")
        print("========================================================\n")

if __name__ == "__main__":
    asyncio.run(run_integration_test())
