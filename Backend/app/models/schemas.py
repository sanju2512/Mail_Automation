from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import datetime

# --- Health Schema ---
class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    app_name: str
    environment: str
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    database_connected: bool = True
    groq_configured: bool = False

# --- Document Upload & Extraction Schemas ---
class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    pages: int
    text: str
    status: str
    file_size_mb: float

class ExtractedFieldMeta(BaseModel):
    confidence: float = 1.0
    missing_fields: List[str] = []
    ambiguous_fields: List[str] = []
    source_pages: Dict[str, int] = {}

class DocumentExtractionResponse(BaseModel):
    document_id: str
    document_type: str
    fields: Dict[str, Any]
    metadata: ExtractedFieldMeta
    status: str

# --- LLM Test Schema ---
class LLMTestRequest(BaseModel):
    message: str

class LLMTestResponse(BaseModel):
    status: str
    response: str
    model: str

# --- RAG Schemas ---
class RAGIngestRequest(BaseModel):
    filename: Optional[str] = None
    document_type: Optional[str] = "policy"

class RAGIngestResponse(BaseModel):
    status: str
    chunks_indexed: int
    filename: str

class RAGSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 4
    document_type: Optional[str] = None

class RAGSearchResult(BaseModel):
    text: str
    source: str
    page: Optional[int] = 1
    score: float
    metadata: Dict[str, Any] = {}

class RAGSearchResponse(BaseModel):
    results: List[RAGSearchResult]
    total: int

# --- Validation Schemas ---
class ValidationErrorDetail(BaseModel):
    field: str
    type: str
    message: str

class ValidationWarningDetail(BaseModel):
    field: str
    message: str

class ValidationResult(BaseModel):
    status: str  # "valid" | "invalid"
    errors: List[ValidationErrorDetail] = []
    warnings: List[ValidationWarningDetail] = []
    suggested_actions: List[Dict[str, str]] = []

# --- Document Generation Schemas ---
class DocumentGenerateRequest(BaseModel):
    template_name: Optional[str] = "default_template.docx"
    output_format: Optional[str] = "pdf"  # "pdf" | "docx"

class DocumentGenerateResponse(BaseModel):
    status: str
    document_id: str
    output_file: str
    download_url: str

# --- Email Schemas ---
class EmailCheckResponse(BaseModel):
    status: str
    emails_processed: int
    documents_detected: List[str] = []
    message: str

class EmailSendRequest(BaseModel):
    recipient_email: str
    subject: Optional[str] = None
    body: Optional[str] = None

class EmailSendResponse(BaseModel):
    status: str
    document_id: str
    recipient: str
    message: str

# --- Orchestrator Processing Result ---
class ProcessDocumentResponse(BaseModel):
    document_id: str
    document_type: Optional[str] = None
    status: str
    extracted_data: Optional[Dict[str, Any]] = None
    retrieved_context: Optional[List[Dict[str, Any]]] = None
    validation: Optional[ValidationResult] = None
    output_file: Optional[str] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None
