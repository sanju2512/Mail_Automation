from typing import Dict, Any

GENERATION_MAPPING_SYSTEM_PROMPT = """You are a Document Template Field Mapping Assistant.
Given a dictionary of extracted document fields and a list of target template placeholders, determine the exact key-to-placeholder mapping.
"""

def build_template_mapping_prompt(extracted_data: Dict[str, Any], template_placeholders: list) -> str:
    return f"""Extracted Data:
{extracted_data}

Template Placeholders:
{template_placeholders}

Map the extracted data keys to the matching template placeholders. Return JSON:
{{
    "mapping": {{
        "PLACEHOLDER_NAME": "extracted_value"
    }}
}}
"""
