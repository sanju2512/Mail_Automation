import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from app.models.database import Base

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String, primary_key=True, index=True)
    document_id = Column(String, index=True, nullable=False)
    step_name = Column(String, nullable=False)  # EXTRACTION, RAG, UNDERSTANDING, VALIDATION, GENERATION, EMAIL
    status = Column(String, default="PENDING")  # PENDING, IN_PROGRESS, SUCCESS, FAILED
    details = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
