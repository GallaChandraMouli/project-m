import uuid
import time
import json
import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.models.user import User
from app.models.node import Node, NodeModel
from app.models.job import InferenceJob
from app.schemas.openai import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatCompletionResponseChoiceMsg,
    UsageInfo,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionChunkDelta,
)
from app.api.v1.deps import get_authenticated_consumer
from app.api.ws.worker_hub import manager
from app.services.tokenizer import count_messages_tokens
from app.services.billing import hold_escrow, release_escrow, settle_job_billing
from app.services.router import select_best_worker

router = APIRouter(prefix="/v1", tags=["OpenAI Compatible"])

@router.get("/models")
def list_openai_models(db: Session = Depends(get_db)):
    """OpenAI standard /v1/models listing."""
    models = (
        db.query(NodeModel.model_name)
        .join(Node, Node.id == NodeModel.node_id)
        .filter(Node.status == "online", NodeModel.is_active == True)
        .distinct()
        .all()
    )
    model_names = [m[0] for m in models]
    
    if not model_names:
        model_names = ["llama3:8b", "mistral:7b", "qwen2.5:7b"]

    return {
        "object": "list",
        "data": [
            {
                "id": m,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "nexuscompute",
                "permission": [],
                "root": m,
                "parent": None
            }
            for m in model_names
        ]
    }

@router.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    consumer: User = Depends(get_authenticated_consumer),
    db: Session = Depends(get_db)
):
    """OpenAI-compatible inference endpoint supporting streaming and non-streaming."""
    model_name = request.model
    prompt_tokens = count_messages_tokens(request.messages)
    
    # Pre-authorize escrow hold (0.05 credits)
    escrow_amount = 0.05
    hold_escrow(db, consumer.id, escrow_amount)

    # Smart Routing
    worker_choice = select_best_worker(db, model_name)
    if not worker_choice:
        release_escrow(db, consumer.id, escrow_amount)
        raise HTTPException(
            status_code=503,
            detail=f"No online GPU providers currently available for model '{model_name}'. Check the Marketplace catalog for active models."
        )

    node_id, p_price, c_price = worker_choice
    job_id = f"job-{uuid.uuid4().hex[:16]}"
    start_time = time.time()

    worker_payload = {
        "type": "job_request",
        "job_id": job_id,
        "model": model_name,
        "messages": [m.model_dump() for m in request.messages],
        "temperature": request.temperature or 0.7,
        "max_tokens": request.max_tokens or 1024,
        "stream": True
    }

    manager.node_concurrency[node_id] = manager.node_concurrency.get(node_id, 0) + 1
    stream_queue = manager.create_job_stream(job_id)

    sent = await manager.send_to_node(node_id, worker_payload)
    if not sent:
        manager.remove_job_stream(job_id)
        release_escrow(db, consumer.id, escrow_amount)
        raise HTTPException(status_code=502, detail="Failed to dispatch job to provider node.")

    if request.stream:
        async def event_generator() -> AsyncGenerator[str, None]:
            completion_tokens = 0
            full_response_text = ""
            created_ts = int(time.time())

            try:
                while True:
                    try:
                        msg = await asyncio.wait_for(stream_queue.get(), timeout=30.0)
                    except asyncio.TimeoutError:
                        yield f"data: {json.dumps({'error': 'Provider response timed out'})}\n\n"
                        break

                    msg_type = msg.get("type")

                    if msg_type == "job_chunk":
                        delta = msg.get("delta", "")
                        full_response_text += delta
                        completion_tokens += 1

                        chunk_obj = ChatCompletionChunk(
                            id=job_id,
                            created=created_ts,
                            model=model_name,
                            choices=[
                                ChatCompletionChunkChoice(
                                    index=0,
                                    delta=ChatCompletionChunkDelta(content=delta),
                                    finish_reason=None
                                )
                            ]
                        )
                        yield f"data: {chunk_obj.model_dump_json()}\n\n"

                    elif msg_type == "job_done":
                        c_tokens = msg.get("completion_tokens", completion_tokens)
                        finish_reason = msg.get("finish_reason", "stop")
                        
                        final_chunk = ChatCompletionChunk(
                            id=job_id,
                            created=created_ts,
                            model=model_name,
                            choices=[
                                ChatCompletionChunkChoice(
                                    index=0,
                                    delta=ChatCompletionChunkDelta(content=""),
                                    finish_reason=finish_reason
                                )
                            ]
                        )
                        yield f"data: {final_chunk.model_dump_json()}\n\n"
                        yield "data: [DONE]\n\n"

                        # Settle Billing and log Job in independent DB session
                        latency = int((time.time() - start_time) * 1000)
                        with SessionLocal() as session:
                            total_cost, prov_cut, plat_cut = settle_job_billing(
                                session,
                                consumer_id=consumer.id,
                                node_id=node_id,
                                prompt_tokens=prompt_tokens,
                                completion_tokens=c_tokens,
                                price_per_million_prompt=p_price,
                                price_per_million_completion=c_price,
                                job_id=job_id,
                                escrow_held=escrow_amount
                            )
                            job_rec = InferenceJob(
                                id=job_id,
                                consumer_id=consumer.id,
                                node_id=node_id,
                                model_name=model_name,
                                prompt_tokens=prompt_tokens,
                                completion_tokens=c_tokens,
                                total_cost=total_cost,
                                provider_cut=prov_cut,
                                platform_cut=plat_cut,
                                latency_ms=latency,
                                status="completed",
                                completed_at=datetime.now(timezone.utc)
                            )
                            session.add(job_rec)
                            session.commit()
                        break

                    elif msg_type == "job_error":
                        err = msg.get("error", "Unknown worker error")
                        yield f"data: {json.dumps({'error': err})}\n\n"
                        with SessionLocal() as session:
                            release_escrow(session, consumer.id, escrow_amount)
                        break

            finally:
                manager.remove_job_stream(job_id)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )

    else:
        full_text = ""
        completion_tokens = 0
        try:
            while True:
                msg = await asyncio.wait_for(stream_queue.get(), timeout=35.0)
                msg_type = msg.get("type")

                if msg_type == "job_chunk":
                    full_text += msg.get("delta", "")
                    completion_tokens += 1
                elif msg_type == "job_done":
                    c_tokens = msg.get("completion_tokens", completion_tokens)
                    latency = int((time.time() - start_time) * 1000)
                    
                    total_cost, prov_cut, plat_cut = settle_job_billing(
                        db,
                        consumer_id=consumer.id,
                        node_id=node_id,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=c_tokens,
                        price_per_million_prompt=p_price,
                        price_per_million_completion=c_price,
                        job_id=job_id,
                        escrow_held=escrow_amount
                    )
                    
                    job_rec = InferenceJob(
                        id=job_id,
                        consumer_id=consumer.id,
                        node_id=node_id,
                        model_name=model_name,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=c_tokens,
                        total_cost=total_cost,
                        provider_cut=prov_cut,
                        platform_cut=plat_cut,
                        latency_ms=latency,
                        status="completed",
                        completed_at=datetime.now(timezone.utc)
                    )
                    db.add(job_rec)
                    db.commit()

                    return ChatCompletionResponse(
                        id=job_id,
                        created=int(time.time()),
                        model=model_name,
                        choices=[
                            ChatCompletionResponseChoice(
                                index=0,
                                message=ChatCompletionResponseChoiceMsg(
                                    role="assistant",
                                    content=full_text
                                ),
                                finish_reason="stop"
                            )
                        ],
                        usage=UsageInfo(
                            prompt_tokens=prompt_tokens,
                            completion_tokens=c_tokens,
                            total_tokens=prompt_tokens + c_tokens,
                            cost_credits=total_cost
                        )
                    )
                elif msg_type == "job_error":
                    release_escrow(db, consumer.id, escrow_amount)
                    raise HTTPException(status_code=500, detail=msg.get("error", "Worker execution error"))
        finally:
            manager.remove_job_stream(job_id)
