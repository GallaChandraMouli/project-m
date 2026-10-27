import pytest
from nexus_worker.hardware import detect_hardware
from nexus_worker.engine import InferenceEngineClient

def test_hardware_detection():
    hw = detect_hardware()
    assert "gpu_name" in hw
    assert "vram_mb" in hw
    assert hw["vram_mb"] > 0
    assert "platform" in hw

def test_engine_discovery_emulated():
    engine = InferenceEngineClient(emulate=True)
    models = engine.discover_models()
    assert len(models) >= 3
    assert "llama3:8b" in models

@pytest.mark.asyncio
async def test_engine_stream_chat_emulated():
    engine = InferenceEngineClient(emulate=True)
    engine.discover_models()

    chunks = []
    done_msg = None
    async for item in engine.stream_chat(
        model="llama3:8b",
        messages=[{"role": "user", "content": "What is AI?"}],
        max_tokens=20
    ):
        if item["type"] == "chunk":
            chunks.append(item["delta"])
        elif item["type"] == "done":
            done_msg = item

    assert len(chunks) > 0
    full_text = "".join(chunks)
    assert len(full_text) > 10
    assert done_msg is not None
    assert done_msg["finish_reason"] == "stop"
    assert done_msg["completion_tokens"] > 0

@pytest.mark.asyncio
async def test_engine_benchmark():
    engine = InferenceEngineClient(emulate=True)
    speed = await engine.run_benchmark()
    assert isinstance(speed, float)
    assert speed >= 10.0
