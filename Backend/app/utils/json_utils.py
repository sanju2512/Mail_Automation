import json
import re
from typing import Any, Dict, Optional, Tuple

def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract structured JSON from LLM output, supporting markdown fences,
    bracket matching, and common LLM response patterns.
    """
    if not text:
        return None

    cleaned = text.strip()

    # 1. Try direct JSON parsing
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 2. Try markdown code fences ```json ... ``` or ``` ... ```
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    matches = re.findall(fence_pattern, cleaned)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # 3. Try finding the outer-most balanced curly braces { ... }
    first_brace = cleaned.find('{')
    last_brace = cleaned.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = cleaned[first_brace:last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Simple syntax repair for trailing commas
            repaired = re.sub(r',\s*([\}\]])', r'\1', candidate)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass

    return None
