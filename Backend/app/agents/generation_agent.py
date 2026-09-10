import os
from typing import Dict, Any
from app.services.document_service import document_service, DocumentGenerationError
from app.utils.logger import get_logger

logger = get_logger(__name__)

class GenerationAgent:
    """Agent responsible for populating verified document templates and producing final output."""

    def generate(
        self,
        document_id: str,
        document_type: str,
        extracted_fields: Dict[str, Any],
        validation_status: str
    ) -> Dict[str, Any]:
        logger.info(f"GenerationAgent: Initiating document build for ID '{document_id}'...")

        if validation_status != "valid":
            raise DocumentGenerationError("Cannot generate document: Validation status is not 'valid'.")

        file_path = document_service.generate_pdf(
            document_id=document_id,
            document_type=document_type,
            data=extracted_fields
        )

        return {
            "status": "success",
            "document_id": document_id,
            "output_path": file_path,
            "output_filename": os.path.basename(file_path),
            "download_url": f"/documents/{document_id}/download"
        }

generation_agent = GenerationAgent()
