"""
API integration tests for document acquisition guidance endpoints
Validates: Requirements 5.3, 5.4, 5.5
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_acquisition_guidance_endpoint():
    """Test acquisition guidance API endpoint"""
    response = client.post(
        "/documents/acquisition-guidance",
        json={"document_id": "AADHAAR", "language": "en"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "AADHAAR"
    assert "steps" in data
    assert len(data["steps"]) > 0
    assert "authority" in data


def test_acquisition_guidance_hindi():
    """Test acquisition guidance in Hindi"""
    response = client.post(
        "/documents/acquisition-guidance",
        json={"document_id": "INCOME_CERTIFICATE", "language": "hi"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "hi"
    assert "steps" in data


def test_acquisition_guidance_default_language():
    """Test acquisition guidance with default language"""
    response = client.post(
        "/documents/acquisition-guidance",
        json={"document_id": "CASTE_CERTIFICATE"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"


def test_document_template_endpoint():
    """Test document template API endpoint"""
    response = client.post(
        "/documents/template",
        json={"document_id": "INCOME_CERTIFICATE", "language": "en"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "INCOME_CERTIFICATE"
    assert "template_info" in data
    assert "format" in data["template_info"]
    assert "key_elements" in data["template_info"]


def test_document_template_tamil():
    """Test document template in Tamil"""
    response = client.post(
        "/documents/template",
        json={"document_id": "CASTE_CERTIFICATE", "language": "ta"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "ta"


def test_complete_guidance_endpoint():
    """Test complete guidance API endpoint"""
    response = client.post(
        "/documents/complete-guidance",
        json={"document_id": "INCOME_CERTIFICATE", "language": "en"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "INCOME_CERTIFICATE"
    assert "document_name" in data
    assert "acquisition_guidance" in data
    assert "template" in data
    assert "alternatives" in data


def test_complete_guidance_telugu():
    """Test complete guidance in Telugu"""
    response = client.post(
        "/documents/complete-guidance",
        json={"document_id": "CASTE_CERTIFICATE", "language": "te"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "te"


def test_authority_contact_endpoint():
    """Test authority contact API endpoint"""
    response = client.post(
        "/authorities/contact",
        json={"authority_id": "UIDAI_CENTER", "language": "en"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["authority_id"] == "UIDAI_CENTER"
    assert "contact_info" in data
    assert "phone" in data["contact_info"]
    assert "website" in data["contact_info"]


def test_authority_contact_hindi():
    """Test authority contact in Hindi"""
    response = client.post(
        "/authorities/contact",
        json={"authority_id": "TEHSIL_OFFICE", "language": "hi"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "hi"


def test_all_authorities_endpoint():
    """Test get all authorities API endpoint"""
    response = client.get("/authorities/all?language=en")
    
    assert response.status_code == 200
    data = response.json()
    assert "authorities" in data
    assert len(data["authorities"]) > 0
    assert data["language"] == "en"


def test_all_authorities_default_language():
    """Test get all authorities with default language"""
    response = client.get("/authorities/all")
    
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"


def test_invalid_document_acquisition_guidance():
    """Test acquisition guidance for invalid document"""
    response = client.post(
        "/documents/acquisition-guidance",
        json={"document_id": "INVALID_DOC", "language": "en"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "error" in data


def test_invalid_authority_contact():
    """Test authority contact for invalid authority"""
    response = client.post(
        "/authorities/contact",
        json={"authority_id": "INVALID_AUTH", "language": "en"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
