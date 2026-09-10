import os
import re
import uuid
import shutil
from pathlib import Path
from typing import Tuple

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and illegal characters."""
    # Remove directory separators
    filename = os.path.basename(filename)
    # Remove any non-alphanumeric, dot, dash, underscore characters
    clean_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    # Avoid empty filename
    return clean_name if clean_name else f"document_{uuid.uuid4().hex[:8]}.pdf"

def generate_document_id(prefix: str = "DOC") -> str:
    """Generate a unique formatted document identifier."""
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

def is_safe_path(base_dir: str, target_path: str) -> bool:
    """Check if target_path resides safely within base_dir to avoid path traversal."""
    resolved_base = Path(base_dir).resolve()
    resolved_target = Path(target_path).resolve()
    try:
        resolved_target.relative_to(resolved_base)
        return True
    except ValueError:
        return False

def get_file_size_mb(file_path: str) -> float:
    """Return file size in megabytes."""
    return os.path.getsize(file_path) / (1024 * 1024)
