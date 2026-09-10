import os
import pymupdf as fitz
from app.models.document import Document
from app.agents.orchestrator import orchestrator

def test_orchestrator_pipeline_flow(db_session, tmp_path):
    # Create sample PDF
    pdf_path = str(tmp_path / "employee_onboarding.pdf")
    doc = fitz.open()
    page = doc.new_page()
    text = (
        "EMPLOYEE ONBOARDING RECORD\n"
        "Name: Sanjay Kumar\n"
        "Email: sanjay@gmail.com\n"
        "Phone: 9876543210\n"
        "Date of Birth: 2003-05-12\n"
        "Employee ID: EMP-9021\n"
        "Department: Engineering"
    )
    page.insert_text((50, 50), text)
    doc.save(pdf_path)
    doc.close()

    # Create document record in test DB
    doc_id = "DOC-TEST-99"
    new_doc = Document(
        id=doc_id,
        filename="employee_onboarding.pdf",
        original_filepath=pdf_path,
        file_size_bytes=os.path.getsize(pdf_path),
        page_count=1,
        status="RECEIVED"
    )
    db_session.add(new_doc)
    db_session.commit()

    # Run orchestrator
    result = orchestrator.process_document(document_id=doc_id, db=db_session)

    assert result["document_id"] == doc_id
    assert result["status"] in ["completed", "invalid", "failed"]
