import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "document-guide"


def test_get_scheme_documents_endpoint():
    """Test getting scheme documents via API"""
    response = client.post(
        "/documents/scheme",
        json={"scheme_id": "PM-KISAN", "language": "en"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scheme_id"] == "PM-KISAN"
    assert data["total_documents"] == 3


def test_get_scheme_documents_hindi():
    """Test getting scheme documents in Hindi"""
    response = client.post(
        "/documents/scheme",
        json={"scheme_id": "PM-KISAN", "language": "hi"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "hi"
    # Check for Hindi text
    aadhaar_doc = next(doc for doc in data["documents"] if doc["document_id"] == "AADHAAR")
    assert "आधार" in aadhaar_doc["name"]


def test_get_document_alternatives_endpoint():
    """Test getting document alternatives via API"""
    response = client.post(
        "/documents/alternatives",
        json={"document_id": "AADHAAR", "language": "en"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "AADHAAR"
    assert len(data["alternatives"]) > 0


def test_get_scheme_documents_with_alternatives_endpoint():
    """Test getting complete scheme documents with alternatives"""
    response = client.post(
        "/documents/scheme/complete",
        json={"scheme_id": "PM-KISAN", "language": "en"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scheme_id"] == "PM-KISAN"
    # Check that documents have alternatives
    for doc in data["documents"]:
        assert "alternatives" in doc


def test_get_supported_languages_endpoint():
    """Test getting supported languages"""
    response = client.get("/documents/languages")
    assert response.status_code == 200
    data = response.json()
    assert "languages" in data
    assert "en" in data["languages"]
    assert "hi" in data["languages"]
    assert len(data["languages"]) == 10


def test_get_all_documents_endpoint():
    """Test getting all documents"""
    response = client.get("/documents/all?language=en")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert len(data["documents"]) > 0
    assert data["language"] == "en"


def test_get_all_documents_tamil():
    """Test getting all documents in Tamil"""
    response = client.get("/documents/all?language=ta")
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "ta"
    # Check for Tamil text
    aadhaar_doc = next(doc for doc in data["documents"] if doc["document_id"] == "AADHAAR")
    assert "ஆதார்" in aadhaar_doc["name"]


def test_invalid_scheme():
    """Test handling of invalid scheme ID"""
    response = client.post(
        "/documents/scheme",
        json={"scheme_id": "INVALID-SCHEME", "language": "en"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" in data


def test_default_language():
    """Test that default language is English"""
    response = client.post(
        "/documents/scheme",
        json={"scheme_id": "PM-KISAN"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"


def test_multiple_schemes():
    """Test getting documents for multiple schemes"""
    schemes = ["PM-KISAN", "MGNREGA", "SC-ST-SCHOLARSHIP"]
    
    for scheme_id in schemes:
        response = client.post(
            "/documents/scheme",
            json={"scheme_id": scheme_id, "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["scheme_id"] == scheme_id
        assert data["total_documents"] > 0


def test_alternatives_for_multiple_documents():
    """Test getting alternatives for multiple documents"""
    documents = ["AADHAAR", "LAND_RECORDS", "INCOME_CERTIFICATE"]
    
    for doc_id in documents:
        response = client.post(
            "/documents/alternatives",
            json={"document_id": doc_id, "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == doc_id
