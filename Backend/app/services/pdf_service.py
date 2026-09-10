import pymupdf as fitz
import os
from typing import Dict, Any, List, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)

class PDFExtractionError(Exception):
    """Custom exception raised during PDF parsing or extraction."""
    pass

class PDFService:
    @staticmethod
    def extract_text(file_path: str) -> Dict[str, Any]:
        """
        Extract structured text and page-by-page content from a PDF document using PyMuPDF.
        Handles encrypted, corrupt, empty, and image-only PDF edge cases.
        """
        if not os.path.exists(file_path):
            raise PDFExtractionError(f"File not found: {file_path}")

        try:
            doc = fitz.open(file_path)
        except Exception as e:
            logger.error(f"Failed to open PDF file {file_path}: {e}")
            raise PDFExtractionError(f"Corrupted or invalid PDF format: {str(e)}")

        if doc.is_encrypted:
            try:
                # Try opening with blank password
                if not doc.authenticate(""):
                    raise PDFExtractionError("PDF is password protected and cannot be extracted.")
            except Exception as e:
                raise PDFExtractionError(f"Encrypted PDF: {str(e)}")

        page_count = len(doc)
        if page_count == 0:
            doc.close()
            raise PDFExtractionError("PDF is empty with 0 pages.")

        pages_data: List[Dict[str, Any]] = []
        combined_text_list: List[str] = []
        total_extracted_chars = 0

        for page_idx in range(page_count):
            try:
                page = doc[page_idx]
                page_text = page.get_text("text").strip()
                char_count = len(page_text)
                total_extracted_chars += char_count

                pages_data.append({
                    "page_number": page_idx + 1,
                    "text": page_text,
                    "char_count": char_count
                })

                if page_text:
                    combined_text_list.append(f"--- PAGE {page_idx + 1} ---\n{page_text}")
            except Exception as e:
                logger.warning(f"Error extracting page {page_idx + 1} from {file_path}: {e}")
                pages_data.append({
                    "page_number": page_idx + 1,
                    "text": "",
                    "char_count": 0,
                    "error": str(e)
                })

        doc.close()

        full_text = "\n\n".join(combined_text_list).strip()

        # Warning / status if no extractable text was found (e.g. scanned image PDF)
        has_text = total_extracted_chars > 0

        return {
            "page_count": page_count,
            "full_text": full_text,
            "pages": pages_data,
            "total_chars": total_extracted_chars,
            "has_extractable_text": has_text,
            "status": "text_extracted" if has_text else "image_only_or_empty_text"
        }
