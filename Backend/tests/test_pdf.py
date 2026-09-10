import os
import pytest
import pymupdf as fitz
from app.services.pdf_service import PDFService, PDFExtractionError

def test_pdf_extraction(tmp_path):
    # Generate a small valid PDF
    pdf_path = str(tmp_path / "sample_employee.pdf")
    doc = fitz.open()
    page = doc.new_page()
    text = "Employee Onboarding Form\nName: Sanjay Kumar\nEmail: sanjay@gmail.com\nPhone: 9876543210\nDepartment: Engineering"
    page.insert_text((50, 50), text)
    doc.save(pdf_path)
    doc.close()

    result = PDFService.extract_text(pdf_path)
    assert result["page_count"] == 1
    assert "Sanjay Kumar" in result["full_text"]
    assert "sanjay@gmail.com" in result["full_text"]
    assert result["has_extractable_text"] is True

def test_invalid_pdf_path():
    with pytest.raises(PDFExtractionError):
        PDFService.extract_text("non_existent_file.pdf")

def test_empty_corrupted_pdf(tmp_path):
    corrupt_path = str(tmp_path / "corrupt.pdf")
    with open(corrupt_path, "wb") as f:
        f.write(b"not a valid pdf content")

    with pytest.raises(PDFExtractionError):
        PDFService.extract_text(corrupt_path)
