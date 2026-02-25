"""
Integration tests for User Profile API.
"""

import pytest
import tempfile
import shutil
from fastapi.testclient import TestClient

from main import app, storage
from models import Gender, CasteCategory, Religion, Occupation, LanguageCode, DialectCode, CommunicationMode


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_profile_data():
    """Sample profile data for testing."""
    return {
        "personalInfo": {
            "name": "Ramesh Kumar",
            "age": 35,
            "gender": "male",
            "phoneNumber": "+919876543210"
        },
        "demographics": {
            "state": "Maharashtra",
            "district": "Pune",
            "block": "Haveli",
            "village": "Khed",
            "caste": "obc",
            "religion": "hindu",
            "familySize": 5
        },
        "economic": {
            "annualIncome": 50000.0,
            "occupation": "farmer",
            "landOwnership": {
                "owned": True,
                "areaInAcres": 2.5,
                "irrigated": True
            },
            "bankAccount": {
                "hasAccount": True
            }
        },
        "preferences": {
            "preferredLanguage": "hi",
            "preferredDialect": "regional",
            "communicationMode": "voice"
        }
    }


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_profile(client, sample_profile_data):
    """Test creating a new profile."""
    response = client.post("/profiles", json=sample_profile_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["profile"]["personalInfo"]["name"] == "Ramesh Kumar"
    assert "userId" in data["profile"]


def test_get_profile(client, sample_profile_data):
    """Test retrieving a profile."""
    # Create profile
    create_response = client.post("/profiles", json=sample_profile_data)
    user_id = create_response.json()["profile"]["userId"]
    
    # Get profile
    response = client.get(f"/profiles/{user_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["profile"]["userId"] == user_id


def test_get_nonexistent_profile(client):
    """Test retrieving a non-existent profile."""
    response = client.get("/profiles/nonexistent-id")
    assert response.status_code == 404


def test_update_profile(client, sample_profile_data):
    """Test updating a profile."""
    # Create profile
    create_response = client.post("/profiles", json=sample_profile_data)
    user_id = create_response.json()["profile"]["userId"]
    
    # Update profile
    update_data = {
        "userId": user_id,
        "personalInfo": {
            "name": "Ramesh Kumar Updated",
            "age": 36,
            "gender": "male",
            "phoneNumber": "+919876543210"
        }
    }
    
    response = client.put("/profiles", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["profile"]["personalInfo"]["name"] == "Ramesh Kumar Updated"
    assert data["profile"]["personalInfo"]["age"] == 36


def test_update_nonexistent_profile(client):
    """Test updating a non-existent profile."""
    update_data = {
        "userId": "nonexistent-id",
        "personalInfo": {
            "name": "Test",
            "age": 30,
            "gender": "male",
            "phoneNumber": "+919876543210"
        }
    }
    
    response = client.put("/profiles", json=update_data)
    assert response.status_code == 404


def test_delete_profile(client, sample_profile_data):
    """Test deleting a profile."""
    # Create profile
    create_response = client.post("/profiles", json=sample_profile_data)
    user_id = create_response.json()["profile"]["userId"]
    
    # Delete profile
    response = client.delete(f"/profiles/{user_id}")
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify deletion
    get_response = client.get(f"/profiles/{user_id}")
    assert get_response.status_code == 404


def test_delete_nonexistent_profile(client):
    """Test deleting a non-existent profile."""
    response = client.delete("/profiles/nonexistent-id")
    assert response.status_code == 404


def test_recognize_user(client, sample_profile_data):
    """Test recognizing user by phone number."""
    # Create profile
    client.post("/profiles", json=sample_profile_data)
    
    # Recognize user
    response = client.get("/profiles/recognize/+919876543210")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["profile"]["personalInfo"]["phoneNumber"] == "+919876543210"


def test_recognize_nonexistent_user(client):
    """Test recognizing non-existent user."""
    response = client.get("/profiles/recognize/+919999999999")
    assert response.status_code == 404


def test_invalid_profile_data(client):
    """Test creating profile with invalid data."""
    invalid_data = {
        "personalInfo": {
            "name": "Test",
            "age": -5,  # Invalid age
            "gender": "male",
            "phoneNumber": "+919876543210"
        }
    }
    
    response = client.post("/profiles", json=invalid_data)
    assert response.status_code == 422  # Validation error


def test_profile_with_aadhaar(client, sample_profile_data):
    """Test creating profile with Aadhaar number."""
    sample_profile_data["personalInfo"]["aadhaarNumber"] = "123456789012"
    
    response = client.post("/profiles", json=sample_profile_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["personalInfo"]["aadhaarNumber"] == "123456789012"


def test_profile_with_bank_details(client, sample_profile_data):
    """Test creating profile with complete bank details."""
    sample_profile_data["economic"]["bankAccount"] = {
        "hasAccount": True,
        "accountNumber": "1234567890",
        "ifscCode": "SBIN0001234",
        "bankName": "State Bank of India"
    }
    
    response = client.post("/profiles", json=sample_profile_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["economic"]["bankAccount"]["bankName"] == "State Bank of India"


def test_multiple_profiles_different_phones(client, sample_profile_data):
    """Test creating multiple profiles with different phone numbers."""
    # Create first profile
    response1 = client.post("/profiles", json=sample_profile_data)
    assert response1.status_code == 200
    
    # Create second profile with different phone
    sample_profile_data["personalInfo"]["phoneNumber"] = "+919876543211"
    sample_profile_data["personalInfo"]["name"] = "Another User"
    
    response2 = client.post("/profiles", json=sample_profile_data)
    assert response2.status_code == 200
    
    # Verify both profiles exist
    user_id1 = response1.json()["profile"]["userId"]
    user_id2 = response2.json()["profile"]["userId"]
    
    assert user_id1 != user_id2
