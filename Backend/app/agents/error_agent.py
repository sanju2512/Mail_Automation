from typing import Dict, Any, List, Optional
from app.services.llm_service import llm_service
from app.prompts.error_handling import ERROR_HANDLING_SYSTEM_PROMPT, build_error_explanation_prompt
from app.utils.json_utils import extract_json_from_text
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ErrorAgent:
    """
    Error Agent: Processes validation errors, provides structured explanations,
    and suggests constructive remediation steps for users.
    """

    def explain_errors(
        self,
        errors: List[Dict[str, Any]],
        warnings: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        logger.info(f"ErrorAgent: Formatting explanations for {len(errors)} error(s)...")

        warnings_list = warnings or []
        suggested_actions = []

        # Deterministic generation of actionable messages
        for err in errors:
            field = err.get("field", "unknown")
            err_type = err.get("type", "validation_error")
            msg = err.get("message", "Validation failed.")

            if err_type == "missing_required_field":
                action = f"Please re-upload a document containing the required '{field}' field."
            elif err_type == "invalid_format":
                action = f"Ensure the '{field}' is formatted properly (e.g. valid email format user@domain.com or phone digits)."
            elif err_type == "invalid_number":
                action = f"Check the '{field}' and ensure it contains a valid numeric monetary amount."
            else:
                action = f"Review and correct the '{field}' entry in the source document."

            suggested_actions.append({
                "field": field,
                "error_type": err_type,
                "message": msg,
                "suggested_action": action
            })

        # Try LLM synthesis for a polished human summary if available
        summary = f"Document processing stopped due to {len(errors)} validation error(s)."
        try:
            prompt = build_error_explanation_prompt(errors, warnings_list)
            messages = [
                {"role": "system", "content": ERROR_HANDLING_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            raw_response = llm_service.generate(messages, json_mode=True)
            parsed = extract_json_from_text(raw_response)
            if parsed and parsed.get("summary"):
                summary = parsed.get("summary")
        except Exception as e:
            logger.debug(f"ErrorAgent LLM summary skipped ({e}), using default template summary.")

        return {
            "status": "error",
            "summary": summary,
            "error_count": len(errors),
            "suggested_actions": suggested_actions
        }

error_agent = ErrorAgent()
