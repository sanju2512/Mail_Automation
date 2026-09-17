import datetime
import os
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.job import ProcessingJob
from app.services.pdf_service import PDFService
from app.agents.document_agent import document_agent
from app.agents.rag_agent import rag_agent
from app.agents.extraction_agent import extraction_agent
from app.agents.validation_agent import validation_agent
from app.agents.error_agent import error_agent
from app.agents.generation_agent import generation_agent
from app.utils.logger import get_logger

logger = get_logger(__name__)

class OrchestrationError(Exception):
    pass

class Orchestrator:
    """
    Agentic Orchestrator: Controls the end-to-end multi-agent lifecycle:
    1. Text Extraction (PyMuPDF)
    2. Document Understanding (Document Agent)
    3. Context Retrieval (RAG Agent / ChromaDB)
    4. Structured Reasoning & Extraction (GroqCloud Qwen LLM)
    5. Deterministic Validation (Validation Agent)
    6. Error Handling / Clarification (Error Agent)
    7. Document Generation (Generation Agent)
    8. State Persistence & Audit Trail (SQLite / SQLAlchemy)
    """

    def process_document(self, document_id: str, db: Session) -> Dict[str, Any]:
        logger.info(f"--- [ORCHESTRATOR] Starting pipeline for Document ID: {document_id} ---")

        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise OrchestrationError(f"Document '{document_id}' not found in database.")

        try:
            # STEP 1: Text Extraction
            self._update_doc_status(db, doc, "TEXT_EXTRACTED")
            if not doc.extracted_text:
                pdf_res = PDFService.extract_text(doc.original_filepath)
                doc.extracted_text = pdf_res.get("full_text", "")
                doc.page_count = pdf_res.get("page_count", 1)
                db.commit()

            self._record_job(db, document_id, "EXTRACTION", "SUCCESS", {"pages": doc.page_count})

            # STEP 2: Document Understanding
            self._update_doc_status(db, doc, "UNDERSTANDING")
            understanding = document_agent.understand(doc.extracted_text)
            doc.document_type = understanding.get("document_type", "general_document")
            required_fields = understanding.get("required_fields", [])
            self._record_job(db, document_id, "UNDERSTANDING", "SUCCESS", understanding)

            # STEP 3: RAG Retrieval
            self._update_doc_status(db, doc, "RETRIEVING")
            rag_res = rag_agent.retrieve_context(
                document_text=doc.extracted_text,
                document_type=doc.document_type
            )
            doc.retrieved_sources = rag_res.get("sources", [])
            self._record_job(db, document_id, "RAG_RETRIEVAL", "SUCCESS", {
                "chunks_retrieved": rag_res.get("total_chunks_retrieved", 0),
                "sources": doc.retrieved_sources
            })

            # STEP 4: Groq Qwen Extraction
            self._update_doc_status(db, doc, "EXTRACTING")
            extraction_res = extraction_agent.extract(
                document_text=doc.extracted_text,
                document_type=doc.document_type,
                required_fields=required_fields,
                retrieved_knowledge=rag_res.get("context_text")
            )
            doc.extracted_data = extraction_res.get("fields", {})
            doc.confidence_score = extraction_res.get("confidence", 0.9)
            self._record_job(db, document_id, "EXTRACTION_REASONING", "SUCCESS", extraction_res)

            # STEP 5: Validation
            self._update_doc_status(db, doc, "VALIDATING")
            validation_res = validation_agent.validate(
                extracted_fields=doc.extracted_data,
                required_fields=required_fields,
                missing_fields=extraction_res.get("missing_fields"),
                ambiguous_fields=extraction_res.get("ambiguous_fields")
            )

            doc.validation_status = validation_res.get("status", "invalid").upper()
            doc.validation_errors = validation_res.get("errors", [])
            doc.validation_warnings = validation_res.get("warnings", [])

            # STEP 6: Generation Agent (Always build output document with extracted fields)
            self._update_doc_status(db, doc, "GENERATING")
            gen_res = generation_agent.generate(
                document_id=document_id,
                document_type=doc.document_type,
                extracted_fields=doc.extracted_data,
                validation_status=validation_res.get("status", "valid")
            )
            doc.output_filepath = gen_res.get("output_path")
            doc.output_filename = gen_res.get("output_filename")
            self._record_job(db, document_id, "DOCUMENT_GENERATION", "SUCCESS", gen_res)

            # STEP 7: Branch on Validation Result
            if validation_res["status"] == "invalid":
                # Branch: Error Agent
                self._update_doc_status(db, doc, "INVALID")
                error_res = error_agent.explain_errors(
                    errors=doc.validation_errors,
                    warnings=doc.validation_warnings
                )
                doc.suggested_actions = error_res.get("suggested_actions", [])
                doc.error_message = error_res.get("summary", "Validation failed.")
                self._record_job(db, document_id, "VALIDATION", "FAILED", {
                    "errors": doc.validation_errors,
                    "suggested_actions": doc.suggested_actions
                })
                db.commit()

                return {
                    "document_id": document_id,
                    "document_type": doc.document_type,
                    "status": "invalid",
                    "extracted_data": doc.extracted_data,
                    "retrieved_context": doc.retrieved_sources,
                    "validation": validation_res,
                    "suggested_actions": doc.suggested_actions,
                    "error_message": doc.error_message,
                    "output_file": doc.output_filename,
                    "download_url": gen_res.get("download_url")
                }

            self._update_doc_status(db, doc, "COMPLETED")
            db.commit()

            return {
                "document_id": document_id,
                "document_type": doc.document_type,
                "status": "completed",
                "extracted_data": doc.extracted_data,
                "retrieved_context": doc.retrieved_sources,
                "validation": validation_res,
                "output_file": doc.output_filename,
                "download_url": gen_res.get("download_url")
            }

        except Exception as e:
            logger.exception(f"Fatal error orchestrating document {document_id}: {e}")
            self._update_doc_status(db, doc, "FAILED", error_msg=str(e))
            self._record_job(db, document_id, "ORCHESTRATION", "FAILED", error_msg=str(e))
            db.commit()
            return {
                "document_id": document_id,
                "status": "failed",
                "error_message": str(e)
            }

    def _update_doc_status(self, db: Session, doc: Document, status_val: str, error_msg: Optional[str] = None):
        doc.status = status_val
        if error_msg:
            doc.error_message = error_msg
        db.commit()

    def _record_job(self, db: Session, doc_id: str, step_name: str, status_val: str, details: Any = None, error_msg: Optional[str] = None):
        job = ProcessingJob(
            id=f"JOB-{uuid.uuid4().hex[:8].upper()}",
            document_id=doc_id,
            step_name=step_name,
            status=status_val,
            details=details,
            error_message=error_msg,
            completed_at=datetime.datetime.utcnow()
        )
        db.add(job)
        db.commit()

orchestrator = Orchestrator()
