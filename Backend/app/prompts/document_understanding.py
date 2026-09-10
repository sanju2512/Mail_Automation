DOCUMENT_UNDERSTANDING_SYSTEM_PROMPT = """You are an expert Document Classification and Analysis Agent.
Your task is to analyze raw document text and identify:
1. The exact document type (e.g., employee_information, purchase_order, invoice, resume, onboarding_form, insurance_claim, unknown).
2. The key entities present.
3. The expected schema and mandatory fields required for this document category.
4. An overview summary of the document contents.

RULES:
- Respond strictly with a valid JSON object. Do NOT include markdown code fences or conversational text.
- Do NOT invent or assume fields that do not exist.
"""

def build_document_understanding_prompt(document_text: str) -> str:
    return f"""Analyze the following extracted document text:

--- DOCUMENT TEXT START ---
{document_text}
--- DOCUMENT TEXT END ---

Return a JSON object in this exact format:
{{
    "document_type": "string (e.g. employee_information, invoice, purchase_order)",
    "summary": "Brief 1-2 sentence description",
    "identified_entities": ["list of entities found, e.g. Person, Company, Dates"],
    "required_fields": ["list of key fields that should be extracted from this document"],
    "confidence": 0.95
}}
"""
