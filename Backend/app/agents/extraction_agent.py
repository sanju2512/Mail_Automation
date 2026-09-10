from typing import Dict, Any, List, Optional
from app.services.llm_service import llm_service
from app.prompts.extraction import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt
from app.utils.json_utils import extract_json_from_text
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ExtractionAgent:
    """Agent responsible for structured information extraction using GroqCloud Qwen LLM."""

    def extract(
        self,
        document_text: str,
        document_type: str,
        required_fields: List[str],
        retrieved_knowledge: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(f"ExtractionAgent: Extracting structured fields for type '{document_type}'...")

        if not document_text or not document_text.strip():
            return {
                "document_type": document_type,
                "fields": {},
                "missing_fields": required_fields,
                "ambiguous_fields": [],
                "confidence": 0.0
            }

        prompt = build_extraction_prompt(
            document_text=document_text,
            document_type=document_type,
            required_fields=required_fields,
            retrieved_knowledge=retrieved_knowledge
        )

        messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        try:
            raw_response = llm_service.generate(messages, json_mode=True)
            parsed = extract_json_from_text(raw_response)
            if parsed and isinstance(parsed, dict):
                fields = parsed.get("fields", {})
                missing = parsed.get("missing_fields", [])
                ambiguous = parsed.get("ambiguous_fields", [])
                confidence = float(parsed.get("confidence", 0.9))

                # Verify required fields
                for req in required_fields:
                    val = fields.get(req)
                    if val is None or val == "" or str(val).lower() == "null":
                        if req not in missing:
                            missing.append(req)

                return {
                    "document_type": parsed.get("document_type", document_type),
                    "fields": fields,
                    "missing_fields": list(set(missing)),
                    "ambiguous_fields": ambiguous,
                    "confidence": confidence
                }
        except Exception as e:
            logger.error(f"ExtractionAgent failed to extract data via LLM: {e}")

        # Fallback heuristic extraction
        fallback_fields: Dict[str, Any] = {}
        for req in required_fields:
            fallback_fields[req] = None

        return {
            "document_type": document_type,
            "fields": fallback_fields,
            "missing_fields": required_fields,
            "ambiguous_fields": [],
            "confidence": 0.1
        }

extraction_agent = ExtractionAgent()
