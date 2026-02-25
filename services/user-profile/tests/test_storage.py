"""
Unit tests for user profile storage service.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from storage import UserProfileStorage
from models import (
    CreateUserProfileRequest, UpdateUserProfileRequest,
    PersonalInfo, Demographics, Economic, Preferences,
    LandDetails, BankDetails,
    Gender, CasteCategory, Religion, Occupation,
    LanguageCode, DialectCode, CommunicationMode
)


@pytest.fixture
def temp_storage():
    """Create temporary storage directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def storage_service(temp_storage):
    """Create storage service with temporary directory."""
    return UserProfileStorage(storage_path=temp_storage)


@pytest.fixture
def sample_profile_request():
    """Create sample profile request."""
    return CreateUserProfileRequest(
        personalInfo=PersonalInfo(
            name="Ramesh Kumar",
            age=35,
            gender=Gender.MALE,
            phoneNumber="+919876543210"
        ),
        demographics=Demographics(
            state="Maharashtra",
            district="Pune",
            block="Haveli",
            village="Khed",
            caste=CasteCategory.OBC,
            religion=Religion.HINDU,
            familySize=5
        ),
        economic=Economic(
            annualIncome=50000.0,
            occupation=Occupation.FARMER,
            landOwnership=LandDetails(owned=True, areaInAcres=2.5, irrigated=True),
            bankAccount=BankDetails(hasAccount=True)
        ),
        preferences=Preferences(
            preferredLanguage=LanguageCode.HI,
            preferredDialect=DialectCode.REGIONAL,
            communicationMode=CommunicationMode.VOICE
        )
    )


def test_create_profile(storage_service, sample_profile_request):
    """Test creating a new profile."""
    profile = storage_service.create_profile(sample_profile_request)
    
    assert profile.userId is not None
    assert profile.personalInfo.name == "Ramesh Kumar"
    assert profile.demographics.state == "Maharashtra"
    assert len(profile.applicationHistory) == 0


def test_get_profile(storage_service, sample_profile_request):
    """Test retrieving a profile."""
    created = storage_service.create_profile(sample_profile_request)
    retrieved = storage_service.get_profile(created.userId)
    
    assert retrieved is not None
    assert retrieved.userId == created.userId
    assert retrieved.personalInfo.name == created.personalInfo.name


def test_get_nonexistent_profile(storage_service):
    """Test retrieving a non-existent profile."""
    profile = storage_service.get_profile("nonexistent-id")
    assert profile is None


def test_update_profile(storage_service, sample_profile_request):
    """Test updating a profile."""
    created = storage_service.create_profile(sample_profile_request)
    
    update_request = UpdateUserProfileRequest(
        userId=created.userId,
        personalInfo=PersonalInfo(
            name="Ramesh Kumar Updated",
            age=36,
            gender=Gender.MALE,
            phoneNumber="+919876543210"
        )
    )
    
    updated = storage_service.update_profile(update_request)
    
    assert updated is not None
    assert updated.personalInfo.name == "Ramesh Kumar Updated"
    assert updated.personalInfo.age == 36
    assert updated.demographics.state == "Maharashtra"  # Unchanged


def test_update_nonexistent_profile(storage_service):
    """Test updating a non-existent profile."""
    update_request = UpdateUserProfileRequest(
        userId="nonexistent-id",
        personalInfo=PersonalInfo(
            name="Test",
            age=30,
            gender=Gender.MALE,
            phoneNumber="+919876543210"
        )
    )
    
    result = storage_service.update_profile(update_request)
    assert result is None


def test_delete_profile(storage_service, sample_profile_request):
    """Test deleting a profile."""
    created = storage_service.create_profile(sample_profile_request)
    
    success = storage_service.delete_profile(created.userId)
    assert success is True
    
    retrieved = storage_service.get_profile(created.userId)
    assert retrieved is None


def test_delete_nonexistent_profile(storage_service):
    """Test deleting a non-existent profile."""
    success = storage_service.delete_profile("nonexistent-id")
    assert success is False


def test_recognize_user(storage_service, sample_profile_request):
    """Test recognizing user by phone number."""
    created = storage_service.create_profile(sample_profile_request)
    
    recognized = storage_service.recognize_user("+919876543210")
    
    assert recognized is not None
    assert recognized.userId == created.userId
    assert recognized.personalInfo.phoneNumber == "+919876543210"


def test_recognize_nonexistent_user(storage_service):
    """Test recognizing non-existent user."""
    recognized = storage_service.recognize_user("+919999999999")
    assert recognized is None


def test_profile_persistence(temp_storage, sample_profile_request):
    """Test that profiles persist across service instances."""
    # Create profile with first service instance
    service1 = UserProfileStorage(storage_path=temp_storage)
    key = service1.encryption_service.get_key_base64()
    profile = service1.create_profile(sample_profile_request)
    user_id = profile.userId
    
    # Create new service instance with same key and retrieve profile
    service2 = UserProfileStorage(storage_path=temp_storage, encryption_key=key)
    retrieved = service2.get_profile(user_id)
    
    assert retrieved is not None
    assert retrieved.userId == user_id
    assert retrieved.personalInfo.name == "Ramesh Kumar"


def test_encryption_key_consistency(temp_storage, sample_profile_request):
    """Test that same encryption key can decrypt data."""
    # Create profile with first service
    service1 = UserProfileStorage(storage_path=temp_storage)
    key = service1.encryption_service.get_key_base64()
    profile = service1.create_profile(sample_profile_request)
    user_id = profile.userId
    
    # Create new service with same key
    service2 = UserProfileStorage(storage_path=temp_storage, encryption_key=key)
    retrieved = service2.get_profile(user_id)
    
    assert retrieved is not None
    assert retrieved.userId == user_id


def test_profile_caching(storage_service, sample_profile_request):
    """Test that profiles are cached after first retrieval."""
    profile = storage_service.create_profile(sample_profile_request)
    user_id = profile.userId
    
    # First retrieval
    retrieved1 = storage_service.get_profile(user_id)
    
    # Second retrieval (should use cache)
    retrieved2 = storage_service.get_profile(user_id)
    
    assert retrieved1 is retrieved2  # Same object reference


def test_multiple_profiles(storage_service):
    """Test creating and managing multiple profiles."""
    profiles = []
    
    for i in range(3):
        request = CreateUserProfileRequest(
            personalInfo=PersonalInfo(
                name=f"User {i}",
                age=30 + i,
                gender=Gender.MALE,
                phoneNumber=f"+9198765432{i}0"
            ),
            demographics=Demographics(
                state="Test State",
                district="Test District",
                block="Test Block",
                village="Test Village",
                caste=CasteCategory.GENERAL,
                religion=Religion.HINDU,
                familySize=4
            ),
            economic=Economic(
                annualIncome=50000.0,
                occupation=Occupation.FARMER,
                landOwnership=LandDetails(owned=True, areaInAcres=2.0, irrigated=False),
                bankAccount=BankDetails(hasAccount=True)
            ),
            preferences=Preferences(
                preferredLanguage=LanguageCode.HI,
                preferredDialect=DialectCode.STANDARD,
                communicationMode=CommunicationMode.VOICE
            )
        )
        profiles.append(storage_service.create_profile(request))
    
    # Verify all profiles can be retrieved
    for profile in profiles:
        retrieved = storage_service.get_profile(profile.userId)
        assert retrieved is not None
        assert retrieved.userId == profile.userId
