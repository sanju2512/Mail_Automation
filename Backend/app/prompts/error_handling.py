from typing import List, Dict, Any

ERROR_HANDLING_SYSTEM_PROMPT = """You are a Document Error Handling and User Clarification Agent.
When validation fails or documents have missing/corrupt values, your job is to translate raw technical validation errors into clear, polite, and actionable human-readable explanations and instructions.

RULES:
1. Do NOT guess or hallucinate valid data.
2. Provide a constructive 'suggested_action' for the user or submitter.
3. Return JSON with the format specified.
"""

def build_error_explanation_prompt(errors: List[Dict[str, Any]], warnings: List[Dict[str, Any]]) -> str:
    return f"""Validation Errors:
{errors}

Validation Warnings:
{warnings}

Generate actionable explanations for each issue. Return JSON:
{{
    "summary": "High-level summary of what is wrong with the document",
    "explanations": [
        {{
            "field": "field_name",
            "message": "Clear explanation of what is wrong",
            "suggested_action": "Actionable step for user to fix or re-upload"
        }}
    ]
}}
"""
