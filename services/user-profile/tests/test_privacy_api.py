"""
Tests for privacy control API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from main import app
from models import (
    CreateUserProfileRequest,
    PersonalInfo,
    Demographics,
    Economic,
    Preferences,
    Gender,
    CasteCategory,
    Religion,
    Occupation,
    LanguageCode,
    DialectCode,
    CommunicationMode,
    LandDetails,
    BankDetails,
    PrivacyConsent
)


client = TestClient(app)


@pytest.fixture
def sample_profile_request():
    """Create a sample profile creation request."""
    return CreateUserProfileRequest(
        personalInfo=PersonalInfo(
            name="Test User",
            age=35,
            gender=Gender.MALE,
            phoneNumber="+919876543210"
        ),
        demographics=Demographics(
            state="Karnataka",
            district="Bangalore",
            block="North",
            village="Test Village",
            caste=CasteCategory.GENERAL,
            religion=Religion.HINDU,
            familySize=4
        ),
        economic=Economic(
            annualIncome=50000.0,
            occupation=Occupation.FARMER,
            landOwnership=LandDetails(owned=True, areaInAcres=2.5, irrigated=True),
            bankAccount=BankDetails(hasAccount=True)
        ),
        preferences=Preferences(
            preferredLanguage=LanguageCode.KN,
            preferredDialect=DialectCode.REGIONAL,
            communicationMode=CommunicationMode.VOICE
        )
    )


def test_export_user_data_endpoint(sample_profile_request):
    """Test data export API endpoint."""
    # Create a profile
    response = client.post("/profiles", json=sample_profile_request.model_dump())
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Export data
    response = client.get(f"/profiles/{user_id}/export")
    assert response.status_code == 200
    
    export_data = response.json()
    assert export_data["userId"] == user_id
    assert export_data["profile"] is not None
    assert "privacySettings" in export_data
    assert "accessLogs" in export_data


def test_export_user_data_without_access_logs(sample_profile_request):
    """Test data export without access logs."""
    # Create a profile
    response = client.post("/profiles", json=sample_profile_request.model_dump())
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Export data without access logs
    response = client.get(f"/profiles/{user_id}/export?include_access_logs=false")
    assert response.status_code == 200
    
    export_data = response.json()
    assert len(export_data["accessLogs"]) == 0


def test_export_user_data_not_found():
    """Test data export for non-existent user."""
    response = client.get("/profiles/non-existent-user/export")
    assert response.status_code == 404


def test_export_user_data_disabled(sample_profile_request):
    """Test data export when disabled in privacy settings."""
    # Create a profile
    response = client.post("/profiles", json=sample_profile_request.model_dump())
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Get privacy settings
    response = client.get(f"/profiles/{user_id}/privacy")
    assert response.status_code == 200
    settings = response.json()
    
    # Disable data export
    settings["allowDataExport"] = False
    response = client.put(f"/profiles/{user_id}/privacy", json=settings)
    assert response.status_code == 200
    
    # Try to export data
    response = client.get(f"/profiles/{user_id}/export")
    assert response.status_code == 403


def test_enforce_retention_policy_endpoint(sample_profile_request):
    """Test retention policy enforcement endpoint."""
    # Create a profile
    response = client.post("/profiles", json=sample_profile_request.model_dump())
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Enforce retention policy
    response = client.post(f"/profiles/{user_id}/retention/enforce")
    assert response.status_code == 200
    
    result = response.json()
    assert result["success"] is True
    assert "cleanupStats" in result


def test_enforce_retention_policy_not_found():
    """Test retention policy enforcement for non-existent user."""
    response = client.post("/profiles/non-existent-user/retention/enforce")
    assert response.status_code == 404


def test_enforce_retention_policy_all_endpoint(sample_profile_request):
    """Test batch retention policy enforcement endpoint."""
    # Create multiple profiles
    for i in range(3):
        profile_request = sample_profile_request.model_copy()
        profile_request.personalInfo.phoneNumber = f"+9198765432{i:02d}"
        response = client.post("/profiles", json=profile_request.model_dump())
        assert response.status_code == 200
    
    # Enforce retention policy for all users
    response = client.post("/admin/retention/enforce-all")
    assert response.status_code == 200
    
    result = response.json()
    assert result["success"] is True
    assert result["stats"]["usersProcessed"] >= 3


def test_privacy_dashboard_endpoint(sample_profile_request):
    """Test privacy dashboard endpoint."""
    # Create a profile
    response = client.post("/profiles", json=sample_profile_request.model_dump())
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Get privacy dashboard
    response = client.get(f"/profiles/{user_id}/privacy/dashboard")
    assert response.status_code == 200
    
    dashboard = response.json()
    assert dashboard["userId"] == user_id
    assert "privacySettings" in dashboard
    assert "deletionStatus" in dashboard
    assert "recentAccessLogs" in dashboard
    assert "familyMembersCount" in dashboard
    assert "dataExportAvailable" in dashboard


def test_privacy_dashboard_not_found():
    """Test privacy dashboard for non-existent user."""
    response = client.get("/profiles/non-existent-user/privacy/dashboard")
    assert response.status_code == 404


def test_privacy_dashboard_with_deletion_scheduled(sample_profile_request):
    """Test privacy dashboard shows deletion status."""
    # Create a profile
    response = client.post("/profiles", json=sample_profile_request.model_dump())
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Schedule deletion
    response = client.post(
        "/profiles/deletion/schedule",
        json={"userId": user_id, "reason": "Test deletion"}
    )
    assert response.status_code == 200
    
    # Get privacy dashboard
    response = client.get(f"/profiles/{user_id}/privacy/dashboard")
    assert response.status_code == 200
    
    dashboard = response.json()
    assert dashboard["deletionStatus"] is not None


def test_privacy_dashboard_shows_recent_access_logs(sample_profile_request):
    """Test privacy dashboard shows recent access logs."""
    # Create a profile
    response = client.post("/profiles", json=sample_profile_request.model_dump())
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Access profile multiple times to generate logs
    for _ in range(5):
        client.get(f"/profiles/{user_id}")
    
    # Get privacy dashboard
    response = client.get(f"/profiles/{user_id}/privacy/dashboard")
    assert response.status_code == 200
    
    dashboard = response.json()
    assert len(dashboard["recentAccessLogs"]) > 0


def test_privacy_dashboard_shows_family_count(sample_profile_request):
    """Test privacy dashboard shows family members count."""
    # Create a profile
    response = client.post("/profiles", json=sample_profile_request.model_dump())
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Create family member
    family_request = {
        "primaryUserId": user_id,
        "relationship": "spouse",
        "personalInfo": {
            "name": "Family Member",
            "age": 32,
            "gender": "female",
            "phoneNumber": "+919876543299"
        },
        "demographics": sample_profile_request.demographics.model_dump(),
        "economic": sample_profile_request.economic.model_dump(),
        "preferences": sample_profile_request.preferences.model_dump()
    }
    response = client.post(f"/profiles/{user_id}/family", json=family_request)
    assert response.status_code == 200
    
    # Get privacy dashboard
    response = client.get(f"/profiles/{user_id}/privacy/dashboard")
    assert response.status_code == 200
    
    dashboard = response.json()
    assert dashboard["familyMembersCount"] == 1


def test_data_export_includes_family_members(sample_profile_request):
    """Test data export includes family members."""
    # Create a profile
    response = client.post("/profiles", json=sample_profile_request.model_dump())
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Create family member
    family_request = {
        "primaryUserId": user_id,
        "relationship": "child",
        "personalInfo": {
            "name": "Child",
            "age": 10,
            "gender": "male",
            "phoneNumber": "+919876543298"
        },
        "demographics": sample_profile_request.demographics.model_dump(),
        "economic": sample_profile_request.economic.model_dump(),
        "preferences": sample_profile_request.preferences.model_dump()
    }
    response = client.post(f"/profiles/{user_id}/family", json=family_request)
    assert response.status_code == 200
    
    # Export data
    response = client.get(f"/profiles/{user_id}/export")
    assert response.status_code == 200
    
    export_data = response.json()
    assert len(export_data["familyMembers"]) == 1
    assert export_data["familyMembers"][0]["relationship"] == "child"


def test_privacy_settings_in_dashboard(sample_profile_request):
    """Test privacy settings are included in dashboard."""
    # Create a profile
    response = client.post("/profiles", json=sample_profile_request.model_dump())
    assert response.status_code == 200
    user_id = response.json()["profile"]["userId"]
    
    # Update consent
    response = client.post(
        f"/profiles/{user_id}/privacy/consent",
        params={
            "consent_type": PrivacyConsent.DATA_COLLECTION.value,
            "granted": True
        }
    )
    assert response.status_code == 200
    
    # Get privacy dashboard
    response = client.get(f"/profiles/{user_id}/privacy/dashboard")
    assert response.status_code == 200
    
    dashboard = response.json()
    assert len(dashboard["privacySettings"]["consents"]) == 1
