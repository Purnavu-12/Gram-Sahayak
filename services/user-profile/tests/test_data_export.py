"""
Tests for data export functionality.
"""

import pytest
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

from models import (
    UserProfile,
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
    FamilyMemberProfile,
    PrivacyConsent
)
from privacy_manager import PrivacyManager


@pytest.fixture
def temp_storage():
    """Create a temporary storage directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def privacy_manager(temp_storage):
    """Create a privacy manager with temporary storage."""
    return PrivacyManager(storage_path=temp_storage)


@pytest.fixture
def sample_profile():
    """Create a sample user profile for testing."""
    return UserProfile(
        userId="test-user-123",
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


@pytest.fixture
def sample_family_member():
    """Create a sample family member profile for testing."""
    return FamilyMemberProfile(
        memberId="member-456",
        primaryUserId="test-user-123",
        relationship="spouse",
        personalInfo=PersonalInfo(
            name="Family Member",
            age=32,
            gender=Gender.FEMALE,
            phoneNumber="+919876543211"
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
            annualIncome=30000.0,
            occupation=Occupation.SELF_EMPLOYED,
            landOwnership=LandDetails(owned=False, areaInAcres=0, irrigated=False),
            bankAccount=BankDetails(hasAccount=True)
        ),
        preferences=Preferences(
            preferredLanguage=LanguageCode.KN,
            preferredDialect=DialectCode.REGIONAL,
            communicationMode=CommunicationMode.VOICE
        )
    )


def test_export_user_data_basic(privacy_manager, sample_profile):
    """Test basic user data export."""
    user_id = sample_profile.userId
    
    export_data = privacy_manager.export_user_data(
        user_id=user_id,
        profile=sample_profile
    )
    
    assert export_data["userId"] == user_id
    assert export_data["profile"] is not None
    assert export_data["profile"]["userId"] == user_id
    assert export_data["exportDate"] is not None
    assert "privacySettings" in export_data
    assert "accessLogs" in export_data


def test_export_user_data_with_family(privacy_manager, sample_profile, sample_family_member):
    """Test user data export with family members."""
    user_id = sample_profile.userId
    
    export_data = privacy_manager.export_user_data(
        user_id=user_id,
        profile=sample_profile,
        family_members=[sample_family_member]
    )
    
    assert len(export_data["familyMembers"]) == 1
    assert export_data["familyMembers"][0]["memberId"] == sample_family_member.memberId


def test_export_user_data_with_access_logs(privacy_manager, sample_profile):
    """Test user data export includes access logs."""
    user_id = sample_profile.userId
    
    # Create some access logs
    for i in range(3):
        privacy_manager.log_data_access(
            user_id=user_id,
            accessed_by=f"accessor-{i}",
            access_type="read",
            data_fields=["profile"],
            purpose=f"Test access {i}"
        )
    
    export_data = privacy_manager.export_user_data(
        user_id=user_id,
        profile=sample_profile,
        include_access_logs=True
    )
    
    assert len(export_data["accessLogs"]) == 3


def test_export_user_data_without_access_logs(privacy_manager, sample_profile):
    """Test user data export excludes access logs when requested."""
    user_id = sample_profile.userId
    
    # Create some access logs
    privacy_manager.log_data_access(
        user_id=user_id,
        accessed_by="accessor",
        access_type="read",
        data_fields=["profile"],
        purpose="Test access"
    )
    
    export_data = privacy_manager.export_user_data(
        user_id=user_id,
        profile=sample_profile,
        include_access_logs=False
    )
    
    assert len(export_data["accessLogs"]) == 0


def test_export_user_data_with_deletion_status(privacy_manager, sample_profile):
    """Test user data export includes deletion status."""
    user_id = sample_profile.userId
    
    # Schedule deletion
    privacy_manager.schedule_deletion(user_id, "User requested")
    
    export_data = privacy_manager.export_user_data(
        user_id=user_id,
        profile=sample_profile
    )
    
    assert export_data["deletionStatus"] is not None
    assert export_data["deletionStatus"]["userId"] == user_id


def test_export_user_data_with_privacy_settings(privacy_manager, sample_profile):
    """Test user data export includes privacy settings."""
    user_id = sample_profile.userId
    
    # Update privacy settings
    privacy_manager.update_consent(
        user_id=user_id,
        consent_type=PrivacyConsent.DATA_COLLECTION,
        granted=True
    )
    
    export_data = privacy_manager.export_user_data(
        user_id=user_id,
        profile=sample_profile
    )
    
    assert export_data["privacySettings"] is not None
    assert len(export_data["privacySettings"]["consents"]) == 1


def test_export_user_data_without_profile(privacy_manager):
    """Test user data export without profile data."""
    user_id = "test-user-no-profile"
    
    export_data = privacy_manager.export_user_data(
        user_id=user_id,
        profile=None
    )
    
    assert export_data["userId"] == user_id
    assert export_data["profile"] is None
    assert export_data["privacySettings"] is not None  # Default settings created


def test_export_data_format(privacy_manager, sample_profile):
    """Test that exported data is properly formatted."""
    user_id = sample_profile.userId
    
    export_data = privacy_manager.export_user_data(
        user_id=user_id,
        profile=sample_profile
    )
    
    # Verify all expected keys are present
    expected_keys = [
        "exportDate",
        "userId",
        "profile",
        "familyMembers",
        "privacySettings",
        "deletionStatus",
        "accessLogs"
    ]
    
    for key in expected_keys:
        assert key in export_data
    
    # Verify export date is ISO format
    assert isinstance(export_data["exportDate"], str)
    datetime.fromisoformat(export_data["exportDate"])  # Should not raise


def test_export_data_completeness(privacy_manager, sample_profile):
    """Test that exported data includes all profile fields."""
    user_id = sample_profile.userId
    
    export_data = privacy_manager.export_user_data(
        user_id=user_id,
        profile=sample_profile
    )
    
    profile_data = export_data["profile"]
    
    # Verify all major sections are present
    assert "personalInfo" in profile_data
    assert "demographics" in profile_data
    assert "economic" in profile_data
    assert "preferences" in profile_data
    assert "applicationHistory" in profile_data
    
    # Verify personal info fields
    assert profile_data["personalInfo"]["name"] == "Test User"
    assert profile_data["personalInfo"]["age"] == 35
