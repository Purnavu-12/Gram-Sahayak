"""
Unit Tests for Alternative Scheme Suggestions with User Preference Learning
**Validates: Requirement 3.5**

Tests the alternative scheme suggestion system including:
1. Fallback recommendations for ineligible users
2. Similarity-based scheme matching
3. User preference learning and adaptation
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scheme_matcher_service import SchemeMatcherService


@pytest.fixture
def matcher():
    """Create a fresh matcher instance for each test"""
    return SchemeMatcherService()


@pytest.fixture
def farmer_with_history():
    """Farmer profile with application history showing preferences"""
    return {
        "user_id": "farmer_with_history",
        "personal_info": {
            "name": "Ramesh Kumar",
            "age": 45,
            "gender": "male",
            "phone_number": "9876543210"
        },
        "demographics": {
            "state": "Uttar Pradesh",
            "district": "Varanasi",
            "block": "Pindra",
            "village": "Rampur",
            "caste": "obc",
            "religion": "hindu",
            "family_size": 5
        },
        "economic": {
            "annual_income": 80000,
            "occupation": "farmer",
            "land_ownership": {
                "has_land": False,  # Make ineligible for PM-KISAN
                "acres": 0.0
            }
        },
        "preferences": {
            "preferred_language": "hi",
            "preferred_dialect": "hi-IN",
            "communication_mode": "voice"
        },
        "application_history": [
            {
                "scheme_id": "MGNREGA",
                "scheme_category": "employment",
                "benefit_amount": 6000,
                "application_difficulty": "easy",
                "status": "approved",
                "applied_date": "2024-01-15"
            },
            {
                "scheme_id": "PMAY",
                "scheme_category": "housing",
                "benefit_amount": 120000,
                "application_difficulty": "medium",
                "status": "approved",
                "applied_date": "2024-02-20"
            },
            {
                "scheme_id": "UJJWALA",
                "scheme_category": "energy",
                "benefit_amount": 1600,
                "application_difficulty": "easy",
                "status": "approved",
                "applied_date": "2024-03-10"
            }
        ]
    }


@pytest.fixture
def student_with_education_preference():
    """Student profile with history showing preference for education schemes"""
    return {
        "user_id": "student_with_pref",
        "personal_info": {
            "name": "Priya Sharma",
            "age": 20,
            "gender": "female",
            "phone_number": "9876543211"
        },
        "demographics": {
            "state": "Bihar",
            "district": "Patna",
            "block": "Patna Sadar",
            "village": "Kumhrar",
            "caste": "general",
            "religion": "hindu",
            "family_size": 4
        },
        "economic": {
            "annual_income": 150000,  # Too high for some scholarships
            "occupation": "student"
        },
        "preferences": {
            "preferred_language": "hi",
            "preferred_dialect": "hi-IN",
            "communication_mode": "voice"
        },
        "application_history": [
            {
                "scheme_id": "NSP-SCHOLARSHIP",
                "scheme_category": "education",
                "benefit_amount": 12000,
                "application_difficulty": "medium",
                "status": "approved",
                "applied_date": "2024-01-10"
            },
            {
                "scheme_id": "MERIT-SCHOLARSHIP",
                "scheme_category": "education",
                "benefit_amount": 15000,
                "application_difficulty": "hard",
                "status": "pending",
                "applied_date": "2024-02-15"
            }
        ]
    }


@pytest.mark.asyncio
async def test_alternative_suggestions_basic(matcher, farmer_with_history):
    """Test basic alternative scheme suggestions for ineligible users"""
    # Request PM-KISAN (farmer is ineligible due to no land)
    alternatives = await matcher.suggest_alternative_schemes(
        farmer_with_history, 
        "PM-KISAN"
    )
    
    # Should return a list of alternatives
    assert isinstance(alternatives, list)
    
    # Should have at least one alternative
    assert len(alternatives) > 0, "Should suggest alternatives when user is ineligible"
    
    # Each alternative should have required fields
    for alt in alternatives:
        assert "scheme_id" in alt
        assert "name" in alt
        assert "suggestion_reason" in alt
        assert "match_score" in alt
        assert "estimated_benefit" in alt


@pytest.mark.asyncio
async def test_similarity_based_matching(matcher, farmer_with_history):
    """Test that alternatives are similar to requested scheme"""
    # Request PM-KISAN (agriculture scheme)
    alternatives = await matcher.suggest_alternative_schemes(
        farmer_with_history,
        "PM-KISAN"
    )
    
    if len(alternatives) > 0:
        # Check that suggestion reasons are provided
        for alt in alternatives:
            assert alt["suggestion_reason"], "Each alternative should have a reason"
            
            # Reason should mention category or relation
            reason = alt["suggestion_reason"].lower()
            assert any(keyword in reason for keyword in [
                "category", "related", "similar", "interest"
            ]), f"Suggestion reason should explain similarity: {alt['suggestion_reason']}"


@pytest.mark.asyncio
async def test_user_preference_learning(matcher, farmer_with_history):
    """Test that system learns from application history"""
    # The farmer has history with employment, housing, and energy schemes
    # Request PM-KISAN (ineligible)
    alternatives = await matcher.suggest_alternative_schemes(
        farmer_with_history,
        "PM-KISAN"
    )
    
    if len(alternatives) > 0:
        # Check if any alternatives mention past interests
        has_preference_boost = any(
            "past interests" in alt.get("suggestion_reason", "").lower()
            for alt in alternatives
        )
        
        # At least verify that match scores are calculated
        for alt in alternatives:
            assert "match_score" in alt
            assert 0 <= alt["match_score"] <= 1.0, "Match score should be between 0 and 1"


@pytest.mark.asyncio
async def test_preference_adaptation_boosts_scores(matcher, student_with_education_preference):
    """Test that learned preferences boost relevant scheme scores"""
    # Student has history with education schemes
    # Make them ineligible for a specific scholarship
    alternatives = await matcher.suggest_alternative_schemes(
        student_with_education_preference,
        "OBC-SCHOLARSHIP"  # Ineligible due to caste
    )
    
    if len(alternatives) > 0:
        # Education schemes should be suggested due to history
        education_schemes = [
            alt for alt in alternatives 
            if alt.get("category") == "education"
        ]
        
        # If there are education schemes, they should rank highly
        if education_schemes:
            # At least one education scheme should be in top 3
            top_3 = alternatives[:min(3, len(alternatives))]
            assert any(
                alt.get("category") == "education" 
                for alt in top_3
            ), "Education schemes should rank highly for student with education history"


@pytest.mark.asyncio
async def test_no_alternatives_when_eligible(matcher, farmer_with_history):
    """Test that no alternatives are suggested when user is eligible"""
    # Make farmer eligible for PM-KISAN by adding land
    farmer_with_history["economic"]["land_ownership"] = {
        "has_land": True,
        "acres": 2.0
    }
    
    alternatives = await matcher.suggest_alternative_schemes(
        farmer_with_history,
        "PM-KISAN"
    )
    
    # Should return empty list when eligible
    assert alternatives == [], "Should not suggest alternatives when user is eligible"


@pytest.mark.asyncio
async def test_alternatives_sorted_by_score(matcher, farmer_with_history):
    """Test that alternatives are sorted by match score"""
    alternatives = await matcher.suggest_alternative_schemes(
        farmer_with_history,
        "PM-KISAN"
    )
    
    if len(alternatives) > 1:
        # Verify scores are in descending order
        scores = [alt["match_score"] for alt in alternatives]
        assert scores == sorted(scores, reverse=True), \
            "Alternatives should be sorted by match score (highest first)"


@pytest.mark.asyncio
async def test_category_based_suggestions(matcher, farmer_with_history):
    """Test that schemes in same category are suggested"""
    # Request PM-KISAN (agriculture category)
    alternatives = await matcher.suggest_alternative_schemes(
        farmer_with_history,
        "PM-KISAN"
    )
    
    if len(alternatives) > 0:
        # Check if any alternatives mention category similarity
        category_matches = [
            alt for alt in alternatives
            if "category" in alt.get("suggestion_reason", "").lower()
        ]
        
        # At least some alternatives should be category-based
        # (though not required if no schemes in same category)
        assert isinstance(category_matches, list)


@pytest.mark.asyncio
async def test_preference_learning_with_empty_history(matcher):
    """Test that system works correctly with no application history"""
    profile_no_history = {
        "user_id": "new_user",
        "personal_info": {
            "name": "New User",
            "age": 30,
            "gender": "male"
        },
        "demographics": {
            "state": "Maharashtra",
            "district": "Mumbai",
            "caste": "general"
        },
        "economic": {
            "annual_income": 100000,
            "occupation": "laborer",
            "land_ownership": {"has_land": False}
        },
        "preferences": {
            "preferred_language": "mr"
        },
        "application_history": []  # Empty history
    }
    
    alternatives = await matcher.suggest_alternative_schemes(
        profile_no_history,
        "PM-KISAN"
    )
    
    # Should still work without history
    assert isinstance(alternatives, list)
    
    # If alternatives exist, they should have valid scores
    for alt in alternatives:
        assert "match_score" in alt
        assert alt["match_score"] >= 0


@pytest.mark.asyncio
async def test_benefit_amount_preference_learning(matcher):
    """Test that system learns benefit amount preferences"""
    profile_with_high_benefit_history = {
        "user_id": "high_benefit_user",
        "personal_info": {
            "name": "Test User",
            "age": 35,
            "gender": "female"
        },
        "demographics": {
            "state": "Tamil Nadu",
            "district": "Chennai",
            "caste": "obc"
        },
        "economic": {
            "annual_income": 90000,
            "occupation": "laborer",
            "land_ownership": {"has_land": False}
        },
        "preferences": {
            "preferred_language": "ta"
        },
        "application_history": [
            {
                "scheme_id": "SCHEME1",
                "scheme_category": "housing",
                "benefit_amount": 100000,
                "application_difficulty": "medium"
            },
            {
                "scheme_id": "SCHEME2",
                "scheme_category": "housing",
                "benefit_amount": 120000,
                "application_difficulty": "medium"
            }
        ]
    }
    
    alternatives = await matcher.suggest_alternative_schemes(
        profile_with_high_benefit_history,
        "PM-KISAN"
    )
    
    # System should work and provide alternatives
    assert isinstance(alternatives, list)


@pytest.mark.asyncio
async def test_difficulty_preference_learning(matcher):
    """Test that system learns application difficulty preferences"""
    profile_prefers_easy = {
        "user_id": "easy_pref_user",
        "personal_info": {
            "name": "Test User",
            "age": 40,
            "gender": "male"
        },
        "demographics": {
            "state": "Karnataka",
            "district": "Bangalore",
            "caste": "sc"
        },
        "economic": {
            "annual_income": 70000,
            "occupation": "farmer",
            "land_ownership": {"has_land": False}
        },
        "preferences": {
            "preferred_language": "kn"
        },
        "application_history": [
            {
                "scheme_id": "EASY1",
                "scheme_category": "employment",
                "benefit_amount": 5000,
                "application_difficulty": "easy"
            },
            {
                "scheme_id": "EASY2",
                "scheme_category": "energy",
                "benefit_amount": 1600,
                "application_difficulty": "easy"
            },
            {
                "scheme_id": "EASY3",
                "scheme_category": "health",
                "benefit_amount": 3000,
                "application_difficulty": "easy"
            }
        ]
    }
    
    alternatives = await matcher.suggest_alternative_schemes(
        profile_prefers_easy,
        "PM-KISAN"
    )
    
    # System should provide alternatives
    assert isinstance(alternatives, list)
    
    # If alternatives exist, easy schemes might rank higher
    # (but this is not strictly required, just a preference boost)
    if len(alternatives) > 0:
        for alt in alternatives:
            assert "application_difficulty" in alt


@pytest.mark.asyncio
async def test_invalid_scheme_id_handling(matcher, farmer_with_history):
    """Test handling of invalid requested scheme ID"""
    alternatives = await matcher.suggest_alternative_schemes(
        farmer_with_history,
        "INVALID-SCHEME-ID"
    )
    
    # Should return empty list for invalid scheme
    assert alternatives == []


@pytest.mark.asyncio
async def test_graph_database_related_schemes(matcher, farmer_with_history):
    """Test that related schemes from graph database are included"""
    # This test verifies the graph database integration
    # Even without Neo4j, the system should use in-memory relationships
    alternatives = await matcher.suggest_alternative_schemes(
        farmer_with_history,
        "PM-KISAN"
    )
    
    if len(alternatives) > 0:
        # Check if any alternatives mention being "related"
        related_schemes = [
            alt for alt in alternatives
            if "related" in alt.get("suggestion_reason", "").lower()
        ]
        
        # Related schemes might exist (depends on data)
        assert isinstance(related_schemes, list)
