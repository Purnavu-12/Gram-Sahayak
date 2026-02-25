"""
Integration tests for user profile API with new features.
"""

import pytest
import tempfile
import shutil
from fastapi.testclient import TestClient

# Import app and reinitialize with test storage
import os
os.environ["STORAGE_PATH"] = tempfile.mkdtemp()
os.environ["PRIVACY_PATH"] = tempfile.mkdtemp()
os.environ["FAMILY_PATH"] = tempfile.mkdtemp()

from main import app
from models import Gender, CasteCategory, Religion, Occupation, LanguageCode, DialectCode, CommunicationMode


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_profile_data():
    """Sample profile data for testing."""
    return {
        "personalInfo": {
            "name": "Test User",
            "age": 30,
            "gender": "male",
            "phoneNumber": "+919876543210"
        },
        "demographics": {
            "state": "Bihar",
            "district": "Patna",
            "block": "Danapur",
            "village": "Rampur",
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


def test_voice_update_with_confirmation(client, sample_profile_data):
    """Test voice-based profile update with confirmation required."""
    # Create profile
    response = client.post("/profiles", json=sample_profile_data)
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Voice update request
    voice_update = {
        "userId": user_id,
        "naturalLanguageUpdate": "My name is Ramesh Kumar and I am 35 years old",
        "confirmationRequired": True
    }
    
    response = client.post("/profiles/voice-update", json=voice_update)
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["requiresConfirmation"] is True
    assert "parsedUpdates" in data
    assert "name" in data["parsedUpdates"]
    assert data["parsedUpdates"]["name"] == "Ramesh Kumar"
    assert "age" in data["parsedUpdates"]
    assert data["parsedUpdates"]["age"] == 35


def test_voice_update_without_confirmation(client, sample_profile_data):
    """Test voice-based profile update without confirmation."""
    # Create profile
    response = client.post("/profiles", json=sample_profile_data)
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Voice update request without confirmation
    voice_update = {
        "userId": user_id,
        "naturalLanguageUpdate": "My occupation is daily wage worker",
        "confirmationRequired": False
    }
    
    response = client.post("/profiles/voice-update", json=voice_update)
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    
    # Verify profile was updated
    response = client.get(f"/profiles/{user_id}")
    profile = response.json()["profile"]
    assert profile["economic"]["occupation"] == "daily_wage_worker"


def test_voice_update_confirm(client, sample_profile_data):
    """Test confirming voice-based profile updates."""
    # Create profile
    response = client.post("/profiles", json=sample_profile_data)
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Confirm updates
    updates = {
        "name": "Confirmed Name",
        "age": 40
    }
    
    response = client.post(
        f"/profiles/voice-update/confirm?user_id={user_id}",
        json=updates
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify profile was updated
    response = client.get(f"/profiles/{user_id}")
    profile = response.json()["profile"]
    assert profile["personalInfo"]["name"] == "Confirmed Name"
    assert profile["personalInfo"]["age"] == 40


def test_schedule_data_deletion(client, sample_profile_data):
    """Test scheduling data deletion."""
    # Create profile
    response = client.post("/profiles", json=sample_profile_data)
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Schedule deletion
    deletion_request = {
        "userId": user_id,
        "reason": "User requested account closure"
    }
    
    response = client.post("/profiles/deletion/schedule", json=deletion_request)
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "scheduledDeletionDate" in data
    assert "confirmationId" in data


def test_get_deletion_status(client, sample_profile_data):
    """Test getting deletion status."""
    # Create profile
    response = client.post("/profiles", json=sample_profile_data)
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Schedule deletion
    deletion_request = {"userId": user_id}
    response = client.post("/profiles/deletion/schedule", json=deletion_request)
    deletion_id = response.json()["confirmationId"]
    
    # Get status
    response = client.get(f"/profiles/deletion/status/{user_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["scheduled"] is True
    assert data["deletionId"] == deletion_id
    assert "scheduledDate" in data


def test_cancel_deletion(client, sample_profile_data):
    """Test cancelling scheduled deletion."""
    # Create profile
    response = client.post("/profiles", json=sample_profile_data)
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Schedule deletion
    deletion_request = {"userId": user_id}
    response = client.post("/profiles/deletion/schedule", json=deletion_request)
    deletion_id = response.json()["confirmationId"]
    
    # Cancel deletion
    response = client.post(f"/profiles/deletion/cancel/{deletion_id}")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_create_family_member(client, sample_profile_data):
    """Test creating a family member profile."""
    # Create primary user
    response = client.post("/profiles", json=sample_profile_data)
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Create family member
    family_member = {
        "primaryUserId": user_id,
        "relationship": "son",
        "personalInfo": {
            "name": "Rahul Kumar",
            "age": 18,
            "gender": "male",
            "phoneNumber": "+919876543211"
        },
        "demographics": sample_profile_data["demographics"],
        "economic": {
            "annualIncome": 0.0,
            "occupation": "student",
            "landOwnership": {
                "owned": False,
                "areaInAcres": 0.0,
                "irrigated": False
            },
            "bankAccount": {
                "hasAccount": False
            }
        },
        "preferences": sample_profile_data["preferences"]
    }
    
    response = client.post(f"/profiles/{user_id}/family", json=family_member)
    assert response.status_code == 200
    data = response.json()
    
    assert data["memberId"] is not None
    assert data["primaryUserId"] == user_id
    assert data["relationship"] == "son"
    assert data["personalInfo"]["name"] == "Rahul Kumar"


def test_get_family_members(client, sample_profile_data):
    """Test getting all family members."""
    # Create primary user
    response = client.post("/profiles", json=sample_profile_data)
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Create multiple family members
    for i, relationship in enumerate(["son", "daughter"]):
        family_member = {
            "primaryUserId": user_id,
            "relationship": relationship,
            "personalInfo": {
                "name": f"Member {i}",
                "age": 18 + i,
                "gender": "male" if i == 0 else "female",
                "phoneNumber": f"+91987654321{i}"
            },
            "demographics": sample_profile_data["demographics"],
            "economic": {
                "annualIncome": 0.0,
                "occupation": "student",
                "landOwnership": {
                    "owned": False,
                    "areaInAcres": 0.0,
                    "irrigated": False
                },
                "bankAccount": {
                    "hasAccount": False
                }
            },
            "preferences": sample_profile_data["preferences"]
        }
        client.post(f"/profiles/{user_id}/family", json=family_member)
    
    # Get all family members
    response = client.get(f"/profiles/{user_id}/family")
    assert response.status_code == 200
    members = response.json()
    
    assert len(members) == 2
    relationships = [m["relationship"] for m in members]
    assert "son" in relationships
    assert "daughter" in relationships


def test_delete_family_member(client, sample_profile_data):
    """Test deleting a family member."""
    # Create primary user
    response = client.post("/profiles", json=sample_profile_data)
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Create family member
    family_member = {
        "primaryUserId": user_id,
        "relationship": "son",
        "personalInfo": {
            "name": "Test Member",
            "age": 20,
            "gender": "male",
            "phoneNumber": "+919876543211"
        },
        "demographics": sample_profile_data["demographics"],
        "economic": {
            "annualIncome": 0.0,
            "occupation": "student",
            "landOwnership": {
                "owned": False,
                "areaInAcres": 0.0,
                "irrigated": False
            },
            "bankAccount": {
                "hasAccount": False
            }
        },
        "preferences": sample_profile_data["preferences"]
    }
    
    response = client.post(f"/profiles/{user_id}/family", json=family_member)
    member_id = response.json()["memberId"]
    
    # Delete family member
    response = client.delete(f"/profiles/family/{member_id}")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_get_privacy_settings(client, sample_profile_data):
    """Test getting privacy settings."""
    # Create profile
    response = client.post("/profiles", json=sample_profile_data)
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Get privacy settings
    response = client.get(f"/profiles/{user_id}/privacy")
    assert response.status_code == 200
    settings = response.json()
    
    assert settings["userId"] == user_id
    assert "dataRetentionDays" in settings
    assert "allowFamilyAccess" in settings
    assert "consents" in settings


def test_update_privacy_settings(client, sample_profile_data):
    """Test updating privacy settings."""
    # Create profile
    response = client.post("/profiles", json=sample_profile_data)
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Get current settings
    response = client.get(f"/profiles/{user_id}/privacy")
    settings = response.json()
    
    # Update settings
    settings["dataRetentionDays"] = 180
    settings["allowFamilyAccess"] = False
    
    response = client.put(f"/profiles/{user_id}/privacy", json=settings)
    assert response.status_code == 200
    updated = response.json()
    
    assert updated["dataRetentionDays"] == 180
    assert updated["allowFamilyAccess"] is False


def test_update_consent(client, sample_profile_data):
    """Test updating user consent."""
    # Create profile
    response = client.post("/profiles", json=sample_profile_data)
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Update consent
    response = client.post(
        f"/profiles/{user_id}/privacy/consent",
        params={
            "consent_type": "data_collection",
            "granted": True,
            "version": "1.0"
        }
    )
    assert response.status_code == 200
    settings = response.json()
    
    assert len(settings["consents"]) > 0
    consent = settings["consents"][0]
    assert consent["consentType"] == "data_collection"
    assert consent["granted"] is True


def test_get_access_logs(client, sample_profile_data):
    """Test getting data access logs."""
    # Create profile
    response = client.post("/profiles", json=sample_profile_data)
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Perform some operations to generate logs
    client.get(f"/profiles/{user_id}")
    client.get(f"/profiles/{user_id}/privacy")
    
    # Get access logs
    response = client.get(f"/profiles/{user_id}/access-logs")
    assert response.status_code == 200
    logs = response.json()
    
    assert isinstance(logs, list)
    # Should have at least the log from getting access logs itself
    assert len(logs) > 0
