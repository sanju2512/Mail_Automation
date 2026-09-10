from typing import List, Optional

EXTRACTION_SYSTEM_PROMPT = """You are an Agentic Data Extraction Specialist.
Your job is to extract structured, truthful information from raw document text and any relevant contextual knowledge.

CRITICAL EXTRACTION RULES:
1. NEVER hallucinate or invent missing data.
2. If a field is not present in the text, set its value to null.
3. If a field is ambiguous or uncertain, place the field name into "ambiguous_fields".
4. If a field was expected but completely missing, add it to "missing_fields".
5. Return ONLY a single valid JSON object. No explanations outside the JSON.
"""

def build_extraction_prompt(
    document_text: str,
    document_type: str,
    required_fields: List[str],
    retrieved_knowledge: Optional[str] = None
) -> str:
    knowledge_section = ""
    if retrieved_knowledge:
        knowledge_section = f"""
--- RETRIEVED KNOWLEDGE BASE CONTEXT (RAG) START ---
{retrieved_knowledge}
--- RETRIEVED KNOWLEDGE BASE CONTEXT (RAG) END ---
Use the above knowledge to help resolve company policies, standard codes, or entity definitions if applicable.
"""

    return f"""Document Type: {document_type}
Expected / Required Fields: {required_fields}

{knowledge_section}

--- DOCUMENT TEXT START ---
{document_text}
--- DOCUMENT TEXT END ---

Extract all information truthfully into this JSON structure:
{{
    "document_type": "{document_type}",
    "fields": {{
        // Key-value pairs of extracted properties (e.g., "name", "email", "phone", "date_of_birth", "address", "employee_id", "total_amount")
    }},
    "missing_fields": ["list of required fields that could not be found"],
    "ambiguous_fields": ["list of fields where the value was unclear or contradictory"],
    "confidence": 0.95
}}
"""
