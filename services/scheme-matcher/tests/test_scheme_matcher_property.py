"""
Property-Based Tests for Scheme Matcher Service
**Validates: Requirements 3.1, 3.2, 3.3**

Property 6: Comprehensive Scheme Matching
For any user profile with demographic information, the Scheme_Matcher should:
1. Identify all eligible schemes
2. Evaluate them against multiple criteria (income, caste, age, gender, occupation, location)
3. Rank them by benefit and ease of application
"""
import pytest
import sys
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scheme_matcher_service import SchemeMatcherService


# Custom strategies for generating valid Indian demographic data
@st.composite
def user_profile_strategy(draw):
    """Generate random but valid user profiles for property testing"""
    
    # Personal information
    age = draw(st.integers(min_value=1, max_value=100))
    gender = draw(st.sampled_from(["male", "female", "other"]))
    
    # Demographics
    states = ["Uttar Pradesh", "Bihar", "Maharashtra", "Tamil Nadu", "Karnataka", "West Bengal"]
    caste = draw(st.sampled_from(["general", "obc", "sc", "st"]))
    
    # Economic information
    annual_income = draw(st.integers(min_value=0, max_value=500000))
    occupation = draw(st.sampled_from(["farmer", "laborer", "student", "unemployed", "teacher", "shopkeeper"]))
    has_land = draw(st.booleans())
    
    # Marital status
    marital_status = draw(st.sampled_from(["single", "married", "widow", "widower", "divorced"]))
    
    return {
        "user_id": f"test_user_{draw(st.integers(min_value=1000, max_value=9999))}",
        "personal_info": {
            "name": f"Test User {draw(st.integers(min_value=1, max_value=999))}",
            "age": age,
            "gender": gender,
            "phone_number": f"98765{draw(st.integers(min_value=10000, max_value=99999))}",
            "marital_status": marital_status
        },
        "demographics": {
            "state": draw(st.sampled_from(states)),
            "district": "Test District",
            "block": "Test Block",
            "village": "Test Village",
            "caste": caste,
            "religion": draw(st.sampled_from(["hindu", "muslim", "christian", "sikh", "buddhist", "jain", "other"])),
            "family_size": draw(st.integers(min_value=1, max_value=15))
        },
        "economic": {
            "annual_income": annual_income,
            "occupation": occupation,
            "land_ownership": {
                "has_land": has_land,
                "acres": draw(st.floats(min_value=0.0, max_value=50.0)) if has_land else 0.0
            }
        },
        "preferences": {
            "preferred_language": draw(st.sampled_from(["hi", "en", "ta", "te", "bn", "mr"])),
            "preferred_dialect": "hi-IN",
            "communication_mode": "voice"
        },
        "application_history": []
    }


@pytest.fixture
def matcher():
    """Create a fresh matcher instance for each test"""
    return SchemeMatcherService()


@pytest.mark.asyncio
@given(profile=user_profile_strategy())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_comprehensive_scheme_matching(profile: Dict[str, Any]):
    """
    **Feature: gram-sahayak, Property 6: Comprehensive Scheme Matching**
    **Validates: Requirements 3.1, 3.2, 3.3**
    
    Property: For any user profile with demographic information, the Scheme_Matcher should:
    1. Identify all eligible schemes (Requirement 3.1)
    2. Evaluate them against multiple criteria: income, caste, age, gender, occupation, location (Requirement 3.2)
    3. Rank them by benefit and ease of application (Requirement 3.3)
    """
    matcher = SchemeMatcherService()
    
    try:
        # 1. Test that scheme matching completes successfully for any valid profile
        eligible_schemes = await matcher.find_eligible_schemes(profile)
        
        # Property 1: Result should always be a list
        assert isinstance(eligible_schemes, list), "find_eligible_schemes must return a list"
        
        # Property 2: All returned schemes must have required fields
        for scheme in eligible_schemes:
            assert "scheme_id" in scheme, "Each scheme must have scheme_id"
            assert "name" in scheme, "Each scheme must have name"
            assert "match_score" in scheme, "Each scheme must have match_score"
            assert "eligibility_status" in scheme, "Each scheme must have eligibility_status"
            assert "estimated_benefit" in scheme, "Each scheme must have estimated_benefit"
            assert "application_difficulty" in scheme, "Each scheme must have application_difficulty"
            assert "matched_criteria" in scheme, "Each scheme must have matched_criteria"
            
            # Property 3: Match score should be between 0 and 1 (or higher with bonuses)
            assert scheme["match_score"] >= 0, "Match score cannot be negative"
            
            # Property 4: Eligibility status should be "eligible" for returned schemes
            assert scheme["eligibility_status"] == "eligible", "Only eligible schemes should be returned"
            
            # Property 5: Matched criteria should be a non-empty list for eligible schemes
            assert isinstance(scheme["matched_criteria"], list), "Matched criteria must be a list"
            assert len(scheme["matched_criteria"]) > 0, "Eligible schemes must have at least one matched criterion"
        
        # 2. Test multi-criteria evaluation (Requirement 3.2)
        # For each eligible scheme, verify the evaluation was comprehensive
        for scheme in eligible_schemes:
            evaluation = await matcher.evaluate_eligibility(scheme["scheme_id"], profile)
            
            # Property 6: Evaluation must return required fields
            assert "is_eligible" in evaluation, "Evaluation must include is_eligible"
            assert "confidence" in evaluation, "Evaluation must include confidence"
            assert "matched_criteria" in evaluation, "Evaluation must include matched_criteria"
            assert "unmatched_criteria" in evaluation, "Evaluation must include unmatched_criteria"
            assert "missing_information" in evaluation, "Evaluation must include missing_information"
            
            # Property 7: If scheme is in eligible list, evaluation should confirm eligibility
            assert evaluation["is_eligible"] is True, f"Scheme {scheme['scheme_id']} should be eligible"
            
            # Property 8: Confidence should be between 0 and 1
            assert 0 <= evaluation["confidence"] <= 1, "Confidence must be between 0 and 1"
            
            # Property 9: No unmatched criteria for eligible schemes
            assert len(evaluation["unmatched_criteria"]) == 0, "Eligible schemes should have no unmatched criteria"
            
            # Property 10: No missing information for eligible schemes
            assert len(evaluation["missing_information"]) == 0, "Eligible schemes should have no missing information"
        
        # 3. Test ranking by benefit and ease (Requirement 3.3)
        if len(eligible_schemes) > 0:
            # Test ranking by benefit
            preferences_benefit = {
                "prioritize_benefit": True,
                "prioritize_ease": False
            }
            ranked_by_benefit = await matcher.get_priority_ranking(eligible_schemes, preferences_benefit)
            
            # Property 11: Ranked list should have same length as input
            assert len(ranked_by_benefit) == len(eligible_schemes), "Ranking should not change number of schemes"
            
            # Property 12: All schemes should have priority_score and rank
            for scheme in ranked_by_benefit:
                assert "priority_score" in scheme, "Ranked schemes must have priority_score"
                assert "rank" in scheme, "Ranked schemes must have rank"
            
            # Property 13: Ranks should be sequential from 1 to n
            ranks = [s["rank"] for s in ranked_by_benefit]
            assert ranks == list(range(1, len(ranked_by_benefit) + 1)), "Ranks must be sequential"
            
            # Property 14: Priority scores should be in descending order
            priority_scores = [s["priority_score"] for s in ranked_by_benefit]
            assert priority_scores == sorted(priority_scores, reverse=True), "Priority scores must be descending"
            
            # Test ranking by ease
            preferences_ease = {
                "prioritize_benefit": False,
                "prioritize_ease": True
            }
            ranked_by_ease = await matcher.get_priority_ranking(eligible_schemes, preferences_ease)
            
            # Property 15: Ease ranking should also produce valid results
            assert len(ranked_by_ease) == len(eligible_schemes), "Ease ranking should not change number of schemes"
            ease_scores = [s["priority_score"] for s in ranked_by_ease]
            assert ease_scores == sorted(ease_scores, reverse=True), "Ease priority scores must be descending"
            
            # Property 16: Easy schemes should rank higher when prioritizing ease
            easy_schemes_in_ease_ranking = [s for s in ranked_by_ease if s["application_difficulty"] == "easy"]
            if easy_schemes_in_ease_ranking:
                # At least one easy scheme should be in top half
                top_half_size = len(ranked_by_ease) // 2 + 1
                top_half_schemes = ranked_by_ease[:top_half_size]
                assert any(s["application_difficulty"] == "easy" for s in top_half_schemes), \
                    "Easy schemes should rank higher when prioritizing ease"
        
        # 4. Test consistency: re-evaluating should give same results
        if len(eligible_schemes) > 0:
            first_scheme = eligible_schemes[0]
            eval1 = await matcher.evaluate_eligibility(first_scheme["scheme_id"], profile)
            eval2 = await matcher.evaluate_eligibility(first_scheme["scheme_id"], profile)
            
            # Property 17: Evaluation should be deterministic
            assert eval1["is_eligible"] == eval2["is_eligible"], "Eligibility evaluation must be deterministic"
            assert eval1["confidence"] == eval2["confidence"], "Confidence scoring must be deterministic"
            assert set(eval1["matched_criteria"]) == set(eval2["matched_criteria"]), \
                "Matched criteria must be deterministic"
        
        # 5. Test that all schemes in database are considered
        # Get all schemes from database
        all_scheme_ids = {s["scheme_id"] for s in matcher.schemes_db}
        
        # For each scheme, verify it was properly evaluated
        for scheme_id in all_scheme_ids:
            evaluation = await matcher.evaluate_eligibility(scheme_id, profile)
            
            # Property 18: Every scheme must be evaluable
            assert evaluation is not None, f"Scheme {scheme_id} must be evaluable"
            assert "is_eligible" in evaluation, f"Scheme {scheme_id} evaluation must include is_eligible"
            
            # Property 19: If scheme is eligible, it should be in the eligible list
            if evaluation["is_eligible"]:
                assert any(s["scheme_id"] == scheme_id for s in eligible_schemes), \
                    f"Eligible scheme {scheme_id} must be in find_eligible_schemes result"
        
        # Property 20: Comprehensive criteria evaluation
        # Verify that the system checks all relevant criteria types
        criteria_types_checked = set()
        for scheme in eligible_schemes:
            evaluation = await matcher.evaluate_eligibility(scheme["scheme_id"], profile)
            criteria_types_checked.update(evaluation["matched_criteria"])
        
        # If any schemes were found, at least some criteria should have been checked
        if len(eligible_schemes) > 0:
            # The system should check various criteria types (income, age, occupation, etc.)
            # At minimum, occupation or income should be checked for most schemes
            possible_criteria = {"income", "age", "occupation", "caste", "gender", "location", 
                               "land_ownership", "marital_status", "age_limit"}
            assert len(criteria_types_checked.intersection(possible_criteria)) > 0, \
                "System must evaluate standard eligibility criteria"
    
    finally:
        # Clean up
        await matcher.close()


@pytest.mark.asyncio
@given(profile=user_profile_strategy())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_multi_criteria_evaluation_completeness(profile: Dict[str, Any]):
    """
    **Feature: gram-sahayak, Property 6: Comprehensive Scheme Matching - Multi-Criteria Evaluation**
    **Validates: Requirement 3.2**
    
    Property: For any user profile, eligibility evaluation must consider all applicable criteria:
    income, caste, age, gender, occupation, and location
    """
    matcher = SchemeMatcherService()
    
    try:
        # Get all schemes
        all_schemes = matcher.schemes_db
        
        for scheme in all_schemes:
            evaluation = await matcher.evaluate_eligibility(scheme["scheme_id"], profile)
            
            # Property 1: Evaluation must check all criteria defined in scheme
            scheme_criteria = scheme.get("eligibility", {})
            
            # For each criterion in the scheme, verify it was evaluated
            for criterion_key in scheme_criteria.keys():
                # The criterion should appear in either matched, unmatched, or missing
                all_evaluated_criteria = (
                    evaluation["matched_criteria"] + 
                    evaluation["unmatched_criteria"] + 
                    evaluation["missing_information"]
                )
                
                # Map scheme criteria keys to evaluation criteria names
                criterion_mapping = {
                    "occupation": "occupation",
                    "max_income": "income",
                    "min_age": "age",
                    "max_age": "age_limit",
                    "gender": "gender",
                    "caste": "caste",
                    "state": "location",
                    "land_ownership": "land_ownership",
                    "marital_status": "marital_status"
                }
                
                expected_criterion = criterion_mapping.get(criterion_key)
                if expected_criterion:
                    # Check if this criterion was evaluated
                    # Note: age might appear as either "age" or "age_limit" or both
                    if expected_criterion in ["age", "age_limit"]:
                        assert any(c in all_evaluated_criteria for c in ["age", "age_limit"]), \
                            f"Age criterion must be evaluated for scheme {scheme['scheme_id']}"
                    else:
                        assert expected_criterion in all_evaluated_criteria, \
                            f"Criterion {expected_criterion} must be evaluated for scheme {scheme['scheme_id']}"
            
            # Property 2: Confidence score should reflect match quality
            if len(evaluation["matched_criteria"]) > 0:
                total_criteria = len(evaluation["matched_criteria"]) + len(evaluation["unmatched_criteria"])
                if total_criteria > 0:
                    expected_confidence = len(evaluation["matched_criteria"]) / total_criteria
                    assert evaluation["confidence"] == expected_confidence, \
                        "Confidence should equal matched / (matched + unmatched)"
            
            # Property 3: Eligibility logic must be correct
            # Eligible only if: has matched criteria AND no unmatched criteria AND no missing info
            expected_eligible = (
                len(evaluation["matched_criteria"]) > 0 and
                len(evaluation["unmatched_criteria"]) == 0 and
                len(evaluation["missing_information"]) == 0
            )
            assert evaluation["is_eligible"] == expected_eligible, \
                f"Eligibility logic incorrect for scheme {scheme['scheme_id']}"
    
    finally:
        await matcher.close()


@pytest.mark.asyncio
@given(profile=user_profile_strategy())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much]
)
async def test_property_ranking_correctness(profile: Dict[str, Any]):
    """
    **Feature: gram-sahayak, Property 6: Comprehensive Scheme Matching - Ranking**
    **Validates: Requirement 3.3**
    
    Property: Ranking by benefit should prioritize higher benefit amounts,
    and ranking by ease should prioritize easier applications
    """
    matcher = SchemeMatcherService()
    
    try:
        eligible_schemes = await matcher.find_eligible_schemes(profile)
        
        # Only test if there are multiple schemes to rank
        assume(len(eligible_schemes) >= 2)
        
        # Test benefit-based ranking
        preferences_benefit = {"prioritize_benefit": True, "prioritize_ease": False}
        ranked_by_benefit = await matcher.get_priority_ranking(eligible_schemes, preferences_benefit)
        
        # Property 1: Higher benefit schemes should have higher priority scores
        # (when prioritizing benefit)
        for i in range(len(ranked_by_benefit) - 1):
            current = ranked_by_benefit[i]
            next_scheme = ranked_by_benefit[i + 1]
            
            # Priority score should be non-increasing
            assert current["priority_score"] >= next_scheme["priority_score"], \
                "Priority scores must be in descending order"
            
            # If priority scores are equal, either benefit is similar or other factors balance out
            if current["priority_score"] > next_scheme["priority_score"]:
                # Higher priority should generally correlate with higher benefit or better match
                assert (
                    current["estimated_benefit"] >= next_scheme["estimated_benefit"] or
                    current["match_score"] >= next_scheme["match_score"]
                ), "Higher priority should correlate with higher benefit or match score"
        
        # Test ease-based ranking
        preferences_ease = {"prioritize_benefit": False, "prioritize_ease": True}
        ranked_by_ease = await matcher.get_priority_ranking(eligible_schemes, preferences_ease)
        
        # Property 2: Easy schemes should rank higher than hard schemes when prioritizing ease
        difficulty_scores = {"easy": 1.0, "medium": 0.5, "hard": 0.0}
        
        for i in range(len(ranked_by_ease) - 1):
            current = ranked_by_ease[i]
            next_scheme = ranked_by_ease[i + 1]
            
            # Priority score should be non-increasing
            assert current["priority_score"] >= next_scheme["priority_score"], \
                "Priority scores must be in descending order"
        
        # Property 3: Different ranking preferences should potentially produce different orders
        # (unless all schemes have same benefit and difficulty)
        benefit_order = [s["scheme_id"] for s in ranked_by_benefit]
        ease_order = [s["scheme_id"] for s in ranked_by_ease]
        
        # Check if schemes have varying benefits and difficulties
        benefits = [s["estimated_benefit"] for s in eligible_schemes]
        difficulties = [s["application_difficulty"] for s in eligible_schemes]
        
        has_varying_benefits = len(set(benefits)) > 1
        has_varying_difficulties = len(set(difficulties)) > 1
        
        # If both vary, rankings might differ (but not required to differ)
        # This is a weak property - we just verify both rankings are valid
        if has_varying_benefits and has_varying_difficulties:
            # Both rankings should be valid (already tested above)
            assert len(benefit_order) == len(ease_order), "Both rankings should have same length"
    
    finally:
        await matcher.close()


@pytest.mark.asyncio
@given(profile=user_profile_strategy())
@settings(
    max_examples=50,  # Fewer examples since this tests all schemes
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_no_false_positives(profile: Dict[str, Any]):
    """
    **Feature: gram-sahayak, Property 6: Comprehensive Scheme Matching - Correctness**
    **Validates: Requirements 3.1, 3.2**
    
    Property: No scheme should be marked as eligible if it has unmatched criteria
    or missing required information
    """
    matcher = SchemeMatcherService()
    
    try:
        eligible_schemes = await matcher.find_eligible_schemes(profile)
        
        # For each scheme marked as eligible, verify it truly is eligible
        for scheme in eligible_schemes:
            evaluation = await matcher.evaluate_eligibility(scheme["scheme_id"], profile)
            
            # Property 1: No false positives - eligible schemes must have no unmatched criteria
            assert len(evaluation["unmatched_criteria"]) == 0, \
                f"Eligible scheme {scheme['scheme_id']} has unmatched criteria: {evaluation['unmatched_criteria']}"
            
            # Property 2: No false positives - eligible schemes must have no missing information
            assert len(evaluation["missing_information"]) == 0, \
                f"Eligible scheme {scheme['scheme_id']} has missing information: {evaluation['missing_information']}"
            
            # Property 3: Eligible schemes must have at least one matched criterion
            assert len(evaluation["matched_criteria"]) > 0, \
                f"Eligible scheme {scheme['scheme_id']} has no matched criteria"
            
            # Property 4: Confidence should be 1.0 for truly eligible schemes
            assert evaluation["confidence"] == 1.0, \
                f"Eligible scheme {scheme['scheme_id']} should have confidence 1.0, got {evaluation['confidence']}"
    
    finally:
        await matcher.close()
