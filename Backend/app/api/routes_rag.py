import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Form
from app.config.settings import settings
from app.services.rag_service import rag_service
from app.models.schemas import RAGIngestResponse, RAGSearchResponse, RAGSearchResult
from app.utils.file_utils import sanitize_filename
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/rag", tags=["RAG & Knowledge Base"])

@router.post("/ingest", response_model=RAGIngestResponse)
async def ingest_knowledge_document(
    file: UploadFile = File(...),
    document_type: str = Form("policy")
):
    """
    Ingest a company policy, handbook, or reference PDF into ChromaDB knowledge base.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported for knowledge ingestion.")

    clean_name = sanitize_filename(file.filename)
    target_path = os.path.join(settings.KNOWLEDGE_BASE_DIR, clean_name)

    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Error saving knowledge document: {e}")
        raise HTTPException(status_code=500, detail="Failed to save knowledge file.")

    try:
        res = rag_service.ingest_pdf(target_path, document_type=document_type)
        return RAGIngestResponse(
            status=res["status"],
            chunks_indexed=res["chunks_indexed"],
            filename=clean_name
        )
    except Exception as e:
        logger.error(f"Knowledge ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest knowledge: {str(e)}")

@router.get("/search", response_model=RAGSearchResponse)
def search_knowledge_base(
    query: str = Query(..., description="Query to search knowledge base"),
    top_k: int = Query(4, ge=1, le=10),
    document_type: Optional[str] = Query(None)
):
    """Semantic search against indexed ChromaDB documents."""
    results = rag_service.search(query=query, top_k=top_k, document_type=document_type)
    
    formatted = [
        RAGSearchResult(
            text=r["text"],
            source=r["source"],
            page=r.get("page", 1),
            score=r["score"],
            metadata=r.get("metadata", {})
        )
        for r in results
    ]

    return RAGSearchResponse(
        results=formatted,
        total=len(formatted)
    )

@router.get("/documents")
def list_rag_documents():
    """List all ingested RAG PDF documents with file size and chunk count."""
    return rag_service.list_documents()

@router.get("/documents/{filename}/view")
def view_rag_document(filename: str):
    """View/Stream a knowledge base PDF document inline."""
    from fastapi.responses import FileResponse
    clean_name = sanitize_filename(filename)
    target_path = os.path.join(settings.KNOWLEDGE_BASE_DIR, clean_name)
    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail="Knowledge base document not found.")
    return FileResponse(
        path=target_path,
        filename=clean_name,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{clean_name}"'}
    )

@router.delete("/documents/{filename}")
def delete_rag_document(filename: str):
    """Delete a RAG document from disk and ChromaDB knowledge base."""
    clean_name = sanitize_filename(filename)
    success = rag_service.delete_document(clean_name)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to delete knowledge document '{clean_name}'")
    return {"status": "success", "message": f"Document '{clean_name}' deleted successfully from RAG knowledge base."}

