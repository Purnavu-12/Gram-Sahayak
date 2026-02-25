"""
Tests for family member profile management.
"""

import pytest
import tempfile
import shutil
from datetime import datetime

from models import (
    CreateFamilyMemberRequest,
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
    BankDetails
)
from family_manager import FamilyManager
from encryption import EncryptionService


@pytest.fixture
def temp_storage():
    """Create a temporary storage directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def encryption_service():
    """Create an encryption service for testing."""
    return EncryptionService()


@pytest.fixture
def family_manager(temp_storage, encryption_service):
    """Create a family manager with temporary storage."""
    return FamilyManager(
        storage_path=temp_storage,
        encryption_key=encryption_service.get_key_base64()
    )


@pytest.fixture
def sample_member_request():
    """Create a sample family member creation request."""
    return CreateFamilyMemberRequest(
        primaryUserId="primary-user-123",
        relationship="son",
        personalInfo=PersonalInfo(
            name="Rahul Kumar",
            age=18,
            gender=Gender.MALE,
            phoneNumber="+919876543211"
        ),
        demographics=Demographics(
            state="Bihar",
            district="Patna",
            block="Danapur",
            village="Rampur",
            caste=CasteCategory.OBC,
            religion=Religion.HINDU,
            familySize=5
        ),
        economic=Economic(
            annualIncome=0.0,
            occupation=Occupation.STUDENT,
            landOwnership=LandDetails(owned=False, areaInAcres=0.0, irrigated=False),
            bankAccount=BankDetails(hasAccount=False)
        ),
        preferences=Preferences(
            preferredLanguage=LanguageCode.HI,
            preferredDialect=DialectCode.REGIONAL,
            communicationMode=CommunicationMode.VOICE
        )
    )


def test_create_family_member(family_manager, sample_member_request):
    """Test creating a family member profile."""
    member = family_manager.create_family_member(sample_member_request)
    
    assert member.memberId is not None
    assert member.primaryUserId == sample_member_request.primaryUserId
    assert member.relationship == sample_member_request.relationship
    assert member.personalInfo.name == sample_member_request.personalInfo.name
    assert member.createdAt is not None
    assert member.updatedAt is not None


def test_get_family_member(family_manager, sample_member_request):
    """Test retrieving a family member profile."""
    # Create member
    created = family_manager.create_family_member(sample_member_request)
    
    # Retrieve member
    retrieved = family_manager.get_family_member(created.memberId)
    
    assert retrieved is not None
    assert retrieved.memberId == created.memberId
    assert retrieved.personalInfo.name == created.personalInfo.name


def test_get_family_member_not_found(family_manager):
    """Test retrieving a non-existent family member."""
    member = family_manager.get_family_member("non-existent-id")
    assert member is None


def test_get_family_members(family_manager, sample_member_request):
    """Test retrieving all family members for a primary user."""
    primary_user_id = "primary-user-456"
    
    # Create multiple family members
    for i, relationship in enumerate(["son", "daughter", "wife"]):
        request = CreateFamilyMemberRequest(
            primaryUserId=primary_user_id,
            relationship=relationship,
            personalInfo=PersonalInfo(
                name=f"Member {i}",
                age=20 + i,
                gender=Gender.MALE if i == 0 else Gender.FEMALE,
                phoneNumber=f"+9198765432{i:02d}"
            ),
            demographics=sample_member_request.demographics,
            economic=sample_member_request.economic,
            preferences=sample_member_request.preferences
        )
        family_manager.create_family_member(request)
    
    # Retrieve all members
    members = family_manager.get_family_members(primary_user_id)
    
    assert len(members) == 3
    assert all(m.primaryUserId == primary_user_id for m in members)
    relationships = [m.relationship for m in members]
    assert "son" in relationships
    assert "daughter" in relationships
    assert "wife" in relationships


def test_get_family_members_empty(family_manager):
    """Test retrieving family members when none exist."""
    members = family_manager.get_family_members("no-members-user")
    assert len(members) == 0


def test_update_family_member(family_manager, sample_member_request):
    """Test updating a family member profile."""
    # Create member
    member = family_manager.create_family_member(sample_member_request)
    
    # Update personal info
    new_personal_info = PersonalInfo(
        name="Updated Name",
        age=19,
        gender=Gender.MALE,
        phoneNumber="+919999999999"
    )
    
    updated = family_manager.update_family_member(
        member_id=member.memberId,
        personal_info=new_personal_info
    )
    
    assert updated is not None
    assert updated.personalInfo.name == "Updated Name"
    assert updated.personalInfo.age == 19
    assert updated.personalInfo.phoneNumber == "+919999999999"
    assert updated.updatedAt >= member.updatedAt


def test_update_family_member_not_found(family_manager):
    """Test updating a non-existent family member."""
    new_personal_info = PersonalInfo(
        name="Test",
        age=20,
        gender=Gender.MALE,
        phoneNumber="+919876543210"
    )
    
    updated = family_manager.update_family_member(
        member_id="non-existent-id",
        personal_info=new_personal_info
    )
    
    assert updated is None


def test_update_family_member_partial(family_manager, sample_member_request):
    """Test partial update of family member (only some fields)."""
    # Create member
    member = family_manager.create_family_member(sample_member_request)
    original_name = member.personalInfo.name
    
    # Update only preferences
    new_preferences = Preferences(
        preferredLanguage=LanguageCode.BN,
        preferredDialect=DialectCode.STANDARD,
        communicationMode=CommunicationMode.TEXT
    )
    
    updated = family_manager.update_family_member(
        member_id=member.memberId,
        preferences=new_preferences
    )
    
    # Name should remain unchanged
    assert updated.personalInfo.name == original_name
    # Preferences should be updated
    assert updated.preferences.preferredLanguage == LanguageCode.BN
    assert updated.preferences.communicationMode == CommunicationMode.TEXT


def test_delete_family_member(family_manager, sample_member_request):
    """Test deleting a family member profile."""
    # Create member
    member = family_manager.create_family_member(sample_member_request)
    
    # Delete member
    success = family_manager.delete_family_member(member.memberId)
    
    assert success is True
    
    # Verify member is deleted
    retrieved = family_manager.get_family_member(member.memberId)
    assert retrieved is None


def test_delete_family_member_not_found(family_manager):
    """Test deleting a non-existent family member."""
    success = family_manager.delete_family_member("non-existent-id")
    assert success is False


def test_delete_all_family_members(family_manager, sample_member_request):
    """Test deleting all family members for a primary user."""
    primary_user_id = "delete-all-user"
    
    # Create multiple family members
    for i in range(3):
        request = CreateFamilyMemberRequest(
            primaryUserId=primary_user_id,
            relationship=f"member-{i}",
            personalInfo=PersonalInfo(
                name=f"Member {i}",
                age=20 + i,
                gender=Gender.MALE,
                phoneNumber=f"+9198765432{i:02d}"
            ),
            demographics=sample_member_request.demographics,
            economic=sample_member_request.economic,
            preferences=sample_member_request.preferences
        )
        family_manager.create_family_member(request)
    
    # Delete all members
    count = family_manager.delete_all_family_members(primary_user_id)
    
    assert count == 3
    
    # Verify all members are deleted
    members = family_manager.get_family_members(primary_user_id)
    assert len(members) == 0


def test_delete_all_family_members_empty(family_manager):
    """Test deleting all family members when none exist."""
    count = family_manager.delete_all_family_members("no-members-user")
    assert count == 0


def test_family_member_encryption(family_manager, sample_member_request):
    """Test that family member data is encrypted in storage."""
    # Create member
    member = family_manager.create_family_member(sample_member_request)
    
    # Read raw file content
    member_file = family_manager.storage_path / f"{member.memberId}.enc"
    raw_content = member_file.read_text()
    
    # Verify content is encrypted (not plain JSON)
    assert member.personalInfo.name not in raw_content
    assert member.personalInfo.phoneNumber not in raw_content


def test_family_member_unique_identifiers(family_manager, sample_member_request):
    """Test that each family member gets a unique identifier."""
    # Create multiple members
    member_ids = set()
    
    for i in range(5):
        member = family_manager.create_family_member(sample_member_request)
        member_ids.add(member.memberId)
    
    # All IDs should be unique
    assert len(member_ids) == 5


def test_family_member_separation(family_manager, sample_member_request):
    """Test that family members are properly separated by primary user."""
    # Create members for different primary users
    user1_id = "user-1"
    user2_id = "user-2"
    
    # Create members for user 1
    for i in range(2):
        request = CreateFamilyMemberRequest(
            primaryUserId=user1_id,
            relationship=f"member-{i}",
            personalInfo=PersonalInfo(
                name=f"User1 Member {i}",
                age=20,
                gender=Gender.MALE,
                phoneNumber=f"+9191111111{i:02d}"
            ),
            demographics=sample_member_request.demographics,
            economic=sample_member_request.economic,
            preferences=sample_member_request.preferences
        )
        family_manager.create_family_member(request)
    
    # Create members for user 2
    for i in range(3):
        request = CreateFamilyMemberRequest(
            primaryUserId=user2_id,
            relationship=f"member-{i}",
            personalInfo=PersonalInfo(
                name=f"User2 Member {i}",
                age=25,
                gender=Gender.FEMALE,
                phoneNumber=f"+9192222222{i:02d}"
            ),
            demographics=sample_member_request.demographics,
            economic=sample_member_request.economic,
            preferences=sample_member_request.preferences
        )
        family_manager.create_family_member(request)
    
    # Verify separation
    user1_members = family_manager.get_family_members(user1_id)
    user2_members = family_manager.get_family_members(user2_id)
    
    assert len(user1_members) == 2
    assert len(user2_members) == 3
    assert all("User1" in m.personalInfo.name for m in user1_members)
    assert all("User2" in m.personalInfo.name for m in user2_members)


def test_family_member_caching(family_manager, sample_member_request):
    """Test that family member profiles are cached for performance."""
    # Create member
    member = family_manager.create_family_member(sample_member_request)
    
    # First retrieval (from storage)
    retrieved1 = family_manager.get_family_member(member.memberId)
    
    # Second retrieval (should be from cache)
    retrieved2 = family_manager.get_family_member(member.memberId)
    
    # Both should return the same data
    assert retrieved1.memberId == retrieved2.memberId
    assert retrieved1.personalInfo.name == retrieved2.personalInfo.name
    
    # Verify cache is populated
    assert member.memberId in family_manager._cache
