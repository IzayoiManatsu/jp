import os
import json
import math
import aiosqlite
from typing import List, Optional
from src.rag.embedding import EmbeddingService


def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class RAGRetriever:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        db_url = os.getenv("DATABASE_URL", "file:./dev.db")
        # Convert Prisma-style SQLite URL to path
        if db_url.startswith("file:"):
            # file:./dev.db -> relative path from backend/prisma or cwd
            self.db_path = db_url.replace("file:", "").lstrip("./")
        else:
            self.db_path = "dev.db"

    async def _get_db(self):
        db_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend", "prisma", self.db_path)
        if not os.path.exists(db_path):
            db_path = self.db_path
        conn = await aiosqlite.connect(db_path)
        conn.row_factory = aiosqlite.Row
        return conn

    async def retrieve(self, query: str, top_k: int = 5, similarity_threshold: float = 0.7) -> List[dict]:
        query_embedding = await self.embedding_service.embed_query(query)
        db = await self._get_db()
        try:
            cursor = await db.execute(
                """
                SELECT dc.id, dc.content, dc.document_id, dc.embedding,
                       d.title, d.source_url, d.source_type
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                """
            )
            rows = await cursor.fetchall()

            results = []
            for row in rows:
                emb_str = row["embedding"]
                if not emb_str:
                    continue
                try:
                    emb = json.loads(emb_str)
                except (json.JSONDecodeError, TypeError):
                    continue
                sim = cosine_similarity(query_embedding, emb)
                if sim >= similarity_threshold:
                    results.append({
                        "id": row["id"],
                        "content": row["content"],
                        "document_id": row["document_id"],
                        "title": row["title"],
                        "source_url": row["source_url"],
                        "source_type": row["source_type"],
                        "similarity": sim,
                    })

            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]
        finally:
            await db.close()

    async def add_document(self, title: str, source_type: str, content: str,
                           source_url: str = None, metadata: dict = None):
        chunks = self._split_text(content)
        embeddings = await self.embedding_service.embed_texts(chunks)

        db = await self._get_db()
        try:
            cursor = await db.execute(
                "INSERT INTO documents (id, title, source_type, source_url, content, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (self._uuid(), title, source_type, source_url, content,
                 json.dumps(metadata) if metadata else None)
            )
            doc_id = cursor.lastrowid
            for chunk, emb in zip(chunks, embeddings):
                await db.execute(
                    "INSERT INTO document_chunks (id, document_id, content, embedding) VALUES (?, ?, ?, ?)",
                    (self._uuid(), doc_id, chunk, json.dumps(emb))
                )
            await db.commit()
            return doc_id
        finally:
            await db.close()

    def _uuid(self) -> str:
        import uuid
        return str(uuid.uuid4())

    def _split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks
