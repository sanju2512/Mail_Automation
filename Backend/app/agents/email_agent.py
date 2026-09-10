import os
import threading
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.services.email_service import email_service
from app.models.document import Document
from app.models.job import ProcessingJob
from app.services.pdf_service import PDFService
from app.utils.logger import get_logger

logger = get_logger(__name__)

class EmailAgent:
    """Agent responsible for checking incoming emails, deduplicating, and ingesting attached documents."""

    def _process_document_async(self, doc_id: str):
        """Run orchestrator in a background thread so documents appear in queue first."""
        try:
            # Import here to avoid circular imports
            from app.agents.orchestrator import orchestrator
            from app.models.database import SessionLocal
            
            db = SessionLocal()
            logger.info(f"   [BACKGROUND] Starting async orchestration for {doc_id}...")
            result = orchestrator.process_document(document_id=doc_id, db=db)
            logger.info(f"   [BACKGROUND] ✅ Orchestration completed for {doc_id}")
            logger.info(f"   [BACKGROUND] Final Status: {result.get('status', 'UNKNOWN')}")
            db.close()
        except Exception as e:
            logger.error(f"   [BACKGROUND] ❌ Async orchestration failed for {doc_id}: {e}", exc_info=True)

    def check_and_ingest(self, db: Session) -> Dict[str, Any]:
        logger.info("=" * 80)
        logger.info("EmailAgent: Checking configured mailbox for new PDF documents...")
        logger.info("=" * 80)
        
        downloaded = email_service.check_inbox()
        created_docs = []
        failed_docs = []

        logger.info(f"Found {len(downloaded)} PDF(s) to ingest")

        for item in downloaded:
            doc_id = item["document_id"]
            filepath = item["filepath"]
            filename = item["filename"]
            sender = item.get("sender", "Unknown")
            subject = item.get("subject", "No Subject")

            logger.info(f"\n📄 Processing Email Attachment:")
            logger.info(f"   Document ID: {doc_id}")
            logger.info(f"   Filename: {filename}")
            logger.info(f"   From: {sender}")
            logger.info(f"   Subject: {subject}")

            try:
                # Prevent duplicate processing by checking file existence or message ID
                existing = db.query(Document).filter(Document.id == doc_id).first()
                if existing:
                    logger.warning(f"   ⚠️  Document {doc_id} already exists. Skipping duplicate.")
                    continue

                # Extract initial text
                logger.info(f"   Extracting text from PDF...")
                text_info = PDFService.extract_text(filepath)

                new_doc = Document(
                    id=doc_id,
                    filename=filename,
                    original_filepath=filepath,
                    file_size_bytes=os.path.getsize(filepath),
                    page_count=text_info.get("page_count", 1),
                    extracted_text=text_info.get("full_text", ""),
                    status="RECEIVED"
                )
                db.add(new_doc)

                # Audit job record
                job = ProcessingJob(
                    id=f"JOB-EMAIL-{doc_id}",
                    document_id=doc_id,
                    step_name="EMAIL_INGESTION",
                    status="SUCCESS",
                    details={"sender": sender, "subject": subject, "pages": text_info.get("page_count", 1)}
                )
                db.add(job)
                db.commit()

                logger.info(f"   ✅ Document ingested. Status: RECEIVED")
                logger.info(f"   📝 Extracted {text_info.get('page_count', 1)} page(s) of text")
                logger.info(f"   ⏳ Document now available in queue while processing begins...")
                
                created_docs.append(doc_id)

                # Start orchestrator in background thread (non-blocking)
                logger.info(f"   🚀 Queuing agentic pipeline for background processing...")
                background_thread = threading.Thread(
                    target=self._process_document_async,
                    args=(doc_id,),
                    daemon=True
                )
                background_thread.start()
                logger.info(f"   ✓ Background thread started for {doc_id}")

            except Exception as e:
                logger.error(f"   ❌ Error processing document {doc_id}: {e}", exc_info=True)
                failed_docs.append({"doc_id": doc_id, "error": str(e)})

        logger.info("\n" + "=" * 80)
        logger.info(f"EmailAgent Summary:")
        logger.info(f"  • Emails processed: {len(downloaded)}")
        logger.info(f"  • Documents ingested: {len(created_docs)}")
        logger.info(f"  • Failed: {len(failed_docs)}")
        if created_docs:
            logger.info(f"  • Queued IDs: {', '.join(created_docs)}")
            logger.info(f"  • Status: RECEIVED (processing in background)")
        if failed_docs:
            logger.info(f"  • Failed IDs: {', '.join([f['doc_id'] for f in failed_docs])}")
        logger.info("=" * 80)

        return {
            "status": "success",
            "emails_processed": len(downloaded),
            "documents_detected": created_docs,
            "failed_documents": failed_docs,
            "message": f"✅ Successfully ingested {len(created_docs)} document(s) from email inbox. Processing in background..."
        }

email_agent = EmailAgent()
