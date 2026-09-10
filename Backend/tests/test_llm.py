import json
from unittest.mock import MagicMock
from app.services.llm_service import LLMService, LLMServiceError
from app.utils.json_utils import extract_json_from_text

def test_json_recovery_direct():
    text = '{"name": "Sanjay", "status": "valid"}'
    parsed = extract_json_from_text(text)
    assert parsed == {"name": "Sanjay", "status": "valid"}

def test_json_recovery_from_markdown():
    text = 'Here is the extracted data:\n```json\n{"name": "Sanjay", "score": 0.95}\n```'
    parsed = extract_json_from_text(text)
    assert parsed == {"name": "Sanjay", "score": 0.95}

def test_json_recovery_with_trailing_comma():
    text = '{"name": "Sanjay", "email": "sanjay@gmail.com",}'
    parsed = extract_json_from_text(text)
    assert parsed == {"name": "Sanjay", "email": "sanjay@gmail.com"}

def test_llm_service_generate_mock():
    service = LLMService(api_key="dummy_key", model="qwen-2.5-32b")
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '{"document_type": "employee_form"}'
    mock_response = MagicMock(choices=[mock_choice])
    mock_client.chat.completions.create.return_value = mock_response
    service.client = mock_client

    response = service.generate([{"role": "user", "content": "hi"}], json_mode=True)
    assert response == '{"document_type": "employee_form"}'
