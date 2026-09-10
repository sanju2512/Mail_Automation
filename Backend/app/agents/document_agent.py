from typing import Dict, Any
from app.services.llm_service import llm_service
from app.prompts.document_understanding import (
    DOCUMENT_UNDERSTANDING_SYSTEM_PROMPT,
    build_document_understanding_prompt,
)
from app.utils.json_utils import extract_json_from_text
from app.utils.logger import get_logger

logger = get_logger(__name__)

class DocumentAgent:
    """Agent responsible for understanding document type, entity structure, and schema."""

    def understand(self, document_text: str) -> Dict[str, Any]:
        logger.info("DocumentAgent: Analyzing document structure and intent...")

        if not document_text or len(document_text.strip()) == 0:
            return {
                "document_type": "unknown",
                "summary": "Empty document with no text content",
                "identified_entities": [],
                "required_fields": [],
                "confidence": 0.0
            }

        prompt = build_document_understanding_prompt(document_text[:4000])
        messages = [
            {"role": "system", "content": DOCUMENT_UNDERSTANDING_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        try:
            raw_response = llm_service.generate(messages, json_mode=True)
            parsed = extract_json_from_text(raw_response)
            if parsed and isinstance(parsed, dict):
                return {
                    "document_type": parsed.get("document_type", "general_document"),
                    "summary": parsed.get("summary", ""),
                    "identified_entities": parsed.get("identified_entities", []),
                    "required_fields": parsed.get("required_fields", ["name", "email", "phone", "date"]),
                    "confidence": float(parsed.get("confidence", 0.9))
                }
        except Exception as e:
            logger.error(f"DocumentAgent failed to understand document: {e}")

        # Deterministic fallback based on keyword heuristics
        lower_text = document_text.lower()
        if "employee" in lower_text or "date of birth" in lower_text or "department" in lower_text:
            doc_type = "employee_information"
            fields = ["name", "email", "phone", "date_of_birth", "employee_id", "department", "address"]
        elif "invoice" in lower_text or "amount due" in lower_text or "total" in lower_text:
            doc_type = "invoice"
            fields = ["invoice_number", "invoice_date", "customer_name", "total_amount", "line_items"]
        else:
            doc_type = "general_form"
            fields = ["name", "email", "phone", "date"]

        return {
            "document_type": doc_type,
            "summary": "Heuristic fallback classification",
            "identified_entities": [],
            "required_fields": fields,
            "confidence": 0.7
        }

document_agent = DocumentAgent()
