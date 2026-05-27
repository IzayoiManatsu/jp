from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class Message(BaseModel):
    role: MessageRole
    content: str

class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float = 0.0

class ChatRequest(BaseModel):
    messages: List[Message]
    model: str = "gpt-4o"
    temperature: float = 0.7
    stream: bool = False
    max_tokens: Optional[int] = None

class ChatResponse(BaseModel):
    content: str
    model: str
    usage: TokenUsage

class ChatChunk(BaseModel):
    content: str
    finish_reason: Optional[str] = None

class EmbeddingRequest(BaseModel):
    texts: List[str]
    model: str = "text-embedding-3-small"

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    usage: TokenUsage

class StudentProfileInput(BaseModel):
    gpa: float = Field(..., ge=0.0, le=4.0)
    english_type: Literal["TOEFL", "IELTS"]
    english_score: float
    jlpt_level: Optional[Literal["N1", "N2", "N3", "N4", "N5"]] = None
    bachelor_school: str
    bachelor_major: str
    budget_yen: Optional[int] = None
    target_major: Optional[str] = None

class RecommendCategory(str, Enum):
    REACH = "REACH"
    TARGET = "TARGET"
    SAFETY = "SAFETY"

class RecommendItem(BaseModel):
    category: RecommendCategory
    university_name: str
    university_name_jp: str
    program_name: str
    reason: str
    match_score: float
    confidence: float
    tuition_yen: Optional[int] = None
    location: Optional[str] = None

class RecommendResponse(BaseModel):
    profile_id: Optional[str] = None
    recommendations: List[RecommendItem]
    model_used: str
    usage: TokenUsage

class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5
    model: str = "gpt-4o"

class RAGSource(BaseModel):
    title: str
    source_url: Optional[str] = None
    content_snippet: str
    similarity: float

class RAGQueryResponse(BaseModel):
    answer: str
    sources: List[RAGSource]
    model_used: str
    usage: TokenUsage

class HealthResponse(BaseModel):
    status: str
    providers: Dict[str, bool]
    version: str = "1.0.0"

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    supports_streaming: bool
    supports_embedding: bool