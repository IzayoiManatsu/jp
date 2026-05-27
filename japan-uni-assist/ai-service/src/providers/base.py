from abc import ABC, abstractmethod
from typing import AsyncIterator, Union, List
import time
from src.models.schemas import ChatRequest, ChatResponse, ChatChunk, EmbeddingRequest, EmbeddingResponse, TokenUsage

class AIProvider(ABC):
    name: str = "base"
    supports_streaming: bool = True
    supports_embedding: bool = False

    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url
        self._last_request_time = 0.0
        self._token_usage = {"prompt": 0, "completion": 0, "total": 0, "cost": 0.0}

    @abstractmethod
    async def chat_completion(self, request: ChatRequest) -> Union[ChatResponse, AsyncIterator[ChatChunk]]:
        pass

    @abstractmethod
    async def embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    @property
    def token_usage(self) -> TokenUsage:
        return TokenUsage(
            prompt_tokens=self._token_usage["prompt"],
            completion_tokens=self._token_usage["completion"],
            total_tokens=self._token_usage["total"],
            cost_usd=self._token_usage["cost"]
        )

    def _record_usage(self, prompt: int, completion: int, model: str):
        cost = self._estimate_cost(prompt, completion, model)
        self._token_usage["prompt"] += prompt
        self._token_usage["completion"] += completion
        self._token_usage["total"] += prompt + completion
        self._token_usage["cost"] += cost

    def _estimate_cost(self, prompt: int, completion: int, model: str) -> float:
        rates = {
            "gpt-4o": (5.0, 15.0),
            "gpt-4o-mini": (0.15, 0.6),
            "claude-opus-4": (15.0, 75.0),
            "claude-sonnet-4": (3.0, 15.0),
            "deepseek-chat": (0.14, 0.28),
            "deepseek-reasoner": (0.55, 2.19),
            "gemini-1.5-pro": (3.5, 10.5),
            "gemini-1.5-flash": (0.35, 1.05),
        }
        p_rate, c_rate = rates.get(model, (5.0, 15.0))
        return (prompt * p_rate + completion * c_rate) / 1_000_000

    def _pre_request_delay(self, min_interval: float = 0.05):
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_time = time.time()