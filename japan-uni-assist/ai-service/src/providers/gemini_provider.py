import httpx
from typing import AsyncIterator, Union
from src.providers.base import AIProvider
from src.models.schemas import ChatRequest, ChatResponse, ChatChunk, EmbeddingRequest, EmbeddingResponse

class GeminiProvider(AIProvider):
    name = "gemini"
    supports_embedding = True

    def __init__(self, api_key: str, base_url: str = "https://generativelanguage.googleapis.com"):
        super().__init__(api_key, base_url)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=60.0
        )

    async def chat_completion(self, request: ChatRequest) -> Union[ChatResponse, AsyncIterator[ChatChunk]]:
        self._pre_request_delay()
        system_msg = ""
        contents = []
        for m in request.messages:
            if m.role == "system":
                system_msg = m.content
            else:
                role = "user" if m.role == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m.content}]})

        payload = {"contents": contents}
        if system_msg:
            payload["systemInstruction"] = {"parts": [{"text": system_msg}]}
        payload["generationConfig"] = {"temperature": request.temperature}
        if request.max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = request.max_tokens

        model_name = request.model if request.model.startswith("gemini") else "gemini-1.5-pro"
        url = f"/v1beta/models/{model_name}:generateContent?key={self.api_key}"

        if request.stream:
            return self._stream_chat(payload, model_name)

        resp = await self.client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

        candidates = data.get("candidates", [])
        content = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            content = "".join(p.get("text", "") for p in parts)

        usage_data = data.get("usageMetadata", {})
        prompt_tokens = usage_data.get("promptTokenCount", 0)
        completion_tokens = usage_data.get("candidatesTokenCount", 0)
        self._record_usage(prompt_tokens, completion_tokens, model_name)

        return ChatResponse(content=content, model=model_name, usage=self.token_usage)

    async def _stream_chat(self, payload: dict, model_name: str) -> AsyncIterator[ChatChunk]:
        url = f"/v1beta/models/{model_name}:streamGenerateContent?alt=sse&key={self.api_key}"
        async with self.client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    import json
                    data = json.loads(data_str)
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        text = "".join(p.get("text", "") for p in parts)
                        finish = candidates[0].get("finishReason")
                        yield ChatChunk(content=text, finish_reason=finish)

    async def embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        self._pre_request_delay()
        model_name = request.model if request.model.startswith("embed") else "text-embedding-004"
        embeddings = []
        total_tokens = 0
        for text in request.texts:
            url = f"/v1beta/models/{model_name}:embedContent?key={self.api_key}"
            resp = await self.client.post(url, json={"content": {"parts": [{"text": text}]}})
            resp.raise_for_status()
            data = resp.json()
            embeddings.append(data["embedding"]["values"])
            total_tokens += len(text) // 4
        self._record_usage(total_tokens, 0, model_name)
        return EmbeddingResponse(embeddings=embeddings, model=model_name, usage=self.token_usage)

    async def health_check(self) -> bool:
        try:
            url = f"/v1beta/models?key={self.api_key}"
            resp = await self.client.get(url)
            return resp.status_code == 200
        except Exception:
            return False