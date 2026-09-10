from app.services.rag_service import rag_service
from app.agents.rag_agent import rag_agent

def test_rag_chunking():
    sample_text = "Paragraph one with some text content.\n\nParagraph two with additional policy rules.\n\nParagraph three."
    chunks = rag_service.chunk_text(sample_text, chunk_size=20, overlap=5)
    assert len(chunks) >= 1

def test_rag_agent_empty_context():
    res = rag_agent.retrieve_context(document_text="", document_type="unknown")
    assert "context_text" in res
    assert "sources" in res
