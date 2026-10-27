from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.v1.auth import router as auth_router
from app.api.v1.consumer import router as consumer_router
from app.api.v1.provider import router as provider_router
from app.api.v1.models import router as models_router
from app.api.v1.admin import router as admin_router
from app.api.ws.worker_hub import router as ws_router
from app.api.openai.completions import router as openai_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="NexusCompute: Decentralized GPU AI Inference Marketplace Coordinator API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(consumer_router, prefix=settings.API_V1_STR)
app.include_router(provider_router, prefix=settings.API_V1_STR)
app.include_router(models_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)
app.include_router(ws_router, prefix=settings.API_V1_STR)
app.include_router(openai_router)  # /v1/chat/completions and /v1/models

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }

@app.get("/")
def root():
    return {
        "message": "Welcome to NexusCompute Decentralized AI Inference Marketplace API",
        "docs_url": "/docs",
        "openai_endpoint": "/v1/chat/completions"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
