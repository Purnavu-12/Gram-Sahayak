"""
Tests for voice-based profile updates.
"""

import pytest
from datetime import datetime

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
    BankDetails
)
from voice_updates import VoiceUpdateParser


@pytest.fixture
def sample_profile():
    """Create a sample user profile for testing."""
    return UserProfile(
        userId="test-user-123",
        personalInfo=PersonalInfo(
            name="Ram Kumar",
            age=35,
            gender=Gender.MALE,
            phoneNumber="+919876543210"
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
            annualIncome=50000.0,
            occupation=Occupation.FARMER,
            landOwnership=LandDetails(owned=True, areaInAcres=2.5, irrigated=True),
            bankAccount=BankDetails(hasAccount=True)
        ),
        preferences=Preferences(
            preferredLanguage=LanguageCode.HI,
            preferredDialect=DialectCode.REGIONAL,
            communicationMode=CommunicationMode.VOICE
        ),
        createdAt=datetime.utcnow(),
        updatedAt=datetime.utcnow()
    )


@pytest.fixture
def parser():
    """Create a voice update parser."""
    return VoiceUpdateParser()


def test_parse_name_update(parser, sample_profile):
    """Test parsing name updates from natural language."""
    updates = parser.parse_update("My name is Shyam Singh", sample_profile)
    assert 'name' in updates
    assert updates['name'] == "Shyam Singh"


def test_parse_age_update(parser, sample_profile):
    """Test parsing age updates from natural language."""
    updates = parser.parse_update("I am 40 years old", sample_profile)
    assert 'age' in updates
    assert updates['age'] == 40


def test_parse_gender_update(parser, sample_profile):
    """Test parsing gender updates from natural language."""
    updates = parser.parse_update("I am female", sample_profile)
    assert 'gender' in updates
    assert updates['gender'] == Gender.FEMALE


def test_parse_phone_update(parser, sample_profile):
    """Test parsing phone number updates from natural language."""
    updates = parser.parse_update("My phone number is +919123456789", sample_profile)
    assert 'phoneNumber' in updates
    assert updates['phoneNumber'] == "+919123456789"


def test_parse_occupation_update(parser, sample_profile):
    """Test parsing occupation updates from natural language."""
    updates = parser.parse_update("I work as a daily wage worker", sample_profile)
    assert 'occupation' in updates
    assert updates['occupation'] == Occupation.DAILY_WAGE_WORKER


def test_parse_income_update(parser, sample_profile):
    """Test parsing income updates from natural language."""
    updates = parser.parse_update("My annual income is Rs. 75,000", sample_profile)
    assert 'annualIncome' in updates
    assert updates['annualIncome'] == 75000.0


def test_parse_caste_update(parser, sample_profile):
    """Test parsing caste category updates from natural language."""
    updates = parser.parse_update("I belong to SC category", sample_profile)
    assert 'caste' in updates
    assert updates['caste'] == CasteCategory.SC


def test_parse_language_update(parser, sample_profile):
    """Test parsing language preference updates from natural language."""
    updates = parser.parse_update("I prefer to speak in Bengali", sample_profile)
    assert 'preferredLanguage' in updates
    assert updates['preferredLanguage'] == LanguageCode.BN


def test_parse_location_update(parser, sample_profile):
    """Test parsing location updates from natural language."""
    updates = parser.parse_update("I am from village Sitapur in Gaya district", sample_profile)
    assert 'village' in updates
    assert updates['village'] == "Sitapur"
    assert 'district' in updates
    assert updates['district'] == "Gaya"


def test_parse_family_size_update(parser, sample_profile):
    """Test parsing family size updates from natural language."""
    updates = parser.parse_update("My family has 7 members", sample_profile)
    assert 'familySize' in updates
    assert updates['familySize'] == 7


def test_parse_land_ownership_update(parser, sample_profile):
    """Test parsing land ownership updates from natural language."""
    updates = parser.parse_update("I own land of 5 acres", sample_profile)
    assert 'landOwned' in updates
    assert updates['landOwned'] is True
    assert 'landArea' in updates
    assert updates['landArea'] == 5.0


def test_parse_no_land_update(parser, sample_profile):
    """Test parsing no land ownership updates from natural language."""
    updates = parser.parse_update("I don't have land", sample_profile)
    assert 'landOwned' in updates
    assert updates['landOwned'] is False


def test_parse_multiple_updates(parser, sample_profile):
    """Test parsing multiple updates in one statement."""
    updates = parser.parse_update(
        "My name is Geeta Devi and I am 28 years old. I work as a farmer and my income is 60000",
        sample_profile
    )
    assert 'name' in updates
    assert updates['name'] == "Geeta Devi"
    assert 'age' in updates
    assert updates['age'] == 28
    assert 'occupation' in updates
    assert updates['occupation'] == Occupation.FARMER
    assert 'annualIncome' in updates
    assert updates['annualIncome'] == 60000.0


def test_parse_no_updates(parser, sample_profile):
    """Test parsing when no recognizable updates are present."""
    updates = parser.parse_update("Hello, how are you?", sample_profile)
    assert len(updates) == 0


def test_generate_confirmation_message(parser):
    """Test generating confirmation messages for updates."""
    updates = {
        'name': 'Test User',
        'age': 30,
        'occupation': Occupation.FARMER
    }
    message = parser.generate_confirmation_message(updates)
    assert "Test User" in message
    assert "30" in message
    assert "farmer" in message
    assert "confirm" in message.lower()


def test_generate_confirmation_empty_updates(parser):
    """Test generating confirmation message for empty updates."""
    updates = {}
    message = parser.generate_confirmation_message(updates)
    assert "couldn't understand" in message.lower()


def test_apply_updates_personal_info(parser, sample_profile):
    """Test applying updates to personal info."""
    updates = {
        'name': 'New Name',
        'age': 45,
        'gender': Gender.FEMALE
    }
    updated_profile = parser.apply_updates(sample_profile, updates)
    assert updated_profile.personalInfo.name == 'New Name'
    assert updated_profile.personalInfo.age == 45
    assert updated_profile.personalInfo.gender == Gender.FEMALE


def test_apply_updates_demographics(parser, sample_profile):
    """Test applying updates to demographics."""
    updates = {
        'state': 'West Bengal',
        'district': 'Kolkata',
        'village': 'New Village',
        'caste': CasteCategory.GENERAL,
        'familySize': 8
    }
    updated_profile = parser.apply_updates(sample_profile, updates)
    assert updated_profile.demographics.state == 'West Bengal'
    assert updated_profile.demographics.district == 'Kolkata'
    assert updated_profile.demographics.village == 'New Village'
    assert updated_profile.demographics.caste == CasteCategory.GENERAL
    assert updated_profile.demographics.familySize == 8


def test_apply_updates_economic(parser, sample_profile):
    """Test applying updates to economic info."""
    updates = {
        'occupation': Occupation.SELF_EMPLOYED,
        'annualIncome': 100000.0,
        'landOwned': False
    }
    updated_profile = parser.apply_updates(sample_profile, updates)
    assert updated_profile.economic.occupation == Occupation.SELF_EMPLOYED
    assert updated_profile.economic.annualIncome == 100000.0
    assert updated_profile.economic.landOwnership.owned is False


def test_apply_updates_preferences(parser, sample_profile):
    """Test applying updates to preferences."""
    updates = {
        'preferredLanguage': LanguageCode.TA
    }
    updated_profile = parser.apply_updates(sample_profile, updates)
    assert updated_profile.preferences.preferredLanguage == LanguageCode.TA


def test_apply_updates_timestamp(parser, sample_profile):
    """Test that applying updates updates the timestamp."""
    original_time = sample_profile.updatedAt
    updates = {'name': 'Updated Name'}
    updated_profile = parser.apply_updates(sample_profile, updates)
    assert updated_profile.updatedAt > original_time


def test_parse_complex_sentence(parser, sample_profile):
    """Test parsing complex natural language sentences."""
    updates = parser.parse_update(
        "Hello, my name is Rajesh Kumar and I'm from Patna district in Bihar state. "
        "I am 42 years old and work as a government employee with annual income of Rs 2,50,000",
        sample_profile
    )
    assert updates['name'] == "Rajesh Kumar"
    assert updates['district'] == "Patna"
    assert updates['state'] == "Bihar"
    assert updates['age'] == 42
    assert updates['occupation'] == Occupation.GOVERNMENT_EMPLOYEE
    assert updates['annualIncome'] == 250000.0
