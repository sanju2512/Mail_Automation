from typing import List, Dict, Any, Optional
from app.services.rag_service import rag_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

class RAGAgent:
    """Agent responsible for formulating queries, performing similarity search, and aggregating knowledge."""

    def retrieve_context(
        self,
        document_text: str,
        document_type: str,
        top_k: int = 4
    ) -> Dict[str, Any]:
        logger.info(f"RAGAgent: Retrieving relevant context for document type '{document_type}'...")

        # Formulate query from document summary or top lines
        lines = [l.strip() for l in document_text.splitlines() if l.strip()]
        sample_query = " ".join(lines[:6]) if lines else document_type

        # Query ChromaDB
        search_results = rag_service.search(query=sample_query, top_k=top_k)

        # Format context for LLM
        context_blocks = []
        sources = []

        for res in search_results:
            text = res.get("text", "")
            src = res.get("source", "knowledge_base")
            score = res.get("score", 0.0)
            context_blocks.append(f"Source: {src} (Relevance: {score})\n{text}")
            sources.append({
                "source": src,
                "score": score,
                "page": res.get("page", 1)
            })

        combined_context = "\n\n".join(context_blocks) if context_blocks else ""

        return {
            "context_text": combined_context,
            "sources": sources,
            "total_chunks_retrieved": len(search_results)
        }

rag_agent = RAGAgent()
