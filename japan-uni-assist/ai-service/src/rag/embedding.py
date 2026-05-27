from typing import List
from src.providers.manager import ProviderManager
from src.models.schemas import EmbeddingRequest

class EmbeddingService:
    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager

    async def embed_texts(self, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
        request = EmbeddingRequest(texts=texts, model=model)
        response = await self.provider_manager.embed(request)
        return response.embeddings

    async def embed_query(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        result = await self.embed_texts([text], model)
        return result[0]