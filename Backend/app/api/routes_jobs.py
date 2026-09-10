from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models.database import get_db
from app.models.job import ProcessingJob
from app.models.document import Document

router = APIRouter(prefix="/jobs", tags=["Jobs & Auditing"])

@router.get("/{document_id}")
def get_jobs_for_document(document_id: str, db: Session = Depends(get_db)):
    """Retrieve audit trail of agent steps and status for a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{document_id}' not found")

    jobs = db.query(ProcessingJob).filter(ProcessingJob.document_id == document_id).order_by(ProcessingJob.created_at.asc()).all()
    
    return {
        "document_id": doc.id,
        "filename": doc.filename,
        "current_status": doc.status,
        "validation_status": doc.validation_status,
        "steps": [
            {
                "id": j.id,
                "step_name": j.step_name,
                "status": j.status,
                "details": j.details,
                "error_message": j.error_message,
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            }
            for j in jobs
        ]
    }
