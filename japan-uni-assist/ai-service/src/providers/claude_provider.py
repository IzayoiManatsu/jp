import httpx
from typing import AsyncIterator, Union
from src.providers.base import AIProvider
from src.models.schemas import ChatRequest, ChatResponse, ChatChunk, EmbeddingRequest, EmbeddingResponse

class ClaudeProvider(AIProvider):
    name = "claude"
    supports_embedding = False

    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com"):
        super().__init__(api_key, base_url)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )

    async def chat_completion(self, request: ChatRequest) -> Union[ChatResponse, AsyncIterator[ChatChunk]]:
        self._pre_request_delay()
        system_msg = ""
        messages = []
        for m in request.messages:
            if m.role == "system":
                system_msg = m.content
            else:
                messages.append({"role": m.role, "content": m.content})

        payload = {
            "model": request.model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens or 4096,
            "stream": request.stream,
        }
        if system_msg:
            payload["system"] = system_msg

        if request.stream:
            return self._stream_chat(payload)

        resp = await self.client.post("/v1/messages", json=payload)
        resp.raise_for_status()
        data = resp.json()

        content = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
        usage = data.get("usage", {})
        self._record_usage(usage.get("input_tokens", 0), usage.get("output_tokens", 0), request.model)

        return ChatResponse(content=content, model=request.model, usage=self.token_usage)

    async def _stream_chat(self, payload: dict) -> AsyncIterator[ChatChunk]:
        async with self.client.stream("POST", "/v1/messages", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    import json
                    data = json.loads(data_str)
                    evt_type = data.get("type")
                    if evt_type == "content_block_delta":
                        text = data.get("delta", {}).get("text", "")
                        yield ChatChunk(content=text)
                    elif evt_type == "message_stop":
                        yield ChatChunk(content="", finish_reason="stop")

    async def embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        raise NotImplementedError("Claude does not support embeddings via this interface")

    async def health_check(self) -> bool:
        try:
            resp = await self.client.get("/v1/models")
            return resp.status_code == 200
        except Exception:
            return False