import asyncio
import json
import logging
from typing import Dict, Any, List
import websockets

from nexus_worker.hardware import detect_hardware
from nexus_worker.engine import InferenceEngineClient

logger = logging.getLogger("nexus_worker")

class WorkerDaemon:
    def __init__(
        self,
        node_token: str,
        server_ws_url: str = "ws://localhost:8000/api/v1/ws/worker",
        ollama_url: str = "http://localhost:11434",
        vllm_url: str = "http://localhost:8000",
        emulate: bool = False,
        prompt_price: float = 0.20,
        completion_price: float = 0.40
    ):
        self.node_token = node_token
        self.server_ws_url = server_ws_url
        self.prompt_price = prompt_price
        self.completion_price = completion_price
        self.engine = InferenceEngineClient(ollama_url=ollama_url, vllm_url=vllm_url, emulate=emulate)
        self.running = False

    async def start(self):
        self.running = True
        
        # 1. Detect hardware
        hw = detect_hardware()
        print(f"\n[NexusCompute Worker] Detected Hardware: {hw['gpu_name']} ({hw['vram_mb']} MB VRAM)")

        # 2. Discover local models
        models = self.engine.discover_models()
        print(f"[NexusCompute Worker] Engine: {self.engine.active_engine.upper()} | Discovered {len(models)} model(s): {', '.join(models)}")

        # 3. Benchmark tokens/sec
        print("[NexusCompute Worker] Running startup synthetic benchmark probe...")
        bench_speed = await self.engine.run_benchmark()
        print(f"[NexusCompute Worker] Benchmark Result: {bench_speed} tokens/second")

        url = f"{self.server_ws_url}?token={self.node_token}"

        # Reconnect loop
        backoff = 2
        while self.running:
            try:
                print(f"[NexusCompute Worker] Connecting outbound to coordinator at {self.server_ws_url}...")
                async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
                    print("[NexusCompute Worker] Connected successfully to NexusCompute Coordinator!")
                    backoff = 2  # Reset backoff

                    # Send Handshake
                    handshake_payload = {
                        "type": "handshake",
                        "gpu_name": hw["gpu_name"],
                        "vram_mb": hw["vram_mb"],
                        "tokens_per_sec": bench_speed,
                        "models": [
                            {
                                "name": m,
                                "prompt_price": self.prompt_price,
                                "completion_price": self.completion_price
                            }
                            for m in models
                        ]
                    }
                    await ws.send(json.dumps(handshake_payload))

                    # Start background heartbeat task
                    heartbeat_task = asyncio.create_task(self._heartbeat_loop(ws))

                    try:
                        while self.running:
                            message_raw = await ws.recv()
                            data = json.loads(message_raw)
                            msg_type = data.get("type")

                            if msg_type == "handshake_ack":
                                print(f"[NexusCompute Worker] Coordinator verified node: {data.get('message')}")
                                print("[NexusCompute Worker] Node is now ONLINE and ready to serve inference requests.\n")

                            elif msg_type == "job_request":
                                # Dispatch job asynchronously
                                asyncio.create_task(self._handle_job(ws, data))

                    finally:
                        heartbeat_task.cancel()

            except (websockets.ConnectionClosed, OSError) as e:
                print(f"[NexusCompute Worker] Connection dropped ({e}). Reconnecting in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff = min(30, backoff * 1.5)
            except Exception as e:
                print(f"[NexusCompute Worker] Unexpected error: {e}")
                await asyncio.sleep(backoff)

    async def _heartbeat_loop(self, ws):
        while True:
            await asyncio.sleep(15)
            try:
                await ws.send(json.dumps({"type": "heartbeat"}))
            except Exception:
                break

    async def _handle_job(self, ws, job_data: dict):
        job_id = job_data.get("job_id")
        model = job_data.get("model")
        messages = job_data.get("messages", [])
        temperature = job_data.get("temperature", 0.7)
        max_tokens = job_data.get("max_tokens", 1024)

        print(f"[NexusCompute Worker] >> Starting Job {job_id[:8]} for model '{model}'...")
        try:
            tokens_count = 0
            async for chunk in self.engine.stream_chat(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                if chunk["type"] == "chunk":
                    tokens_count += 1
                    await ws.send(json.dumps({
                        "type": "job_chunk",
                        "job_id": job_id,
                        "delta": chunk["delta"]
                    }))
                elif chunk["type"] == "done":
                    await ws.send(json.dumps({
                        "type": "job_done",
                        "job_id": job_id,
                        "prompt_tokens": chunk.get("prompt_tokens", 15),
                        "completion_tokens": chunk.get("completion_tokens", tokens_count),
                        "finish_reason": "stop"
                    }))
                    print(f"[NexusCompute Worker] << Job {job_id[:8]} Completed ({tokens_count} tokens streamed).")
                    return

        except Exception as e:
            print(f"[NexusCompute Worker] !! Job {job_id[:8]} Error: {e}")
            await ws.send(json.dumps({
                "type": "job_error",
                "job_id": job_id,
                "error": str(e)
            }))
