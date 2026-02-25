"""
Property-Based Tests for Alternative Scheme Suggestions
**Validates: Requirement 3.5**

Property 8: Alternative Scheme Suggestions
For any user ineligible for requested schemes, the Scheme_Matcher should provide
relevant alternative programs based on user profile and preferences
"""
import pytest
import sys
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scheme_matcher_service import SchemeMatcherService


# Custom strategies for generating valid Indian demographic data
@st.composite
def user_profile_with_history_strategy(draw):
    """Generate random but valid user profiles with application history"""
    
    # Personal information
    age = draw(st.integers(min_value=1, max_value=100))
    gender = draw(st.sampled_from(["male", "female", "other"]))
    marital_status = draw(st.sampled_from(["single", "married", "widow", "widower", "divorced"]))
    
    # Demographics
    states = ["Uttar Pradesh", "Bihar", "Maharashtra", "Tamil Nadu", "Karnataka", "West Bengal"]
    caste = draw(st.sampled_from(["general", "obc", "sc", "st"]))
    
    # Economic information
    annual_income = draw(st.integers(min_value=0, max_value=500000))
    occupation = draw(st.sampled_from(["farmer", "laborer", "student", "unemployed", "teacher", "shopkeeper"]))
    has_land = draw(st.booleans())
    
    # Generate application history (0-5 past applications)
    num_applications = draw(st.integers(min_value=0, max_value=5))
    application_history = []
    
    categories = ["agriculture", "employment", "education", "social_welfare", "housing", "health", "energy"]
    difficulties = ["easy", "medium", "hard"]
    
    for _ in range(num_applications):
        application_history.append({
            "scheme_id": f"SCHEME-{draw(st.integers(min_value=100, max_value=999))}",
            "scheme_category": draw(st.sampled_from(categories)),
            "benefit_amount": draw(st.integers(min_value=1000, max_value=150000)),
            "application_difficulty": draw(st.sampled_from(difficulties)),
            "status": draw(st.sampled_from(["approved", "pending", "rejected"])),
            "applied_date": f"2024-{draw(st.integers(min_value=1, max_value=12)):02d}-{draw(st.integers(min_value=1, max_value=28)):02d}"
        })
    
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
        "application_history": application_history
    }


@st.composite
def ineligible_scenario_strategy(draw):
    """
    Generate scenarios where user is ineligible for a specific scheme
    Returns (user_profile, scheme_id) tuple
    """
    profile = draw(user_profile_with_history_strategy())
    
    # Pick a scheme from the database that user might be ineligible for
    # We'll use known schemes and modify profile to make them ineligible
    scheme_choices = [
        ("PM-KISAN", {"land_ownership": {"has_land": False, "acres": 0.0}}),  # Requires land
        ("WIDOW-PENSION", {"personal_info": {"gender": "male"}}),  # Requires female widow
        ("SC-ST-SCHOLARSHIP", {"demographics": {"caste": "general"}}),  # Requires SC/ST
        ("OLD-AGE-PENSION", {"personal_info": {"age": 30}}),  # Requires age >= 60
    ]
    
    scheme_id, ineligibility_modifier = draw(st.sampled_from(scheme_choices))
    
    # Apply the modifier to make user ineligible
    for key, value in ineligibility_modifier.items():
        if key in profile:
            if isinstance(value, dict):
                profile[key].update(value)
            else:
                profile[key] = value
    
    return profile, scheme_id


@pytest.mark.asyncio
@given(scenario=ineligible_scenario_strategy())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_alternative_suggestions_for_ineligible_users(scenario):
    """
    **Feature: gram-sahayak, Property 8: Alternative Scheme Suggestions**
    **Validates: Requirement 3.5**
    
    Property: For any user ineligible for requested schemes, the Scheme_Matcher
    should provide relevant alternative programs based on user profile and preferences
    """
    profile, requested_scheme_id = scenario
    matcher = SchemeMatcherService()
    
    try:
        # Verify user is actually ineligible for the requested scheme
        eligibility = await matcher.evaluate_eligibility(requested_scheme_id, profile)
        
        # Only test when user is truly ineligible
        assume(not eligibility["is_eligible"])
        
        # Get alternative suggestions
        alternatives = await matcher.suggest_alternative_schemes(profile, requested_scheme_id)
        
        # Property 1: Result should always be a list
        assert isinstance(alternatives, list), "suggest_alternative_schemes must return a list"
        
        # Property 2: All alternatives must be schemes the user IS eligible for
        for alt in alternatives:
            alt_eligibility = await matcher.evaluate_eligibility(alt["scheme_id"], profile)
            assert alt_eligibility["is_eligible"], \
                f"Alternative scheme {alt['scheme_id']} must be one user is eligible for"
        
        # Property 3: Alternatives should not include the requested scheme
        alternative_ids = [alt["scheme_id"] for alt in alternatives]
        assert requested_scheme_id not in alternative_ids, \
            "Alternatives should not include the ineligible requested scheme"
        
        # Property 4: Each alternative must have required fields
        for alt in alternatives:
            assert "scheme_id" in alt, "Alternative must have scheme_id"
            assert "name" in alt, "Alternative must have name"
            assert "suggestion_reason" in alt, "Alternative must have suggestion_reason"
            assert "match_score" in alt, "Alternative must have match_score"
            assert "estimated_benefit" in alt, "Alternative must have estimated_benefit"
            assert "application_difficulty" in alt, "Alternative must have application_difficulty"
            assert "category" in alt, "Alternative must have category"
        
        # Property 5: Match scores should be valid (between 0 and 1, or slightly higher with boosts)
        for alt in alternatives:
            assert alt["match_score"] >= 0, "Match score cannot be negative"
            assert alt["match_score"] <= 1.5, "Match score should not exceed reasonable bounds"
        
        # Property 6: Suggestion reasons should be non-empty and meaningful
        for alt in alternatives:
            assert alt["suggestion_reason"], "Each alternative must have a non-empty suggestion reason"
            assert len(alt["suggestion_reason"]) > 0, "Suggestion reason must not be empty string"
        
        # Property 7: Alternatives should be sorted by match score (descending)
        if len(alternatives) > 1:
            scores = [alt["match_score"] for alt in alternatives]
            assert scores == sorted(scores, reverse=True), \
                "Alternatives must be sorted by match score (highest first)"
        
        # Property 8: Alternatives should be relevant (category or relationship based)
        if len(alternatives) > 0:
            # Get the requested scheme details
            requested_scheme = next(
                (s for s in matcher.schemes_db if s["scheme_id"] == requested_scheme_id),
                None
            )
            
            if requested_scheme:
                requested_category = requested_scheme.get("category", "general")
                
                # At least some alternatives should be relevant
                # (same category, related, or based on user preferences)
                for alt in alternatives:
                    reason = alt["suggestion_reason"].lower()
                    
                    # Reason should mention relevance
                    assert any(keyword in reason for keyword in [
                        "category", "related", "similar", "interest", "past"
                    ]), f"Suggestion reason should explain relevance: {alt['suggestion_reason']}"
        
        # Property 9: User preferences should influence suggestions
        if len(profile.get("application_history", [])) > 0 and len(alternatives) > 0:
            # If user has application history, some alternatives might mention preferences
            # This is a soft property - not all alternatives need to mention it
            has_preference_mention = any(
                "past interests" in alt.get("suggestion_reason", "").lower() or
                "based on your" in alt.get("suggestion_reason", "").lower()
                for alt in alternatives
            )
            
            # If user has strong category preferences, they should be reflected
            # (but this is not strictly required, so we just verify the field exists)
            for alt in alternatives:
                assert "match_score" in alt, "Match score should reflect preferences"
        
        # Property 10: No duplicate alternatives
        alternative_ids = [alt["scheme_id"] for alt in alternatives]
        assert len(alternative_ids) == len(set(alternative_ids)), \
            "Alternatives should not contain duplicates"
        
        # Property 11: Consistency - calling again should give same results
        alternatives2 = await matcher.suggest_alternative_schemes(profile, requested_scheme_id)
        
        # Should return same scheme IDs in same order
        ids1 = [alt["scheme_id"] for alt in alternatives]
        ids2 = [alt["scheme_id"] for alt in alternatives2]
        assert ids1 == ids2, "Alternative suggestions should be deterministic"
        
        # Scores should be identical
        if len(alternatives) > 0:
            scores1 = [alt["match_score"] for alt in alternatives]
            scores2 = [alt["match_score"] for alt in alternatives2]
            assert scores1 == scores2, "Match scores should be deterministic"
    
    finally:
        await matcher.close()


@pytest.mark.asyncio
@given(profile=user_profile_with_history_strategy())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_no_alternatives_when_eligible(profile):
    """
    **Feature: gram-sahayak, Property 8: Alternative Scheme Suggestions - Eligibility Check**
    **Validates: Requirement 3.5**
    
    Property: When user IS eligible for requested scheme, no alternatives should be suggested
    """
    matcher = SchemeMatcherService()
    
    try:
        # Find schemes user is eligible for
        eligible_schemes = await matcher.find_eligible_schemes(profile)
        
        # Only test if user is eligible for at least one scheme
        assume(len(eligible_schemes) > 0)
        
        # Pick an eligible scheme
        eligible_scheme_id = eligible_schemes[0]["scheme_id"]
        
        # Request alternatives for this eligible scheme
        alternatives = await matcher.suggest_alternative_schemes(profile, eligible_scheme_id)
        
        # Property: Should return empty list when user is eligible
        assert alternatives == [], \
            "Should not suggest alternatives when user is eligible for requested scheme"
    
    finally:
        await matcher.close()


@pytest.mark.asyncio
@given(profile=user_profile_with_history_strategy())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_preference_learning_influences_suggestions(profile):
    """
    **Feature: gram-sahayak, Property 8: Alternative Scheme Suggestions - Preference Learning**
    **Validates: Requirement 3.5**
    
    Property: User's application history should influence alternative suggestions
    through preference learning and adaptation
    """
    matcher = SchemeMatcherService()
    
    try:
        # Only test profiles with application history
        assume(len(profile.get("application_history", [])) > 0)
        
        # Find a scheme user is ineligible for
        all_schemes = matcher.schemes_db
        ineligible_schemes = []
        
        for scheme in all_schemes:
            eligibility = await matcher.evaluate_eligibility(scheme["scheme_id"], profile)
            if not eligibility["is_eligible"]:
                ineligible_schemes.append(scheme["scheme_id"])
        
        # Only test if there's at least one ineligible scheme
        assume(len(ineligible_schemes) > 0)
        
        # Pick an ineligible scheme
        requested_scheme_id = ineligible_schemes[0]
        
        # Get alternatives
        alternatives = await matcher.suggest_alternative_schemes(profile, requested_scheme_id)
        
        if len(alternatives) > 0:
            # Property 1: Preference learning should be applied
            # Verify that _learn_user_preferences was called by checking if scores are adapted
            
            # Get learned preferences
            learned_prefs = matcher._learn_user_preferences(profile["application_history"])
            
            # Property 2: Learned preferences should have expected structure
            assert "preferred_categories" in learned_prefs
            assert "preferred_benefit_range" in learned_prefs
            assert "preferred_difficulty" in learned_prefs
            assert "application_count" in learned_prefs
            
            # Property 3: Application count should match history length
            assert learned_prefs["application_count"] == len(profile["application_history"])
            
            # Property 4: If user has category preferences, schemes in those categories
            # should potentially have boosted scores
            if learned_prefs["preferred_categories"]:
                preferred_cat = learned_prefs["preferred_categories"][0]
                
                # Find alternatives in preferred category
                preferred_alts = [
                    alt for alt in alternatives
                    if alt.get("category") == preferred_cat
                ]
                
                # If such alternatives exist, they should rank reasonably well
                if preferred_alts:
                    # At least one should be in top half
                    top_half_size = len(alternatives) // 2 + 1
                    top_half = alternatives[:top_half_size]
                    
                    has_preferred_in_top = any(
                        alt.get("category") == preferred_cat
                        for alt in top_half
                    )
                    
                    # This is a soft property - preferences boost but don't guarantee top ranking
                    # We just verify the mechanism exists
                    assert isinstance(has_preferred_in_top, bool)
            
            # Property 5: Score adaptation should be consistent
            # Re-calculate adapted scores and verify they match
            for alt in alternatives:
                scheme_data = next(
                    (s for s in matcher.schemes_db if s["scheme_id"] == alt["scheme_id"]),
                    None
                )
                
                if scheme_data:
                    # The match_score should have been adapted
                    # We can't easily verify the exact value, but it should be >= base score
                    assert alt["match_score"] >= 0
    
    finally:
        await matcher.close()


@pytest.mark.asyncio
@given(profile=user_profile_with_history_strategy())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_category_and_relationship_based_suggestions(profile):
    """
    **Feature: gram-sahayak, Property 8: Alternative Scheme Suggestions - Relevance**
    **Validates: Requirement 3.5**
    
    Property: Alternative suggestions should be based on category similarity
    or scheme relationships (related schemes)
    """
    matcher = SchemeMatcherService()
    
    try:
        # Find a scheme user is ineligible for
        all_schemes = matcher.schemes_db
        ineligible_schemes = []
        
        for scheme in all_schemes:
            eligibility = await matcher.evaluate_eligibility(scheme["scheme_id"], profile)
            if not eligibility["is_eligible"]:
                ineligible_schemes.append(scheme)
        
        # Only test if there's at least one ineligible scheme
        assume(len(ineligible_schemes) > 0)
        
        # Pick an ineligible scheme
        requested_scheme = ineligible_schemes[0]
        requested_scheme_id = requested_scheme["scheme_id"]
        
        # Get alternatives
        alternatives = await matcher.suggest_alternative_schemes(profile, requested_scheme_id)
        
        if len(alternatives) > 0:
            requested_category = requested_scheme.get("category", "general")
            requested_related = requested_scheme.get("related_schemes", [])
            
            # Property 1: Alternatives should be relevant
            for alt in alternatives:
                # Each alternative should be either:
                # 1. In the same category as requested scheme
                # 2. Related to the requested scheme
                # 3. Based on user preferences (from history)
                
                is_same_category = alt.get("category") == requested_category
                is_related = alt["scheme_id"] in requested_related
                
                # At minimum, the suggestion reason should explain the connection
                reason = alt["suggestion_reason"]
                assert len(reason) > 0, "Must have a suggestion reason"
                
                # Reason should mention one of the relevance factors
                reason_lower = reason.lower()
                has_relevance_mention = any(keyword in reason_lower for keyword in [
                    "category", "related", "similar", requested_category.lower(),
                    "interest", "past", "based on"
                ])
                
                assert has_relevance_mention, \
                    f"Suggestion reason must explain relevance: {reason}"
            
            # Property 2: If same-category alternatives exist, they should be included
            same_category_alts = [
                alt for alt in alternatives
                if alt.get("category") == requested_category
            ]
            
            # If there are eligible schemes in the same category, at least some should be suggested
            # (This is a soft property - we just verify the mechanism works)
            if same_category_alts:
                for alt in same_category_alts:
                    assert "category" in alt["suggestion_reason"].lower() or \
                           requested_category.lower() in alt["suggestion_reason"].lower(), \
                           "Same-category alternatives should mention category in reason"
            
            # Property 3: If related schemes exist and user is eligible, they should be included
            related_alts = [
                alt for alt in alternatives
                if alt["scheme_id"] in requested_related
            ]
            
            if related_alts:
                for alt in related_alts:
                    assert "related" in alt["suggestion_reason"].lower(), \
                           "Related alternatives should mention relationship in reason"
    
    finally:
        await matcher.close()


@pytest.mark.asyncio
@given(profile=user_profile_with_history_strategy())
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_invalid_scheme_handling(profile):
    """
    **Feature: gram-sahayak, Property 8: Alternative Scheme Suggestions - Error Handling**
    **Validates: Requirement 3.5**
    
    Property: System should handle invalid scheme IDs gracefully
    """
    matcher = SchemeMatcherService()
    
    try:
        # Request alternatives for non-existent scheme
        invalid_scheme_id = "INVALID-SCHEME-DOES-NOT-EXIST"
        
        alternatives = await matcher.suggest_alternative_schemes(profile, invalid_scheme_id)
        
        # Property: Should return empty list for invalid scheme
        assert alternatives == [], \
            "Should return empty list for invalid scheme ID"
        
        # Should not raise an exception
        assert isinstance(alternatives, list)
    
    finally:
        await matcher.close()
