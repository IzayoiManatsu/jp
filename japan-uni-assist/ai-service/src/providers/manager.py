import os
from dotenv import load_dotenv
from typing import Optional, Dict, List

load_dotenv()
from src.providers.base import AIProvider
from src.providers.openai_provider import OpenAIProvider
from src.providers.claude_provider import ClaudeProvider
from src.providers.deepseek_provider import DeepSeekProvider
from src.providers.gemini_provider import GeminiProvider
from src.providers.volcengine_provider import VolcengineProvider
from src.models.schemas import ChatRequest, ChatResponse, ChatChunk, EmbeddingRequest, EmbeddingResponse, ModelInfo

FALLBACK_CHAIN: Dict[str, List[str]] = {
    "gpt-4o": ["claude-sonnet-4", "deepseek-chat", "gemini-1.5-pro"],
    "gpt-4o-mini": ["gemini-1.5-flash", "deepseek-chat"],
    "claude-opus-4": ["gpt-4o", "deepseek-chat"],
    "claude-sonnet-4": ["gpt-4o", "deepseek-chat", "gemini-1.5-pro"],
    "deepseek-reasoner": ["deepseek-chat", "gpt-4o", "claude-sonnet-4"],
    "deepseek-chat": ["gpt-4o-mini", "gemini-1.5-flash"],
    "gemini-1.5-pro": ["gpt-4o", "claude-sonnet-4"],
    "gemini-1.5-flash": ["deepseek-chat", "gpt-4o-mini"],
}

class ProviderManager:
    def __init__(self):
        self._providers: Dict[str, AIProvider] = {}
        self._register_providers()

    def _register_providers(self):
        if os.getenv("OPENAI_API_KEY"):
            self._providers["openai"] = OpenAIProvider(os.getenv("OPENAI_API_KEY"))
        if os.getenv("ANTHROPIC_API_KEY"):
            self._providers["claude"] = ClaudeProvider(os.getenv("ANTHROPIC_API_KEY"))
        if os.getenv("DEEPSEEK_API_KEY"):
            self._providers["deepseek"] = DeepSeekProvider(os.getenv("DEEPSEEK_API_KEY"))
        if os.getenv("GEMINI_API_KEY"):
            self._providers["gemini"] = GeminiProvider(os.getenv("GEMINI_API_KEY"))
        if os.getenv("VOLCENGINE_API_KEY"):
            self._providers["volcengine"] = VolcengineProvider(os.getenv("VOLCENGINE_API_KEY"))

    def _resolve_provider(self, model: str) -> Optional[AIProvider]:
        mapping = {
            "gpt-4o": "openai", "gpt-4o-mini": "openai", "gpt-4-turbo": "openai",
            "claude-opus-4": "claude", "claude-sonnet-4": "claude", "claude-haiku-4": "claude",
            "deepseek-chat": "deepseek", "deepseek-reasoner": "deepseek",
            "gemini-1.5-pro": "gemini", "gemini-1.5-flash": "gemini",
        }
        provider_key = mapping.get(model)
        return self._providers.get(provider_key) if provider_key else None

    async def chat(self, request: ChatRequest, fallback: bool = True) -> ChatResponse:
        provider = self._resolve_provider(request.model)
        if not provider and fallback:
            for p in self._providers.values():
                provider = p
                break
        if not provider:
            raise ValueError(f"No provider available for model {request.model}")

        tried = set()
        models_to_try = [request.model] + FALLBACK_CHAIN.get(request.model, [])

        for model in models_to_try:
            if model in tried:
                continue
            tried.add(model)
            p = self._resolve_provider(model) or provider
            try:
                req_copy = request.model_copy(update={"model": model})
                result = await p.chat_completion(req_copy)
                if isinstance(result, ChatResponse):
                    return result
                content_parts = []
                async for chunk in result:
                    content_parts.append(chunk.content)
                    if chunk.finish_reason:
                        break
                return ChatResponse(content="".join(content_parts), model=model, usage=p.token_usage)
            except Exception as e:
                continue

        raise RuntimeError("All providers failed for chat completion")

    async def chat_stream(self, request: ChatRequest):
        provider = self._resolve_provider(request.model)
        if not provider:
            for p in self._providers.values():
                provider = p
                break
        if not provider:
            raise ValueError("No provider available")

        result = await provider.chat_completion(request)
        async for chunk in result:
            yield chunk

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        for name, provider in self._providers.items():
            if provider.supports_embedding:
                try:
                    return await provider.embedding(request)
                except Exception:
                    continue
        raise RuntimeError("No embedding provider available")

    async def health(self) -> Dict[str, bool]:
        health = {}
        for name, provider in self._providers.items():
            health[name] = await provider.health_check()
        return health

    def list_models(self) -> List[ModelInfo]:
        models = []
        registry = [
            ("gpt-4o", "OpenAI GPT-4o", "openai", True, False),
            ("gpt-4o-mini", "OpenAI GPT-4o Mini", "openai", True, False),
            ("claude-opus-4", "Claude Opus 4", "claude", True, False),
            ("claude-sonnet-4", "Claude Sonnet 4", "claude", True, False),
            ("deepseek-chat", "DeepSeek Chat", "deepseek", True, False),
            ("deepseek-reasoner", "DeepSeek Reasoner", "deepseek", True, False),
            ("gemini-1.5-pro", "Gemini 1.5 Pro", "gemini", True, True),
            ("gemini-1.5-flash", "Gemini 1.5 Flash", "gemini", True, True),
        ]
        for m_id, m_name, m_prov, stream, emb in registry:
            if m_prov in self._providers:
                models.append(ModelInfo(
                    id=m_id, name=m_name, provider=m_prov,
                    supports_streaming=stream, supports_embedding=emb
                ))
        return models

    def get_provider(self, name: str) -> Optional[AIProvider]:
        return self._providers.get(name)