import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON
from app.models.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filepath = Column(String, nullable=False)
    file_size_bytes = Column(Integer, default=0)
    page_count = Column(Integer, default=0)
    
    # Document Understanding & Extraction
    document_type = Column(String, nullable=True, default="unknown")
    extracted_text = Column(Text, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    confidence_score = Column(Float, default=0.0)
    
    # RAG Context & Source Traceability
    retrieved_sources = Column(JSON, nullable=True)
    
    # Validation & Error State
    validation_status = Column(String, default="PENDING")  # PENDING, VALID, INVALID
    validation_errors = Column(JSON, nullable=True)
    validation_warnings = Column(JSON, nullable=True)
    suggested_actions = Column(JSON, nullable=True)
    
    # Generation & Email Output
    output_filepath = Column(String, nullable=True)
    output_filename = Column(String, nullable=True)
    email_status = Column(String, default="NONE")  # NONE, PENDING, SENT, FAILED
    recipient_email = Column(String, nullable=True)
    
    # Lifecycle Status
    status = Column(String, default="RECEIVED", index=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
