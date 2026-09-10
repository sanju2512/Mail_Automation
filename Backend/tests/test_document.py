import os
from app.services.document_service import document_service
from app.agents.generation_agent import generation_agent

def test_pdf_generation(tmp_path):
    data = {
        "name": "Sanjay Kumar",
        "email": "sanjay@gmail.com",
        "phone": "+919876543210",
        "employee_id": "EMP-1023",
        "department": "AI Engineering"
    }

    output_path = document_service.generate_pdf(
        document_id="TEST-001",
        document_type="employee_information",
        data=data,
        output_dir=str(tmp_path)
    )

    assert os.path.exists(output_path)
    assert output_path.endswith(".pdf")
    assert os.path.getsize(output_path) > 0
