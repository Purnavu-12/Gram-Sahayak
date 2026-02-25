import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scheme_matcher_service import SchemeMatcherService


@pytest.fixture
def matcher():
    return SchemeMatcherService()


@pytest.fixture
def sample_user_profile():
    return {
        "user_id": "user123",
        "personal_info": {
            "name": "Test User",
            "age": 35,
            "gender": "male",
            "phone_number": "9876543210"
        },
        "demographics": {
            "state": "Uttar Pradesh",
            "district": "Lucknow",
            "block": "Mohanlalganj",
            "village": "Test Village",
            "caste": "obc",
            "religion": "hindu",
            "family_size": 5
        },
        "economic": {
            "annual_income": 150000,
            "occupation": "farmer",
            "land_ownership": {
                "has_land": True,
                "acres": 2.5
            }
        },
        "preferences": {
            "preferred_language": "hi",
            "preferred_dialect": "hi-IN",
            "communication_mode": "voice"
        },
        "application_history": []
    }


@pytest.mark.asyncio
async def test_find_eligible_schemes(matcher, sample_user_profile):
    """Test finding eligible schemes for a user"""
    schemes = await matcher.find_eligible_schemes(sample_user_profile)

    assert isinstance(schemes, list)
    assert len(schemes) > 0
    assert all("scheme_id" in s for s in schemes)
    assert all("eligibility_status" in s for s in schemes)


@pytest.mark.asyncio
async def test_evaluate_eligibility_for_valid_scheme(matcher, sample_user_profile):
    """Test eligibility evaluation for a valid scheme"""
    result = await matcher.evaluate_eligibility("PM-KISAN", sample_user_profile)

    assert result is not None
    assert "is_eligible" in result
    assert "confidence" in result
    assert "matched_criteria" in result
    assert isinstance(result["matched_criteria"], list)


@pytest.mark.asyncio
async def test_evaluate_eligibility_for_invalid_scheme(matcher, sample_user_profile):
    """Test eligibility evaluation for an invalid scheme"""
    result = await matcher.evaluate_eligibility("INVALID-SCHEME", sample_user_profile)

    assert result["is_eligible"] is False
    assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_get_priority_ranking(matcher):
    """Test priority ranking of schemes"""
    schemes = [
        {
            "scheme_id": "SCHEME1",
            "name": "Scheme 1",
            "match_score": 0.8,
            "estimated_benefit": 5000,
            "application_difficulty": "easy"
        },
        {
            "scheme_id": "SCHEME2",
            "name": "Scheme 2",
            "match_score": 0.9,
            "estimated_benefit": 10000,
            "application_difficulty": "medium"
        }
    ]

    preferences = {
        "prioritize_benefit": True,
        "prioritize_ease": False
    }

    ranked = await matcher.get_priority_ranking(schemes, preferences)

    assert isinstance(ranked, list)
    assert len(ranked) == 2
    assert all("rank" in s for s in ranked)
    assert all("priority_score" in s for s in ranked)
    assert ranked[0]["rank"] == 1
    assert ranked[1]["rank"] == 2
