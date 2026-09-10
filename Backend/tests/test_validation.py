from app.agents.validation_agent import validation_agent

def test_validation_valid_payload():
    data = {
        "name": "Sanjay Kumar",
        "email": "sanjay@gmail.com",
        "phone": "+919876543210",
        "date_of_birth": "2003-05-12"
    }
    result = validation_agent.validate(
        extracted_fields=data,
        required_fields=["name", "email", "phone"]
    )
    assert result["status"] == "valid"
    assert len(result["errors"]) == 0

def test_validation_invalid_email():
    data = {
        "name": "Sanjay Kumar",
        "email": "invalid_email_format",
        "phone": "9876543210"
    }
    result = validation_agent.validate(
        extracted_fields=data,
        required_fields=["name", "email"]
    )
    assert result["status"] == "invalid"
    assert any(e["field"] == "email" for e in result["errors"])

def test_validation_missing_required_field():
    data = {
        "name": "Sanjay Kumar",
        "email": "sanjay@gmail.com"
    }
    result = validation_agent.validate(
        extracted_fields=data,
        required_fields=["name", "email", "phone"]
    )
    assert result["status"] == "invalid"
    assert any(e["field"] == "phone" for e in result["errors"])
