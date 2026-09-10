import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ValidationAgent:
    """
    Validation Agent: Performs strict, deterministic validation on extracted fields.
    Does NOT hallucinate corrections. Fails early if critical requirements are violated.
    """

    EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    PHONE_REGEX = r"^\+?[0-9]{7,15}$"

    def validate(
        self,
        extracted_fields: Dict[str, Any],
        required_fields: Optional[List[str]] = None,
        missing_fields: Optional[List[str]] = None,
        ambiguous_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        logger.info("ValidationAgent: Running deterministic validation suite...")

        errors: List[Dict[str, str]] = []
        warnings: List[Dict[str, str]] = []

        # 1. Check reported missing fields
        if missing_fields:
            for field in missing_fields:
                errors.append({
                    "field": field,
                    "type": "missing_required_field",
                    "message": f"Mandatory field '{field}' is missing from the document."
                })

        # 2. Check required fields in data dictionary
        req_list = required_fields or []
        for req in req_list:
            val = extracted_fields.get(req)
            if val is None or str(val).strip() == "" or str(val).lower() == "null":
                # Ensure no duplicate error if already logged
                if not any(e["field"] == req and e["type"] == "missing_required_field" for e in errors):
                    errors.append({
                        "field": req,
                        "type": "missing_required_field",
                        "message": f"Mandatory field '{req}' is empty or not provided."
                    })

        # 3. Check ambiguous fields
        if ambiguous_fields:
            for amb in ambiguous_fields:
                warnings.append({
                    "field": amb,
                    "message": f"Field '{amb}' has ambiguous or conflicting information in the document."
                })

        # 4. Field-specific deterministic validations
        for field, value in extracted_fields.items():
            if value is None or str(value).strip() == "" or str(value).lower() == "null":
                continue

            str_val = str(value).strip()
            lower_field = field.lower()

            # Email validation
            if "email" in lower_field:
                if not re.match(self.EMAIL_REGEX, str_val):
                    errors.append({
                        "field": field,
                        "type": "invalid_format",
                        "message": f"'{str_val}' is not a valid email address format."
                    })

            # Phone validation (strip spaces/dashes before check)
            elif "phone" in lower_field or "mobile" in lower_field:
                clean_phone = re.sub(r"[\s\-\(\)]", "", str_val)
                if not re.match(self.PHONE_REGEX, clean_phone):
                    errors.append({
                        "field": field,
                        "type": "invalid_format",
                        "message": f"'{str_val}' is not a valid phone number (expected 7-15 digits)."
                    })

            # Date validation (e.g. YYYY-MM-DD or common date formats)
            elif "date" in lower_field or "dob" in lower_field:
                if not self._is_valid_date(str_val):
                    warnings.append({
                        "field": field,
                        "message": f"Date '{str_val}' could not be parsed into a standard ISO format (YYYY-MM-DD)."
                    })

            # Amount / Price validation
            elif "amount" in lower_field or "price" in lower_field or "total" in lower_field:
                clean_num = re.sub(r"[^\d.]", "", str_val)
                try:
                    float(clean_num)
                except ValueError:
                    errors.append({
                        "field": field,
                        "type": "invalid_number",
                        "message": f"'{str_val}' cannot be parsed as a numeric currency amount."
                    })

        is_valid = len(errors) == 0

        return {
            "status": "valid" if is_valid else "invalid",
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors),
            "warning_count": len(warnings)
        }

    def _is_valid_date(self, date_str: str) -> bool:
        formats = [
            "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y",
            "%Y/%m/%d", "%B %d, %Y", "%b %d, %Y", "%d %B %Y"
        ]
        for fmt in formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        return False

validation_agent = ValidationAgent()
