import os
import asyncpg
from typing import List
from src.rag.embedding import EmbeddingService

class RAGRetriever:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.db_url = os.getenv("DATABASE_URL")

    async def _get_pool(self):
        return await asyncpg.create_pool(self.db_url)

    async def retrieve(self, query: str, top_k: int = 5, similarity_threshold: float = 0.7) -> List[dict]:
        embedding = await self.embedding_service.embed_query(query)
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT
                        dc.id,
                        dc.content,
                        dc.document_id,
                        d.title,
                        d.source_url,
                        d.source_type,
                        1 - (dc.embedding <=> $1::vector) AS similarity
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE 1 - (dc.embedding <=> $1::vector) > $3
                    ORDER BY dc.embedding <=> $1::vector
                    LIMIT $2
                    """,
                    embedding,
                    top_k,
                    similarity_threshold
                )
                return [dict(r) for r in rows]
        finally:
            await pool.close()

    async def add_document(self, title: str, source_type: str, content: str, source_url: str = None, metadata: dict = None):
        chunks = self._split_text(content)
        embeddings = await self.embedding_service.embed_texts(chunks)

        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                doc_id = await conn.fetchval(
                    "INSERT INTO documents (title, source_type, source_url, content, metadata) VALUES ($1, $2, $3, $4, $5) RETURNING id",
                    title, source_type, source_url, content, metadata
                )
                for chunk, emb in zip(chunks, embeddings):
                    await conn.execute(
                        "INSERT INTO document_chunks (document_id, content, embedding) VALUES ($1, $2, $3::vector)",
                        doc_id, chunk, emb
                    )
                return doc_id
        finally:
            await pool.close()

    def _split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks