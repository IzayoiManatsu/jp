import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from typing import Optional
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.providers.manager import ProviderManager
from src.rag.embedding import EmbeddingService
from src.rag.retriever import RAGRetriever
from src.rag.chain import RAGChain
from src.recommend.recommender import Recommender
from src.utils.rate_limit import RateLimiter
from src.utils.logger import get_logger
from src.models.schemas import (
    ChatRequest, ChatResponse, ChatChunk, EmbeddingRequest, EmbeddingResponse,
    StudentProfileInput, RecommendResponse,
    RAGQueryRequest, RAGQueryResponse,
    HealthResponse, ModelInfo
)

logger = get_logger("main")
provider_manager = ProviderManager()
embedding_service = EmbeddingService(provider_manager)
rag_retriever = RAGRetriever(embedding_service)
rag_chain = RAGChain(provider_manager, rag_retriever)
recommender = Recommender(provider_manager)
rate_limiter = RateLimiter()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        logger.info(
            f"{request.method} {request.url.path}",
            extra={"status": response.status_code, "client": request.client.host if request.client else None}
        )
        return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI Service starting up")
    yield
    await rate_limiter.close()
    logger.info("AI Service shutting down")

app = FastAPI(
    title="AI日本考学推荐系统 - AI Service",
    description="FastAPI AI服务，提供统一模型调用、RAG检索、择校推荐",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def check_rate_limit(request: Request, limit: int = 60, window: int = 60):
    client = request.client.host if request.client else "unknown"
    allowed = await rate_limiter.is_allowed(f"ratelimit:{client}", limit, window)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

@app.get("/health", response_model=HealthResponse)
async def health():
    providers = await provider_manager.health()
    return HealthResponse(
        status="healthy" if any(providers.values()) else "degraded",
        providers=providers
    )

@app.get("/models", response_model=list[ModelInfo])
async def list_models():
    return provider_manager.list_models()

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request):
    await check_rate_limit(req)
    try:
        return await provider_manager.chat(request)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest, req: Request):
    await check_rate_limit(req)
    async def event_generator():
        try:
            async for chunk in provider_manager.chat_stream(request):
                data = json.dumps({"content": chunk.content, "finish_reason": chunk.finish_reason})
                yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/embeddings", response_model=EmbeddingResponse)
async def embeddings(request: EmbeddingRequest, req: Request):
    await check_rate_limit(req, limit=30, window=60)
    try:
        return await provider_manager.embed(request)
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend", response_model=RecommendResponse)
async def recommend(profile: StudentProfileInput, req: Request):
    await check_rate_limit(req, limit=10, window=60)
    try:
        return await recommender.recommend(profile)
    except Exception as e:
        logger.error(f"Recommend error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest, req: Request):
    await check_rate_limit(req)
    try:
        return await rag_chain.query(request.query, request.top_k, request.model)
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/query/stream")
async def rag_query_stream(request: RAGQueryRequest, req: Request):
    await check_rate_limit(req)
    async def event_generator():
        try:
            async for chunk in rag_chain.query_stream(request.query, request.top_k, request.model):
                data = json.dumps({"content": chunk.content, "finish_reason": chunk.finish_reason})
                yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

class AddDocumentBody(BaseModel):
    title: str
    content: str
    source_type: str = "FAQ"
    source_url: Optional[str] = None

@app.post("/rag/documents")
async def add_document(body: AddDocumentBody, req: Request):
    await check_rate_limit(req, limit=10, window=60)
    try:
        doc_id = await rag_retriever.add_document(body.title, body.source_type, body.content, body.source_url)
        return {"document_id": doc_id}
    except Exception as e:
        logger.error(f"Add document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)