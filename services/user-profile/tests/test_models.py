"""
Unit tests for data models and validation.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from models import (
    PersonalInfo, Demographics, Economic, Preferences,
    LandDetails, BankDetails, UserProfile,
    Gender, CasteCategory, Religion, Occupation,
    LanguageCode, DialectCode, CommunicationMode
)


def test_personal_info_valid():
    """Test valid personal info creation."""
    info = PersonalInfo(
        name="Ramesh Kumar",
        age=35,
        gender=Gender.MALE,
        phoneNumber="+919876543210",
        aadhaarNumber="123456789012"
    )
    
    assert info.name == "Ramesh Kumar"
    assert info.age == 35
    assert info.gender == Gender.MALE


def test_personal_info_invalid_age():
    """Test personal info with invalid age."""
    with pytest.raises(ValidationError):
        PersonalInfo(
            name="Test",
            age=-5,
            gender=Gender.MALE,
            phoneNumber="+919876543210"
        )


def test_personal_info_invalid_phone():
    """Test personal info with invalid phone number."""
    with pytest.raises(ValidationError):
        PersonalInfo(
            name="Test",
            age=30,
            gender=Gender.MALE,
            phoneNumber="invalid"
        )


def test_personal_info_invalid_aadhaar():
    """Test personal info with invalid Aadhaar number."""
    with pytest.raises(ValidationError):
        PersonalInfo(
            name="Test",
            age=30,
            gender=Gender.MALE,
            phoneNumber="+919876543210",
            aadhaarNumber="123"  # Too short
        )


def test_demographics_valid():
    """Test valid demographics creation."""
    demo = Demographics(
        state="Maharashtra",
        district="Pune",
        block="Haveli",
        village="Khed",
        caste=CasteCategory.OBC,
        religion=Religion.HINDU,
        familySize=5
    )
    
    assert demo.state == "Maharashtra"
    assert demo.familySize == 5


def test_demographics_invalid_family_size():
    """Test demographics with invalid family size."""
    with pytest.raises(ValidationError):
        Demographics(
            state="Maharashtra",
            district="Pune",
            block="Haveli",
            village="Khed",
            caste=CasteCategory.OBC,
            religion=Religion.HINDU,
            familySize=0  # Must be >= 1
        )


def test_land_details_valid():
    """Test valid land details."""
    land = LandDetails(
        owned=True,
        areaInAcres=2.5,
        irrigated=True
    )
    
    assert land.owned is True
    assert land.areaInAcres == 2.5


def test_land_details_negative_area():
    """Test land details with negative area."""
    with pytest.raises(ValidationError):
        LandDetails(
            owned=True,
            areaInAcres=-1.0,
            irrigated=False
        )


def test_bank_details_valid():
    """Test valid bank details."""
    bank = BankDetails(
        hasAccount=True,
        accountNumber="1234567890",
        ifscCode="SBIN0001234",
        bankName="State Bank of India"
    )
    
    assert bank.hasAccount is True
    assert len(bank.ifscCode) == 11


def test_bank_details_invalid_ifsc():
    """Test bank details with invalid IFSC code."""
    with pytest.raises(ValidationError):
        BankDetails(
            hasAccount=True,
            accountNumber="1234567890",
            ifscCode="SHORT",  # Must be 11 characters
            bankName="Test Bank"
        )


def test_economic_valid():
    """Test valid economic information."""
    economic = Economic(
        annualIncome=50000.0,
        occupation=Occupation.FARMER,
        landOwnership=LandDetails(owned=True, areaInAcres=3.0, irrigated=True),
        bankAccount=BankDetails(hasAccount=True)
    )
    
    assert economic.annualIncome == 50000.0
    assert economic.occupation == Occupation.FARMER


def test_preferences_valid():
    """Test valid preferences."""
    prefs = Preferences(
        preferredLanguage=LanguageCode.HI,
        preferredDialect=DialectCode.REGIONAL,
        communicationMode=CommunicationMode.VOICE
    )
    
    assert prefs.preferredLanguage == LanguageCode.HI
    assert prefs.communicationMode == CommunicationMode.VOICE


def test_user_profile_complete():
    """Test complete user profile creation."""
    profile = UserProfile(
        userId="test-123",
        personalInfo=PersonalInfo(
            name="Test User",
            age=30,
            gender=Gender.MALE,
            phoneNumber="+919876543210"
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
            annualIncome=100000.0,
            occupation=Occupation.FARMER,
            landOwnership=LandDetails(owned=True, areaInAcres=2.0, irrigated=False),
            bankAccount=BankDetails(hasAccount=True)
        ),
        preferences=Preferences(
            preferredLanguage=LanguageCode.HI,
            preferredDialect=DialectCode.STANDARD,
            communicationMode=CommunicationMode.VOICE
        ),
        applicationHistory=[],
        createdAt=datetime.utcnow(),
        updatedAt=datetime.utcnow()
    )
    
    assert profile.userId == "test-123"
    assert profile.personalInfo.name == "Test User"
    assert len(profile.applicationHistory) == 0
