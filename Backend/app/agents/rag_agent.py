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

        # Formulate a primary query from document type and meaningful body words
        clean_lines = [l.strip() for l in (document_text or "").splitlines() if len(l.strip()) > 2]
        body_sample = " ".join(clean_lines[:15]) if clean_lines else ""
        primary_query = f"{document_type.replace('_', ' ')} {body_sample}".strip()

        if not primary_query:
            primary_query = "policy guidelines standards"

        # 1. Primary Query search
        search_results = rag_service.search(query=primary_query, top_k=top_k)

        # 2. If nothing returned or few returned, fallback with document type / general policy query
        if not search_results:
            fallback_query = document_type.replace("_", " ") if document_type and document_type != "unknown" else "policy guidelines rules"
            search_results = rag_service.search(query=fallback_query, top_k=top_k)

        # Format context for LLM with deduplication
        seen_texts = set()
        context_blocks = []
        sources = []

        for res in search_results:
            text = (res.get("text") or "").strip()
            if not text or text in seen_texts:
                continue
            seen_texts.add(text)

            src = res.get("source", "knowledge_base")
            score = res.get("score", 0.0)
            context_blocks.append(f"--- [KNOWLEDGE SOURCE: {src} | Score: {score}] ---\n{text}")
            sources.append({
                "source": src,
                "score": score,
                "page": res.get("page", 1)
            })

        combined_context = "\n\n".join(context_blocks) if context_blocks else ""

        logger.info(f"RAGAgent: Retrieved {len(sources)} unique knowledge chunks for '{document_type}'.")

        return {
            "context_text": combined_context,
            "sources": sources,
            "total_chunks_retrieved": len(sources)
        }

rag_agent = RAGAgent()
