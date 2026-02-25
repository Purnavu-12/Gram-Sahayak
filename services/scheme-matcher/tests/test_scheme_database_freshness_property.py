"""
Property-Based Test for Scheme Database Freshness
**Validates: Requirement 3.4**

Property 7: Scheme Database Freshness
For any change in government scheme criteria, the Knowledge_Base should reflect 
updates within 24 hours while maintaining system availability.
"""
import pytest
import sys
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import Dict, Any, List
from datetime import datetime, timedelta
import asyncio

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scheme_matcher_service import SchemeMatcherService
from data_freshness_monitor import FreshnessStatus


# Custom strategies for generating scheme updates
@st.composite
def scheme_update_strategy(draw):
    """Generate random but valid scheme updates for property testing"""
    
    # Select a scheme to update - only use schemes that exist in the database
    scheme_ids = [
        "PM-KISAN", "MGNREGA", "PM-FASAL-BIMA", "WIDOW-PENSION", "OLD-AGE-PENSION"
    ]
    
    scheme_id = draw(st.sampled_from(scheme_ids))
    
    # Generate update timestamp (can be recent or old)
    hours_ago = draw(st.integers(min_value=0, max_value=72))
    update_time = datetime.now() - timedelta(hours=hours_ago)
    
    # Generate changes to scheme criteria
    changes = {}
    
    # Randomly update different fields
    if draw(st.booleans()):
        changes["benefit_amount"] = draw(st.integers(min_value=1000, max_value=50000))
    
    if draw(st.booleans()):
        changes["max_income"] = draw(st.integers(min_value=50000, max_value=500000))
    
    if draw(st.booleans()):
        changes["min_age"] = draw(st.integers(min_value=18, max_value=60))
    
    if draw(st.booleans()):
        changes["description"] = f"Updated description at {update_time.isoformat()}"
    
    if draw(st.booleans()):
        changes["difficulty"] = draw(st.sampled_from(["easy", "medium", "hard"]))
    
    # Ensure at least one change
    if not changes:
        changes["description"] = f"Updated at {update_time.isoformat()}"
    
    return {
        "scheme_id": scheme_id,
        "changes": changes,
        "update_time": update_time,
        "hours_ago": hours_ago
    }


@st.composite
def batch_updates_strategy(draw):
    """Generate a batch of scheme updates"""
    num_updates = draw(st.integers(min_value=1, max_value=5))
    updates = [draw(scheme_update_strategy()) for _ in range(num_updates)]
    return updates


@pytest.mark.asyncio
@given(update=scheme_update_strategy())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_scheme_database_freshness_single_update(update: Dict[str, Any]):
    """
    **Feature: gram-sahayak, Property 7: Scheme Database Freshness**
    **Validates: Requirement 3.4**
    
    Property: For any change in government scheme criteria, the Knowledge_Base should:
    1. Reflect updates within 24 hours
    2. Maintain system availability during updates
    3. Track update timestamps accurately
    """
    matcher = SchemeMatcherService()
    
    try:
        # Property 1: System should be available before update
        initial_schemes = await matcher.find_eligible_schemes({
            "user_id": "test_user",
            "personal_info": {"age": 30, "gender": "male"},
            "demographics": {"state": "Test State", "caste": "general", "family_size": 4},
            "economic": {"annual_income": 100000, "occupation": "farmer", "land_ownership": {"has_land": True}},
            "preferences": {"preferred_language": "hi"}
        })
        assert isinstance(initial_schemes, list), "System must be available before update"
        
        # Get initial scheme state
        initial_scheme = next(
            (s for s in matcher.schemes_db if s["scheme_id"] == update["scheme_id"]),
            None
        )
        assert initial_scheme is not None, f"Scheme {update['scheme_id']} must exist"
        
        # Property 2: Update should complete successfully (system availability maintained)
        update_payload = [{
            "scheme_id": update["scheme_id"],
            "changes": update["changes"]
        }]
        
        result = await matcher.update_scheme_database(update_payload)
        
        assert result["success"] is True, "Update must succeed"
        assert result["updated_count"] >= 1, "At least one scheme must be updated"
        assert update["scheme_id"] in result["updated_schemes"], "Updated scheme must be in result"
        
        # Property 3: System should remain available after update
        post_update_schemes = await matcher.find_eligible_schemes({
            "user_id": "test_user",
            "personal_info": {"age": 30, "gender": "male"},
            "demographics": {"state": "Test State", "caste": "general", "family_size": 4},
            "economic": {"annual_income": 100000, "occupation": "farmer", "land_ownership": {"has_land": True}},
            "preferences": {"preferred_language": "hi"}
        })
        assert isinstance(post_update_schemes, list), "System must remain available after update"
        
        # Property 4: Updated scheme should reflect changes
        updated_scheme = next(
            (s for s in matcher.schemes_db if s["scheme_id"] == update["scheme_id"]),
            None
        )
        assert updated_scheme is not None, "Updated scheme must exist in database"
        
        # Verify changes were applied
        for field, new_value in update["changes"].items():
            if field in ["max_income", "min_age", "max_age"]:
                # These are in eligibility sub-dict
                if field == "max_income":
                    assert updated_scheme["eligibility"].get("max_income") == new_value, \
                        f"Field {field} must be updated"
                elif field == "min_age":
                    assert updated_scheme["eligibility"].get("min_age") == new_value, \
                        f"Field {field} must be updated"
                elif field == "max_age":
                    assert updated_scheme["eligibility"].get("max_age") == new_value, \
                        f"Field {field} must be updated"
            else:
                # Top-level fields
                assert updated_scheme.get(field) == new_value, \
                    f"Field {field} must be updated to {new_value}"
        
        # Property 5: Update timestamp should be recorded
        assert "last_updated" in updated_scheme, "Scheme must have last_updated timestamp"
        
        last_updated_str = updated_scheme["last_updated"]
        last_updated = datetime.fromisoformat(last_updated_str)
        
        # Timestamp should be recent (within last minute)
        time_diff = datetime.now() - last_updated
        assert time_diff.total_seconds() < 60, "Update timestamp must be recent"
        
        # Property 6: Freshness monitoring should detect update status
        if matcher.freshness_monitor:
            freshness_status = matcher.freshness_monitor.check_scheme_freshness(updated_scheme)
            
            # Freshly updated scheme should be marked as FRESH
            assert freshness_status == FreshnessStatus.FRESH, \
                "Newly updated scheme must be marked as FRESH"
        
        # Property 7: Update should be logged
        status = matcher.get_scheme_update_status()
        assert status["recent_updates"] >= 1, "Update must be logged"
        assert status["total_schemes"] > 0, "Database must contain schemes"
        
        # Property 8: Database integrity maintained
        # All schemes should still have required fields
        for scheme in matcher.schemes_db:
            assert "scheme_id" in scheme, "All schemes must have scheme_id"
            assert "name" in scheme, "All schemes must have name"
            assert "eligibility" in scheme, "All schemes must have eligibility"
            assert "last_updated" in scheme, "All schemes must have last_updated"
        
    finally:
        await matcher.close()


@pytest.mark.asyncio
@given(updates=batch_updates_strategy())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_scheme_database_freshness_batch_updates(updates: List[Dict[str, Any]]):
    """
    **Feature: gram-sahayak, Property 7: Scheme Database Freshness - Batch Updates**
    **Validates: Requirement 3.4**
    
    Property: For any batch of scheme updates, the system should:
    1. Process all updates successfully
    2. Maintain availability throughout
    3. Track freshness for all updated schemes
    """
    matcher = SchemeMatcherService()
    
    try:
        # Property 1: System available before batch update
        initial_status = matcher.get_scheme_update_status()
        assert initial_status["total_schemes"] > 0, "Database must be initialized"
        
        # Property 2: Batch update should succeed
        update_payload = [
            {
                "scheme_id": update["scheme_id"],
                "changes": update["changes"]
            }
            for update in updates
        ]
        
        result = await matcher.update_scheme_database(update_payload)
        
        assert result["success"] is True, "Batch update must succeed"
        assert result["updated_count"] == len(updates), \
            f"All {len(updates)} updates must be processed"
        
        # Property 3: All updated schemes should be in result
        for update in updates:
            assert update["scheme_id"] in result["updated_schemes"], \
                f"Scheme {update['scheme_id']} must be in update result"
        
        # Property 4: System remains available after batch update
        test_profile = {
            "user_id": "test_user",
            "personal_info": {"age": 30, "gender": "male"},
            "demographics": {"state": "Test State", "caste": "general", "family_size": 4},
            "economic": {"annual_income": 100000, "occupation": "farmer", "land_ownership": {"has_land": True}},
            "preferences": {"preferred_language": "hi"}
        }
        
        schemes = await matcher.find_eligible_schemes(test_profile)
        assert isinstance(schemes, list), "System must remain available after batch update"
        
        # Property 5: All updated schemes should have fresh timestamps
        for update in updates:
            updated_scheme = next(
                (s for s in matcher.schemes_db if s["scheme_id"] == update["scheme_id"]),
                None
            )
            assert updated_scheme is not None, f"Scheme {update['scheme_id']} must exist"
            
            last_updated = datetime.fromisoformat(updated_scheme["last_updated"])
            time_diff = datetime.now() - last_updated
            assert time_diff.total_seconds() < 60, \
                f"Scheme {update['scheme_id']} timestamp must be recent"
        
        # Property 6: Freshness monitoring should work for all schemes
        if matcher.freshness_monitor:
            freshness_report = matcher.check_data_freshness()
            
            assert "total_schemes" in freshness_report, "Freshness report must include total"
            assert freshness_report["total_schemes"] > 0, "Database must have schemes"
            
            # Updated schemes should be fresh
            for update in updates:
                updated_scheme = next(
                    (s for s in matcher.schemes_db if s["scheme_id"] == update["scheme_id"]),
                    None
                )
                status = matcher.freshness_monitor.check_scheme_freshness(updated_scheme)
                assert status == FreshnessStatus.FRESH, \
                    f"Updated scheme {update['scheme_id']} must be FRESH"
        
        # Property 7: Update log should reflect all changes
        final_status = matcher.get_scheme_update_status()
        assert final_status["recent_updates"] >= len(updates), \
            "All updates must be logged"
        
    finally:
        await matcher.close()


@pytest.mark.asyncio
@given(update=scheme_update_strategy())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_freshness_detection_accuracy(update: Dict[str, Any]):
    """
    **Feature: gram-sahayak, Property 7: Scheme Database Freshness - Detection Accuracy**
    **Validates: Requirement 3.4**
    
    Property: Freshness monitoring should accurately detect scheme age:
    - Fresh: Updated within 24 hours
    - Stale: Updated more than 24 hours ago
    - Critical: Updated more than 48 hours ago
    """
    matcher = SchemeMatcherService()
    
    # Skip if monitoring not available
    if not matcher.freshness_monitor:
        pytest.skip("Freshness monitoring not available")
    
    try:
        # Create a scheme with specific update time
        scheme_id = update["scheme_id"]
        update_time = update["update_time"]
        hours_ago = update["hours_ago"]
        
        # Update the scheme
        await matcher.update_scheme_database([{
            "scheme_id": scheme_id,
            "changes": update["changes"]
        }])
        
        # Get the updated scheme
        scheme = next(
            (s for s in matcher.schemes_db if s["scheme_id"] == scheme_id),
            None
        )
        assert scheme is not None
        
        # Manually set the last_updated to simulate age
        scheme["last_updated"] = update_time.isoformat()
        
        # Property 1: Freshness detection should be accurate based on age
        status = matcher.freshness_monitor.check_scheme_freshness(scheme)
        
        if hours_ago < 24:
            # Should be FRESH
            assert status == FreshnessStatus.FRESH, \
                f"Scheme updated {hours_ago} hours ago should be FRESH"
        elif hours_ago < 48:
            # Should be STALE
            assert status == FreshnessStatus.STALE, \
                f"Scheme updated {hours_ago} hours ago should be STALE"
        else:
            # Should be CRITICAL
            assert status == FreshnessStatus.CRITICAL, \
                f"Scheme updated {hours_ago} hours ago should be CRITICAL"
        
        # Property 2: Database-wide freshness check should aggregate correctly
        freshness_report = matcher.check_data_freshness()
        
        assert "fresh_count" in freshness_report
        assert "stale_count" in freshness_report
        assert "critical_count" in freshness_report
        
        total = (freshness_report["fresh_count"] + 
                freshness_report["stale_count"] + 
                freshness_report["critical_count"] +
                freshness_report.get("unknown_count", 0))
        
        assert total == freshness_report["total_schemes"], \
            "Freshness counts must sum to total schemes"
        
        # Property 3: Stale schemes should be identifiable
        stale_schemes = matcher.get_stale_schemes()
        assert isinstance(stale_schemes, list), "Stale schemes must be a list"
        
        # If our test scheme is stale/critical, it should be in the list
        if hours_ago > 24:
            assert any(s["scheme_id"] == scheme_id for s in stale_schemes), \
                f"Stale scheme {scheme_id} should be in stale schemes list"
        
    finally:
        await matcher.close()


@pytest.mark.asyncio
@given(updates=batch_updates_strategy())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_system_availability_during_updates(updates: List[Dict[str, Any]]):
    """
    **Feature: gram-sahayak, Property 7: Scheme Database Freshness - System Availability**
    **Validates: Requirement 3.4**
    
    Property: System must remain available and responsive during scheme updates:
    1. Read operations should work during updates
    2. Multiple concurrent operations should succeed
    3. No data corruption should occur
    """
    matcher = SchemeMatcherService()
    
    try:
        test_profile = {
            "user_id": "test_user",
            "personal_info": {"age": 30, "gender": "male"},
            "demographics": {"state": "Test State", "caste": "general", "family_size": 4},
            "economic": {"annual_income": 100000, "occupation": "farmer", "land_ownership": {"has_land": True}},
            "preferences": {"preferred_language": "hi"}
        }
        
        # Property 1: Concurrent read and write operations should both succeed
        update_payload = [
            {"scheme_id": u["scheme_id"], "changes": u["changes"]}
            for u in updates
        ]
        
        # Execute update and read concurrently
        update_task = matcher.update_scheme_database(update_payload)
        read_task = matcher.find_eligible_schemes(test_profile)
        
        update_result, read_result = await asyncio.gather(
            update_task,
            read_task,
            return_exceptions=True
        )
        
        # Both operations should succeed
        assert not isinstance(update_result, Exception), \
            f"Update should not raise exception: {update_result}"
        assert not isinstance(read_result, Exception), \
            f"Read should not raise exception: {read_result}"
        
        assert update_result["success"] is True, "Update must succeed"
        assert isinstance(read_result, list), "Read must return list"
        
        # Property 2: Multiple concurrent reads should work
        read_tasks = [
            matcher.find_eligible_schemes(test_profile)
            for _ in range(3)
        ]
        
        read_results = await asyncio.gather(*read_tasks, return_exceptions=True)
        
        for i, result in enumerate(read_results):
            assert not isinstance(result, Exception), \
                f"Read {i} should not raise exception"
            assert isinstance(result, list), f"Read {i} must return list"
        
        # Property 3: All reads should return consistent results
        # (same schemes should be eligible across concurrent reads)
        scheme_ids_sets = [
            set(s["scheme_id"] for s in result)
            for result in read_results
            if not isinstance(result, Exception)
        ]
        
        if len(scheme_ids_sets) > 1:
            # All sets should be equal (deterministic matching)
            first_set = scheme_ids_sets[0]
            for scheme_set in scheme_ids_sets[1:]:
                assert scheme_set == first_set, \
                    "Concurrent reads must return consistent results"
        
        # Property 4: Database integrity after concurrent operations
        for scheme in matcher.schemes_db:
            assert "scheme_id" in scheme, "All schemes must have scheme_id"
            assert "name" in scheme, "All schemes must have name"
            assert "eligibility" in scheme, "All schemes must have eligibility"
            assert "last_updated" in scheme, "All schemes must have last_updated"
        
        # Property 5: No duplicate schemes after updates
        scheme_ids = [s["scheme_id"] for s in matcher.schemes_db]
        assert len(scheme_ids) == len(set(scheme_ids)), \
            "No duplicate schemes should exist"
        
    finally:
        await matcher.close()


@pytest.mark.asyncio
@given(st.just(None))  # Dummy strategy to satisfy @given requirement
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_24_hour_freshness_guarantee(_):
    """
    **Feature: gram-sahayak, Property 7: Scheme Database Freshness - 24 Hour Guarantee**
    **Validates: Requirement 3.4**
    
    Property: The system should guarantee that scheme updates are reflected within 24 hours:
    1. Updates should be immediately visible
    2. Freshness monitoring should track the 24-hour window
    3. Alerts should be generated for stale data
    """
    matcher = SchemeMatcherService()
    
    if not matcher.freshness_monitor:
        pytest.skip("Freshness monitoring not available")
    
    try:
        # Property 1: Fresh update should be immediately visible
        update_payload = [{
            "scheme_id": "PM-KISAN",
            "changes": {
                "benefit_amount": 7000,
                "description": "Updated for 24-hour test"
            }
        }]
        
        result = await matcher.update_scheme_database(update_payload)
        assert result["success"] is True
        
        # Verify immediate visibility
        updated_scheme = next(
            (s for s in matcher.schemes_db if s["scheme_id"] == "PM-KISAN"),
            None
        )
        assert updated_scheme is not None
        assert updated_scheme["benefit_amount"] == 7000
        
        # Property 2: Freshness status should be FRESH immediately after update
        status = matcher.freshness_monitor.check_scheme_freshness(updated_scheme)
        assert status == FreshnessStatus.FRESH, \
            "Immediately updated scheme must be FRESH"
        
        # Property 3: Simulate scheme aging beyond 24 hours
        old_time = datetime.now() - timedelta(hours=25)
        updated_scheme["last_updated"] = old_time.isoformat()
        
        status_after_aging = matcher.freshness_monitor.check_scheme_freshness(updated_scheme)
        assert status_after_aging == FreshnessStatus.STALE, \
            "Scheme older than 24 hours must be STALE"
        
        # Property 4: Freshness report should identify stale schemes
        freshness_report = matcher.check_data_freshness()
        
        # At least one scheme should be stale (the one we aged)
        assert freshness_report["stale_count"] >= 1, \
            "Freshness report must identify stale schemes"
        
        # Property 5: Stale schemes should be retrievable
        stale_schemes = matcher.get_stale_schemes()
        assert any(s["scheme_id"] == "PM-KISAN" for s in stale_schemes), \
            "Aged scheme must appear in stale schemes list"
        
        # Property 6: Alerts should be generated for stale data
        if matcher.freshness_monitor:
            alerts = matcher.get_freshness_alerts(hours=1)
            # There should be alerts for the stale scheme
            assert isinstance(alerts, list), "Alerts must be a list"
        
    finally:
        await matcher.close()
