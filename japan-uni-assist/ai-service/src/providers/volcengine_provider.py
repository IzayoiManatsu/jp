import httpx
from typing import AsyncIterator, Union
from src.providers.base import AIProvider
from src.models.schemas import ChatRequest, ChatResponse, ChatChunk, EmbeddingRequest, EmbeddingResponse

class VolcengineProvider(AIProvider):
    name = "volcengine"
    supports_embedding = False

    def __init__(self, api_key: str, base_url: str = "https://ark.cn-beijing.volces.com/api/v3"):
        super().__init__(api_key, base_url)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            timeout=60.0
        )

    async def chat_completion(self, request: ChatRequest) -> Union[ChatResponse, AsyncIterator[ChatChunk]]:
        self._pre_request_delay()
        payload = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "stream": request.stream,
        }
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        if request.stream:
            return self._stream_chat(payload)

        resp = await self.client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]
        content = choice["message"]["content"]
        usage = data.get("usage", {})
        self._record_usage(usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), request.model)

        return ChatResponse(content=content, model=request.model, usage=self.token_usage)

    async def _stream_chat(self, payload: dict) -> AsyncIterator[ChatChunk]:
        async with self.client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    import json
                    data = json.loads(data_str)
                    delta = data["choices"][0].get("delta", {})
                    finish = data["choices"][0].get("finish_reason")
                    if delta.get("content") or finish:
                        yield ChatChunk(content=delta.get("content", ""), finish_reason=finish)

    async def embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        raise NotImplementedError("Volcengine embedding not supported in this version")

    async def health_check(self) -> bool:
        try:
            resp = await self.client.get("/models")
            return resp.status_code == 200
        except Exception:
            return False