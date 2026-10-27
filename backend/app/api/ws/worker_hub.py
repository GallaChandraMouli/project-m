import asyncio
import json
import logging
from typing import Dict, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.database import SessionLocal
from app.models.node import Node, NodeModel

logger = logging.getLogger("worker_hub")
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/ws", tags=["websocket"])

class WorkerConnectionManager:
    def __init__(self):
        # Map node_id -> active WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Map node_id -> set of served model names
        self.node_models: Dict[str, Dict[str, dict]] = {}
        # Map job_id -> asyncio.Queue for streaming chunks back to the HTTP gateway
        self.job_streams: Dict[str, asyncio.Queue] = {}
        # Map node_id -> current job concurrency count
        self.node_concurrency: Dict[str, int] = {}

    async def connect(self, node_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[node_id] = websocket
        self.node_concurrency[node_id] = 0
        logger.info(f"Node {node_id} connected via WebSocket.")

    async def disconnect(self, node_id: str):
        if node_id in self.active_connections:
            del self.active_connections[node_id]
        if node_id in self.node_models:
            del self.node_models[node_id]
        if node_id in self.node_concurrency:
            del self.node_concurrency[node_id]
        
        # Mark offline in DB
        with SessionLocal() as db:
            node = db.query(Node).filter(Node.id == node_id).first()
            if node:
                node.status = "offline"
                db.commit()
        logger.info(f"Node {node_id} disconnected and marked offline.")

    def is_online(self, node_id: str) -> bool:
        return node_id in self.active_connections

    async def send_to_node(self, node_id: str, message: dict) -> bool:
        ws = self.active_connections.get(node_id)
        if not ws:
            return False
        try:
            await ws.send_text(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Error sending message to node {node_id}: {e}")
            return False

    def create_job_stream(self, job_id: str) -> asyncio.Queue:
        q = asyncio.Queue()
        self.job_streams[job_id] = q
        return q

    def remove_job_stream(self, job_id: str):
        if job_id in self.job_streams:
            del self.job_streams[job_id]

    async def push_chunk(self, job_id: str, data: dict):
        if job_id in self.job_streams:
            await self.job_streams[job_id].put(data)

manager = WorkerConnectionManager()

@router.websocket("/worker")
async def websocket_worker_endpoint(websocket: WebSocket, token: str = Query(...)):
    """Outbound WebSocket endpoint where provider worker daemons connect."""
    node_id: Optional[str] = None
    
    # 1. Authenticate Node Token
    with SessionLocal() as db:
        node = db.query(Node).filter(Node.node_token == token).first()
        if not node:
            logger.warning(f"Rejected connection for invalid node token: {token}")
            await websocket.close(code=4001, reason="Invalid Node Token")
            return
        node_id = node.id
        node.status = "online"
        node.last_heartbeat = datetime.now(timezone.utc)
        db.commit()

    await manager.connect(node_id, websocket)

    try:
        while True:
            raw_text = await websocket.receive_text()
            data = json.loads(raw_text)
            msg_type = data.get("type")

            if msg_type == "handshake":
                gpu_name = data.get("gpu_name", "Generic GPU")
                vram_mb = data.get("vram_mb", 0)
                benchmark_speed = float(data.get("tokens_per_sec", 42.5))
                models_list = data.get("models", [])

                with SessionLocal() as db:
                    current_node = db.query(Node).filter(Node.id == node_id).first()
                    if current_node:
                        current_node.gpu_name = gpu_name
                        current_node.vram_mb = vram_mb
                        current_node.tokens_per_sec_benchmark = benchmark_speed
                        current_node.status = "online"
                        current_node.last_heartbeat = datetime.now(timezone.utc)

                        manager.node_models[node_id] = {}
                        for m in models_list:
                            m_name = m.get("name") if isinstance(m, dict) else str(m)
                            p_price = m.get("prompt_price", 0.20) if isinstance(m, dict) else 0.20
                            c_price = m.get("completion_price", 0.40) if isinstance(m, dict) else 0.40

                            manager.node_models[node_id][m_name] = {
                                "prompt_price": p_price,
                                "completion_price": c_price,
                            }

                            existing_m = db.query(NodeModel).filter(
                                NodeModel.node_id == node_id,
                                NodeModel.model_name == m_name
                            ).first()

                            if existing_m:
                                existing_m.is_active = True
                                existing_m.price_per_million_prompt = p_price
                                existing_m.price_per_million_completion = c_price
                            else:
                                new_m = NodeModel(
                                    node_id=node_id,
                                    model_name=m_name,
                                    price_per_million_prompt=p_price,
                                    price_per_million_completion=c_price,
                                    is_active=True
                                )
                                db.add(new_m)
                        db.commit()

                await websocket.send_text(json.dumps({
                    "type": "handshake_ack",
                    "status": "verified",
                    "message": f"Worker successfully registered with {len(models_list)} model(s)."
                }))

            elif msg_type == "heartbeat":
                with SessionLocal() as db:
                    n = db.query(Node).filter(Node.id == node_id).first()
                    if n:
                        n.last_heartbeat = datetime.now(timezone.utc)
                        n.status = "online"
                        db.commit()
                await websocket.send_text(json.dumps({"type": "heartbeat_ack"}))

            elif msg_type == "job_chunk":
                job_id = data.get("job_id")
                await manager.push_chunk(job_id, data)

            elif msg_type == "job_done":
                job_id = data.get("job_id")
                await manager.push_chunk(job_id, data)
                if node_id in manager.node_concurrency:
                    manager.node_concurrency[node_id] = max(0, manager.node_concurrency[node_id] - 1)

            elif msg_type == "job_error":
                job_id = data.get("job_id")
                await manager.push_chunk(job_id, data)
                if node_id in manager.node_concurrency:
                    manager.node_concurrency[node_id] = max(0, manager.node_concurrency[node_id] - 1)

    except WebSocketDisconnect:
        await manager.disconnect(node_id)
    except Exception as e:
        logger.error(f"WebSocket error for node {node_id}: {e}")
        await manager.disconnect(node_id)
