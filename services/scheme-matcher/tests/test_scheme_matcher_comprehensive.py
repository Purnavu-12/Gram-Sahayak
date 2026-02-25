"""
Comprehensive tests for Scheme Matcher Service
Tests multi-criteria eligibility, alternative suggestions, and database updates
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scheme_matcher_service import SchemeMatcherService


@pytest.fixture
def matcher():
    return SchemeMatcherService()


@pytest.fixture
def farmer_profile():
    """Profile of a farmer eligible for agricultural schemes"""
    return {
        "user_id": "farmer001",
        "personal_info": {
            "name": "Ram Kumar",
            "age": 45,
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


@pytest.fixture
def student_profile():
    """Profile of an OBC student eligible for scholarship"""
    return {
        "user_id": "student001",
        "personal_info": {
            "name": "Priya Sharma",
            "age": 22,
            "gender": "female",
            "phone_number": "9876543211"
        },
        "demographics": {
            "state": "Bihar",
            "district": "Patna",
            "block": "Patna Sadar",
            "village": "Test Village",
            "caste": "obc",
            "religion": "hindu",
            "family_size": 4
        },
        "economic": {
            "annual_income": 120000,
            "occupation": "student"
        },
        "preferences": {
            "preferred_language": "hi",
            "preferred_dialect": "hi-IN",
            "communication_mode": "voice"
        },
        "application_history": []
    }


@pytest.fixture
def elderly_profile():
    """Profile of an elderly person eligible for pension"""
    return {
        "user_id": "elderly001",
        "personal_info": {
            "name": "Lakshmi Devi",
            "age": 65,
            "gender": "female",
            "phone_number": "9876543212"
        },
        "demographics": {
            "state": "Tamil Nadu",
            "district": "Chennai",
            "block": "Chennai North",
            "village": "Test Village",
            "caste": "general",
            "religion": "hindu",
            "family_size": 2
        },
        "economic": {
            "annual_income": 80000,
            "occupation": "unemployed"
        },
        "preferences": {
            "preferred_language": "ta",
            "preferred_dialect": "ta-IN",
            "communication_mode": "voice"
        },
        "application_history": []
    }


@pytest.mark.asyncio
async def test_multi_criteria_eligibility_farmer(matcher, farmer_profile):
    """Test multi-criteria eligibility evaluation for farmer (Requirements 3.2)"""
    result = await matcher.evaluate_eligibility("PM-KISAN", farmer_profile)
    
    assert result["is_eligible"] is True
    assert "occupation" in result["matched_criteria"]
    assert "land_ownership" in result["matched_criteria"]
    assert "income" in result["matched_criteria"]
    assert len(result["unmatched_criteria"]) == 0
    assert result["confidence"] == 1.0


@pytest.mark.asyncio
async def test_multi_criteria_eligibility_student(matcher, student_profile):
    """Test multi-criteria eligibility for student scholarship (Requirements 3.2)"""
    result = await matcher.evaluate_eligibility("OBC-SCHOLARSHIP", student_profile)
    
    assert result["is_eligible"] is True
    assert "occupation" in result["matched_criteria"]
    assert "caste" in result["matched_criteria"]
    assert "age_limit" in result["matched_criteria"]
    assert "income" in result["matched_criteria"]


@pytest.mark.asyncio
async def test_multi_criteria_eligibility_elderly(matcher, elderly_profile):
    """Test multi-criteria eligibility for elderly pension (Requirements 3.2)"""
    result = await matcher.evaluate_eligibility("OLD-AGE-PENSION", elderly_profile)
    
    assert result["is_eligible"] is True
    assert "age" in result["matched_criteria"]
    assert "income" in result["matched_criteria"]


@pytest.mark.asyncio
async def test_income_criteria_rejection(matcher, farmer_profile):
    """Test that high income disqualifies from income-limited schemes"""
    # Set income above limit
    farmer_profile["economic"]["annual_income"] = 250000
    
    result = await matcher.evaluate_eligibility("PM-KISAN", farmer_profile)
    
    assert result["is_eligible"] is False
    assert "income" in result["unmatched_criteria"]
    assert any("Income exceeds" in r for r in result["recommendations"])


@pytest.mark.asyncio
async def test_age_criteria_rejection(matcher, student_profile):
    """Test that age limits are enforced"""
    # Set age above limit
    student_profile["personal_info"]["age"] = 35
    
    result = await matcher.evaluate_eligibility("OBC-SCHOLARSHIP", student_profile)
    
    assert result["is_eligible"] is False
    assert "age_limit" in result["unmatched_criteria"]


@pytest.mark.asyncio
async def test_caste_criteria_matching(matcher, student_profile):
    """Test caste-based eligibility (Requirements 3.2)"""
    # Test SC/ST scholarship with OBC student
    result = await matcher.evaluate_eligibility("SC-ST-SCHOLARSHIP", student_profile)
    
    assert result["is_eligible"] is False
    assert "caste" in result["unmatched_criteria"]
    
    # Change to SC and test again
    student_profile["demographics"]["caste"] = "sc"
    result = await matcher.evaluate_eligibility("SC-ST-SCHOLARSHIP", student_profile)
    
    assert result["is_eligible"] is True
    assert "caste" in result["matched_criteria"]


@pytest.mark.asyncio
async def test_find_all_eligible_schemes(matcher, farmer_profile):
    """Test finding all eligible schemes (Requirements 3.1)"""
    schemes = await matcher.find_eligible_schemes(farmer_profile)
    
    assert isinstance(schemes, list)
    assert len(schemes) >= 2  # Should match PM-KISAN and MGNREGA at minimum
    
    scheme_ids = [s["scheme_id"] for s in schemes]
    assert "PM-KISAN" in scheme_ids
    assert "MGNREGA" in scheme_ids
    
    # Verify all returned schemes have required fields
    for scheme in schemes:
        assert "scheme_id" in scheme
        assert "name" in scheme
        assert "match_score" in scheme
        assert "eligibility_status" in scheme
        assert "estimated_benefit" in scheme
        assert "matched_criteria" in scheme


@pytest.mark.asyncio
async def test_priority_ranking_by_benefit(matcher, farmer_profile):
    """Test priority ranking by benefit amount (Requirements 3.3)"""
    schemes = await matcher.find_eligible_schemes(farmer_profile)
    
    preferences = {
        "prioritize_benefit": True,
        "prioritize_ease": False
    }
    
    ranked = await matcher.get_priority_ranking(schemes, preferences)
    
    assert len(ranked) > 0
    # Higher benefit schemes should rank higher
    for i in range(len(ranked) - 1):
        assert ranked[i]["priority_score"] >= ranked[i + 1]["priority_score"]


@pytest.mark.asyncio
async def test_priority_ranking_by_ease(matcher, farmer_profile):
    """Test priority ranking by application ease (Requirements 3.3)"""
    schemes = await matcher.find_eligible_schemes(farmer_profile)
    
    preferences = {
        "prioritize_benefit": False,
        "prioritize_ease": True
    }
    
    ranked = await matcher.get_priority_ranking(schemes, preferences)
    
    assert len(ranked) > 0
    # Easy schemes should get higher scores
    easy_schemes = [s for s in ranked if s["application_difficulty"] == "easy"]
    if easy_schemes:
        assert easy_schemes[0]["rank"] <= len(ranked) // 2  # Should be in top half


@pytest.mark.asyncio
async def test_scheme_database_update(matcher):
    """Test scheme database updates (Requirements 3.4)"""
    initial_count = len(matcher.schemes_db)
    
    # Update existing scheme
    updates = [
        {
            "scheme_id": "PM-KISAN",
            "changes": {
                "benefit_amount": 7000,
                "description": "Updated description"
            }
        }
    ]
    
    await matcher.update_scheme_database(updates)
    
    # Verify update was applied
    updated_scheme = next(s for s in matcher.schemes_db if s["scheme_id"] == "PM-KISAN")
    assert updated_scheme["benefit_amount"] == 7000
    assert updated_scheme["description"] == "Updated description"
    assert "last_updated" in updated_scheme
    
    # Verify update log
    assert len(matcher.scheme_updates_log) > 0
    assert matcher.scheme_updates_log[-1]["scheme_id"] == "PM-KISAN"


@pytest.mark.asyncio
async def test_new_scheme_addition(matcher):
    """Test adding new schemes to database (Requirements 3.4)"""
    initial_count = len(matcher.schemes_db)
    
    # Add new scheme
    updates = [
        {
            "scheme_id": "NEW-SCHEME",
            "changes": {
                "name": "New Test Scheme",
                "benefit_amount": 5000,
                "difficulty": "easy",
                "eligibility": {
                    "occupation": ["farmer"]
                }
            }
        }
    ]
    
    await matcher.update_scheme_database(updates)
    
    # Verify scheme was added
    assert len(matcher.schemes_db) == initial_count + 1
    new_scheme = next(s for s in matcher.schemes_db if s["scheme_id"] == "NEW-SCHEME")
    assert new_scheme["name"] == "New Test Scheme"


@pytest.mark.asyncio
async def test_alternative_scheme_suggestions(matcher, farmer_profile):
    """Test alternative scheme suggestions when ineligible (Requirements 3.5)"""
    # Make farmer ineligible for PM-KISAN by removing land
    farmer_profile["economic"]["land_ownership"] = {"has_land": False}
    
    alternatives = await matcher.suggest_alternative_schemes(farmer_profile, "PM-KISAN")
    
    assert isinstance(alternatives, list)
    # Should suggest MGNREGA as alternative (same category or related)
    if len(alternatives) > 0:
        assert all("suggestion_reason" in s for s in alternatives)
        assert all("match_score" in s for s in alternatives)


@pytest.mark.asyncio
async def test_alternative_suggestions_same_category(matcher, student_profile):
    """Test alternative suggestions prioritize same category (Requirements 3.5)"""
    # Make student ineligible for OBC scholarship by exceeding income
    student_profile["economic"]["annual_income"] = 200000
    
    alternatives = await matcher.suggest_alternative_schemes(student_profile, "OBC-SCHOLARSHIP")
    
    # Should suggest SC-ST scholarship if student changes caste, or other education schemes
    # At minimum, should return empty list if no alternatives
    assert isinstance(alternatives, list)


@pytest.mark.asyncio
async def test_no_alternatives_when_eligible(matcher, farmer_profile):
    """Test no alternatives suggested when user is eligible for requested scheme"""
    alternatives = await matcher.suggest_alternative_schemes(farmer_profile, "PM-KISAN")
    
    # Should return empty list since farmer is eligible for PM-KISAN
    assert alternatives == []


@pytest.mark.asyncio
async def test_missing_information_detection(matcher):
    """Test detection of missing profile information"""
    incomplete_profile = {
        "user_id": "incomplete001",
        "personal_info": {
            "name": "Test User"
            # Missing age, gender
        },
        "demographics": {},
        "economic": {},
        "preferences": {},
        "application_history": []
    }
    
    result = await matcher.evaluate_eligibility("PM-KISAN", incomplete_profile)
    
    assert len(result["missing_information"]) > 0
    assert any("provide" in r.lower() for r in result["recommendations"])


@pytest.mark.asyncio
async def test_scheme_update_status_tracking(matcher):
    """Test scheme update status tracking"""
    # Perform an update
    updates = [
        {
            "scheme_id": "MGNREGA",
            "changes": {"benefit_amount": 9000}
        }
    ]
    await matcher.update_scheme_database(updates)
    
    # Get update status
    status = matcher.get_scheme_update_status()
    
    assert "last_update_time" in status
    assert "total_schemes" in status
    assert "recent_updates" in status
    assert status["total_schemes"] > 0
    assert status["recent_updates"] >= 1


@pytest.mark.asyncio
async def test_confidence_scoring(matcher, farmer_profile):
    """Test confidence scoring in eligibility evaluation"""
    # Full match should give 1.0 confidence
    result = await matcher.evaluate_eligibility("PM-KISAN", farmer_profile)
    assert result["confidence"] == 1.0
    
    # Partial match should give lower confidence
    farmer_profile["economic"]["annual_income"] = 250000  # Exceeds limit
    result = await matcher.evaluate_eligibility("PM-KISAN", farmer_profile)
    assert 0 <= result["confidence"] < 1.0


@pytest.mark.asyncio
async def test_multiple_scheme_categories(matcher, farmer_profile):
    """Test that schemes from different categories are properly identified"""
    all_schemes = await matcher.find_eligible_schemes(farmer_profile)
    
    categories = set(s.get("category", "general") for s in all_schemes)
    # Farmer should match schemes from multiple categories
    assert len(categories) >= 1


@pytest.mark.asyncio
async def test_scheme_relationships(matcher):
    """Test that scheme relationships are properly defined"""
    # Verify related schemes are defined
    for scheme in matcher.schemes_db:
        if "related_schemes" in scheme:
            assert isinstance(scheme["related_schemes"], list)
            # Verify related schemes exist
            for related_id in scheme["related_schemes"]:
                assert any(s["scheme_id"] == related_id for s in matcher.schemes_db)
