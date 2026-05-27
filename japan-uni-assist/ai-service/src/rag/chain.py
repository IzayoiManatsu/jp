from typing import AsyncIterator
from src.providers.manager import ProviderManager
from src.rag.retriever import RAGRetriever
from src.models.schemas import ChatRequest, Message, ChatChunk, RAGQueryResponse, RAGSource, TokenUsage

RAG_SYSTEM_PROMPT = """你是日本留学专家，熟悉日本大学院入学制度。请基于以下参考资料回答用户问题。
如果参考资料不足以回答问题，请明确告知用户，不要编造信息。

【参考资料】
{context}

【回答要求】
- 使用中文回答
- 涉及截止日期、分数要求等具体信息时，必须注明信息来源
- 如果不确定，建议用户直接联系大学确认"""

class RAGChain:
    def __init__(self, provider_manager: ProviderManager, retriever: RAGRetriever):
        self.provider_manager = provider_manager
        self.retriever = retriever

    async def query(self, query: str, top_k: int = 5, model: str = "gpt-4o") -> RAGQueryResponse:
        docs = await self.retriever.retrieve(query, top_k=top_k)
        context = "\n\n---\n\n".join(
            f"[来源: {d['title']}]\n{d['content']}" for d in docs
        )

        system_msg = RAG_SYSTEM_PROMPT.format(context=context or "（无相关参考资料）")
        messages = [
            Message(role="system", content=system_msg),
            Message(role="user", content=f"用户问题：{query}\n\n请基于参考资料给出准确、有帮助的回答：")
        ]

        request = ChatRequest(messages=messages, model=model, temperature=0.5)
        response = await self.provider_manager.chat(request)

        sources = [
            RAGSource(
                title=d["title"],
                source_url=d.get("source_url"),
                content_snippet=d["content"][:200] + "...",
                similarity=d["similarity"]
            ) for d in docs
        ]

        return RAGQueryResponse(
            answer=response.content,
            sources=sources,
            model_used=response.model,
            usage=response.usage
        )

    async def query_stream(self, query: str, top_k: int = 5, model: str = "gpt-4o") -> AsyncIterator[ChatChunk]:
        docs = await self.retriever.retrieve(query, top_k=top_k)
        context = "\n\n---\n\n".join(
            f"[来源: {d['title']}]\n{d['content']}" for d in docs
        )

        system_msg = RAG_SYSTEM_PROMPT.format(context=context or "（无相关参考资料）")
        messages = [
            Message(role="system", content=system_msg),
            Message(role="user", content=f"用户问题：{query}\n\n请基于参考资料给出准确、有帮助的回答：")
        ]

        request = ChatRequest(messages=messages, model=model, temperature=0.5, stream=True)
        async for chunk in self.provider_manager.chat_stream(request):
            yield chunk