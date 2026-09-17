import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.database import get_db
from app.models.document import Document
from app.models.schemas import (
    DocumentUploadResponse,
    DocumentExtractionResponse,
    ExtractedFieldMeta,
    ProcessDocumentResponse,
    DocumentGenerateResponse,
    EmailSendRequest,
    EmailSendResponse,
)
from app.services.pdf_service import PDFService, PDFExtractionError
from app.services.email_service import email_service
from app.agents.document_agent import document_agent
from app.agents.rag_agent import rag_agent
from app.agents.extraction_agent import extraction_agent
from app.agents.orchestrator import orchestrator
from app.utils.file_utils import sanitize_filename, generate_document_id, is_safe_path, get_file_size_mb
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])

MAX_FILE_SIZE_MB = 20.0

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF document.
    Validates file type, size, stores in data/input/, and extracts initial text.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents (.pdf) are supported."
        )

    clean_name = sanitize_filename(file.filename)
    document_id = generate_document_id("DOC")
    stored_filename = f"{document_id}_{clean_name}"
    target_path = os.path.join(settings.INPUT_DIR, stored_filename)

    # Save uploaded file
    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.")

    file_size_mb = get_file_size_mb(target_path)
    if file_size_mb > MAX_FILE_SIZE_MB:
        os.remove(target_path)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size_mb:.2f}MB) exceeds maximum limit of {MAX_FILE_SIZE_MB}MB."
        )

    # Extract text using PyMuPDF
    try:
        extraction_res = PDFService.extract_text(target_path)
    except PDFExtractionError as e:
        # Keep document record with failed extraction status
        new_doc = Document(
            id=document_id,
            filename=clean_name,
            original_filepath=target_path,
            file_size_bytes=os.path.getsize(target_path),
            page_count=0,
            status="EXTRACTION_FAILED",
            error_message=str(e)
        )
        db.add(new_doc)
        db.commit()
        raise HTTPException(status_code=400, detail=str(e))

    # Persist in Database
    new_doc = Document(
        id=document_id,
        filename=clean_name,
        original_filepath=target_path,
        file_size_bytes=os.path.getsize(target_path),
        page_count=extraction_res.get("page_count", 1),
        extracted_text=extraction_res.get("full_text", ""),
        status="TEXT_EXTRACTED"
    )
    db.add(new_doc)
    db.commit()

    return DocumentUploadResponse(
        document_id=document_id,
        filename=clean_name,
        pages=extraction_res.get("page_count", 1),
        text=extraction_res.get("full_text", "")[:1000],  # Return preview
        status="text_extracted",
        file_size_mb=round(file_size_mb, 2)
    )

@router.get("/")
def list_documents(db: Session = Depends(get_db)):
    """List all tracked documents and their processing status."""
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "document_type": d.document_type,
            "status": d.status,
            "validation_status": d.validation_status,
            "confidence_score": d.confidence_score,
            "output_filename": d.output_filename,
            "created_at": d.created_at.isoformat() if d.created_at else None
        }
        for d in docs
    ]

@router.get("/{document_id}")
def get_document_details(document_id: str, db: Session = Depends(get_db)):
    """Get full details and metadata for a specific document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")

    return {
        "id": doc.id,
        "filename": doc.filename,
        "document_type": doc.document_type,
        "page_count": doc.page_count,
        "extracted_text": doc.extracted_text,
        "extracted_data": doc.extracted_data,
        "retrieved_sources": doc.retrieved_sources,
        "confidence_score": doc.confidence_score,
        "validation_status": doc.validation_status,
        "validation_errors": doc.validation_errors,
        "validation_warnings": doc.validation_warnings,
        "suggested_actions": doc.suggested_actions,
        "output_filename": doc.output_filename,
        "email_status": doc.email_status,
        "status": doc.status,
        "error_message": doc.error_message,
        "created_at": doc.created_at.isoformat() if doc.created_at else None
    }

@router.post("/{document_id}/extract", response_model=DocumentExtractionResponse)
def extract_document(document_id: str, db: Session = Depends(get_db)):
    """Trigger Document Understanding + RAG Retrieval + Qwen Extraction for a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")

    understanding = document_agent.understand(doc.extracted_text or "")
    doc.document_type = understanding.get("document_type", "general_document")

    # Retrieve relevant RAG context
    rag_res = rag_agent.retrieve_context(
        document_text=doc.extracted_text or "",
        document_type=doc.document_type
    )
    doc.retrieved_sources = rag_res.get("sources", [])

    extraction = extraction_agent.extract(
        document_text=doc.extracted_text or "",
        document_type=doc.document_type,
        required_fields=understanding.get("required_fields", []),
        retrieved_knowledge=rag_res.get("context_text")
    )

    doc.extracted_data = extraction.get("fields", {})
    doc.confidence_score = extraction.get("confidence", 0.9)
    doc.status = "EXTRACTED"
    db.commit()

    return DocumentExtractionResponse(
        document_id=doc.id,
        document_type=doc.document_type,
        fields=doc.extracted_data,
        metadata=ExtractedFieldMeta(
            confidence=doc.confidence_score,
            missing_fields=extraction.get("missing_fields", []),
            ambiguous_fields=extraction.get("ambiguous_fields", []),
            source_pages={}
        ),
        status="extracted"
    )

@router.post("/{document_id}/process", response_model=ProcessDocumentResponse)
def process_document_pipeline(document_id: str, db: Session = Depends(get_db)):
    """Execute complete multi-agent orchestration for a document."""
    result = orchestrator.process_document(document_id=document_id, db=db)
    return ProcessDocumentResponse(**result)

@router.get("/{document_id}/download")
def download_generated_document(document_id: str, db: Session = Depends(get_db)):
    """Download the completed output document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or not doc.output_filepath:
        raise HTTPException(status_code=404, detail="Generated document output not found.")

    if not os.path.exists(doc.output_filepath) or not is_safe_path(settings.OUTPUT_DIR, doc.output_filepath):
        raise HTTPException(status_code=404, detail="Output file is missing or invalid.")

    return FileResponse(
        path=doc.output_filepath,
        filename=doc.output_filename or f"completed_{document_id}.pdf",
        media_type="application/pdf"
    )

@router.post("/{document_id}/send", response_model=EmailSendResponse)
def send_document_via_email(
    document_id: str,
    payload: EmailSendRequest,
    db: Session = Depends(get_db)
):
    """Send generated document to recipient email."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")

    if doc.status != "COMPLETED" or not doc.output_filepath or not os.path.exists(doc.output_filepath):
        raise HTTPException(
            status_code=400,
            detail="Cannot send document: Generation is not completed or output file is missing."
        )

    subject = payload.subject or f"Completed Document - {doc.id} ({doc.document_type})"
    body = payload.body or f"Hello,\n\nPlease find attached the verified and completed document for ID {doc.id}.\n\nAgentic Document Automation System"

    sent = email_service.send_document_email(
        recipient_email=payload.recipient_email,
        subject=subject,
        body_text=body,
        attachment_path=doc.output_filepath
    )

    doc.recipient_email = payload.recipient_email
    doc.email_status = "SENT" if sent else "FAILED"
    db.commit()

    return EmailSendResponse(
        status="sent" if sent else "failed",
        document_id=doc.id,
        recipient=payload.recipient_email,
        message="Email successfully dispatched" if sent else "Failed to dispatch email (check credentials)"
    )

@router.get("/{document_id}/view")
def view_document_pdf(
    document_id: str,
    file_type: str = "auto",  # 'output', 'original', or 'auto'
    db: Session = Depends(get_db)
):
    """View/Stream document PDF inline in browser. Defaults to output if available, else original."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")

    target_path = None
    target_name = None

    if file_type == "output" or (file_type == "auto" and doc.output_filepath and os.path.exists(doc.output_filepath)):
        target_path = doc.output_filepath
        target_name = doc.output_filename or f"output_{doc.filename}"
    elif doc.original_filepath and os.path.exists(doc.original_filepath):
        target_path = doc.original_filepath
        target_name = doc.filename

    if not target_path or not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail="Requested PDF file not found on server.")

    return FileResponse(
        path=target_path,
        filename=target_name,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{target_name}"'}
    )

@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete document record from database and clean up associated files."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")

    # Clean up original file
    if doc.original_filepath and os.path.exists(doc.original_filepath):
        try:
            os.remove(doc.original_filepath)
        except Exception as e:
            logger.warning(f"Could not delete original file {doc.original_filepath}: {e}")

    # Clean up output file
    if doc.output_filepath and os.path.exists(doc.output_filepath):
        try:
            os.remove(doc.output_filepath)
        except Exception as e:
            logger.warning(f"Could not delete output file {doc.output_filepath}: {e}")

    db.delete(doc)
    db.commit()
    logger.info(f"Successfully deleted document record {document_id}")

    return {"status": "success", "message": f"Document '{document_id}' successfully deleted."}

