from typing import Dict, Any

VALIDATION_SEMANTIC_SYSTEM_PROMPT = """You are a Semantic Document Validation Specialist.
Your job is to check whether extracted document fields conform to domain business logic, logical consistency, and any referenced policy rules.
Do not repeat simple syntax checks (like email regex). Focus on semantic inconsistencies (e.g. date conflicts, logically impossible values, policy contradictions).

Return JSON:
{
    "is_consistent": true/false,
    "issues": [
        {"field": "field_name", "reason": "semantic issue description"}
    ]
}
"""

def build_semantic_validation_prompt(extracted_fields: Dict[str, Any], retrieved_policy: str = "") -> str:
    return f"""Extracted Data:
{extracted_fields}

Referenced Knowledge/Policy:
{retrieved_policy or 'No specific policy constraint provided.'}

Check for semantic inconsistencies or policy violations. Return JSON only."""
