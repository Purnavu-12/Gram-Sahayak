"""
Property-based tests for Model Update Continuity
Tests that language model updates can be incorporated without service interruption
or degradation of existing functionality

**Feature: gram-sahayak, Property 5: Model Update Continuity**
**Validates: Requirements 2.5**
"""

import pytest
import sys
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
import asyncio
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dialect_detector_service import DialectDetectorService
from continuous_learning import ModelVersion


# Custom strategies for generating test data
@st.composite
def audio_features_strategy(draw):
    """Generate valid audio features for testing"""
    sample_rate = draw(st.sampled_from([8000, 16000, 22050, 44100, 48000]))
    duration = draw(st.floats(min_value=0.5, max_value=30.0))
    
    return {
        "sample_rate": sample_rate,
        "channels": 1,
        "bit_depth": 16,
        "duration": duration
    }


@st.composite
def model_version_strategy(draw):
    """Generate valid model version identifiers"""
    major = draw(st.integers(min_value=1, max_value=10))
    minor = draw(st.integers(min_value=0, max_value=20))
    patch = draw(st.integers(min_value=0, max_value=50))
    
    return f"v{major}.{minor}.{patch}"


@st.composite
def model_data_strategy(draw):
    """Generate model data for updates"""
    model_type = draw(st.sampled_from(["improved", "optimized", "retrained", "fine-tuned"]))
    accuracy = draw(st.floats(min_value=0.85, max_value=0.99))
    
    return {
        "type": model_type,
        "accuracy": accuracy,
        "training_samples": draw(st.integers(min_value=1000, max_value=100000)),
        "timestamp": time.time()
    }


@st.composite
def traffic_split_strategy(draw):
    """Generate valid traffic split percentages for A/B testing"""
    return draw(st.floats(min_value=0.05, max_value=0.95))


class TestModelUpdateContinuityProperties:
    """
    Property-based tests for model update continuity
    **Validates: Requirement 2.5**
    """
    
    @given(
        audio_features=audio_features_strategy(),
        new_version=model_version_strategy(),
        model_data=model_data_strategy()
    )
    @settings(max_examples=20, deadline=10000)
    def test_property_service_available_during_update(
        self, audio_features, new_version, model_data
    ):
        """
        Property 5.1: Service Availability During Update
        For any model update, the service must remain available and functional
        **Validates: Requirement 2.5 (incorporate updates without service interruption)**
        """
        service = DialectDetectorService()
        
        # Initialize service
        initial_result = asyncio.run(service.detect_dialect(audio_features))
        assert initial_result is not None, "Service failed before update"
        
        # Deploy new model version
        update_result = asyncio.run(service.deploy_model_update(
            version=new_version,
            model_data=model_data,
            gradual_rollout=True
        ))
        
        # Property: Update should succeed
        assert update_result["success"] is True, (
            f"Model update failed for version {new_version}"
        )
        
        # Property: Service must still be functional after update
        post_update_result = asyncio.run(service.detect_dialect(audio_features))
        assert post_update_result is not None, (
            "Service unavailable after model update"
        )
        
        # Property: Result structure must remain consistent
        assert set(initial_result.keys()) == set(post_update_result.keys()), (
            f"Result structure changed after update. "
            f"Before: {set(initial_result.keys())}, "
            f"After: {set(post_update_result.keys())}"
        )
    
    @given(
        audio_features=audio_features_strategy(),
        new_version=model_version_strategy(),
        model_data=model_data_strategy()
    )
    @settings(max_examples=20, deadline=10000)
    def test_property_no_functionality_degradation(
        self, audio_features, new_version, model_data
    ):
        """
        Property 5.2: No Functionality Degradation
        For any model update, existing functionality must not degrade
        **Validates: Requirement 2.5 (no degradation of existing functionality)**
        """
        service = DialectDetectorService()
        
        # Get baseline functionality
        baseline_result = asyncio.run(service.detect_dialect(audio_features))
        baseline_confidence = baseline_result["confidence"]
        baseline_time = baseline_result["detection_time"]
        
        # Deploy new model
        asyncio.run(service.deploy_model_update(
            version=new_version,
            model_data=model_data
        ))
        
        # Test functionality after update
        updated_result = asyncio.run(service.detect_dialect(audio_features))
        
        # Property: Confidence must remain in valid range
        assert 0 <= updated_result["confidence"] <= 1, (
            f"Confidence out of range after update: {updated_result['confidence']}"
        )
        
        # Property: Detection time must not significantly degrade (allow 3x tolerance for simulated timing)
        assert updated_result["detection_time"] < baseline_time * 3, (
            f"Detection time degraded significantly: "
            f"baseline={baseline_time}ms, updated={updated_result['detection_time']}ms"
        )
        
        # Property: Must still meet 3-second requirement
        assert updated_result["detection_time"] < 3000, (
            f"Detection time exceeds requirement after update: "
            f"{updated_result['detection_time']}ms"
        )
        
        # Property: Must return valid dialect
        supported_dialects = asyncio.run(service.get_supported_dialects())
        supported_codes = [d["dialect_code"] for d in supported_dialects]
        assert updated_result["primary_dialect"] in supported_codes, (
            f"Invalid dialect after update: {updated_result['primary_dialect']}"
        )
    
    @given(
        audio_features_list=st.lists(
            audio_features_strategy(),
            min_size=3,
            max_size=10
        ),
        new_version=model_version_strategy(),
        model_data=model_data_strategy()
    )
    @settings(max_examples=10, deadline=15000)
    def test_property_concurrent_requests_during_update(
        self, audio_features_list, new_version, model_data
    ):
        """
        Property 5.3: Concurrent Request Handling During Update
        For any model update, concurrent requests must be handled without errors
        **Validates: Requirement 2.5 (no service interruption)**
        """
        service = DialectDetectorService()
        
        # Initialize service
        asyncio.run(service.detect_dialect(audio_features_list[0]))
        
        async def concurrent_test():
            # Start model update
            update_task = asyncio.create_task(
                service.deploy_model_update(
                    version=new_version,
                    model_data=model_data,
                    gradual_rollout=True
                )
            )
            
            # Make concurrent detection requests during update
            detection_tasks = [
                asyncio.create_task(service.detect_dialect(features))
                for features in audio_features_list
            ]
            
            # Wait for all tasks
            update_result = await update_task
            detection_results = await asyncio.gather(*detection_tasks, return_exceptions=True)
            
            return update_result, detection_results
        
        update_result, detection_results = asyncio.run(concurrent_test())
        
        # Property: Update should succeed
        assert update_result["success"] is True, (
            "Model update failed during concurrent requests"
        )
        
        # Property: All detection requests should succeed (no exceptions)
        for i, result in enumerate(detection_results):
            assert not isinstance(result, Exception), (
                f"Detection request {i} failed during update: {result}"
            )
            assert result is not None, (
                f"Detection request {i} returned None during update"
            )
            assert "primary_dialect" in result, (
                f"Detection request {i} missing primary_dialect during update"
            )
    
    @given(
        audio_features=audio_features_strategy(),
        version1=model_version_strategy(),
        version2=model_version_strategy(),
        model_data1=model_data_strategy(),
        model_data2=model_data_strategy()
    )
    @settings(max_examples=10, deadline=15000)
    def test_property_multiple_sequential_updates(
        self, audio_features, version1, version2, model_data1, model_data2
    ):
        """
        Property 5.4: Multiple Sequential Updates
        For any sequence of model updates, each update must succeed without breaking service
        **Validates: Requirement 2.5 (continuous model improvement capability)**
        """
        # Ensure versions are different
        assume(version1 != version2)
        
        service = DialectDetectorService()
        
        # Initial detection
        initial_result = asyncio.run(service.detect_dialect(audio_features))
        assert initial_result is not None
        
        # First update
        update1_result = asyncio.run(service.deploy_model_update(
            version=version1,
            model_data=model_data1
        ))
        assert update1_result["success"] is True, (
            f"First update to {version1} failed"
        )
        
        # Detection after first update
        result1 = asyncio.run(service.detect_dialect(audio_features))
        assert result1 is not None, "Service failed after first update"
        assert result1["model_version"] == version1, (
            f"Model version mismatch after first update: "
            f"expected {version1}, got {result1['model_version']}"
        )
        
        # Second update
        update2_result = asyncio.run(service.deploy_model_update(
            version=version2,
            model_data=model_data2
        ))
        assert update2_result["success"] is True, (
            f"Second update to {version2} failed"
        )
        
        # Detection after second update
        result2 = asyncio.run(service.detect_dialect(audio_features))
        assert result2 is not None, "Service failed after second update"
        assert result2["model_version"] == version2, (
            f"Model version mismatch after second update: "
            f"expected {version2}, got {result2['model_version']}"
        )
        
        # Property: Service remains functional through multiple updates
        assert 0 <= result2["confidence"] <= 1
        assert result2["detection_time"] < 3000
    
    @given(
        audio_features=audio_features_strategy(),
        new_version=model_version_strategy(),
        model_data=model_data_strategy()
    )
    @settings(max_examples=20, deadline=10000)
    def test_property_rollback_capability(
        self, audio_features, new_version, model_data
    ):
        """
        Property 5.5: Rollback Capability
        For any model update, the system must support rollback to previous version
        **Validates: Requirement 2.5 (safe model updates with rollback)**
        """
        service = DialectDetectorService()
        
        # Get initial version
        initial_result = asyncio.run(service.detect_dialect(audio_features))
        initial_version = initial_result["model_version"]
        
        # Deploy new version
        update_result = asyncio.run(service.deploy_model_update(
            version=new_version,
            model_data=model_data
        ))
        assert update_result["success"] is True
        
        # Verify new version is active
        new_result = asyncio.run(service.detect_dialect(audio_features))
        assert new_result["model_version"] == new_version
        
        # Rollback to initial version
        rollback_result = asyncio.run(service.rollback_model_version(initial_version))
        
        # Property: Rollback should succeed
        assert rollback_result["success"] is True, (
            f"Rollback to {initial_version} failed"
        )
        
        # Property: Service should use rolled-back version
        rollback_detection = asyncio.run(service.detect_dialect(audio_features))
        assert rollback_detection["model_version"] == initial_version, (
            f"Rollback failed: expected {initial_version}, "
            f"got {rollback_detection['model_version']}"
        )
        
        # Property: Service remains functional after rollback
        assert rollback_detection is not None
        assert 0 <= rollback_detection["confidence"] <= 1
        assert rollback_detection["detection_time"] < 3000
    
    @given(
        audio_features=audio_features_strategy(),
        candidate_version=model_version_strategy(),
        model_data=model_data_strategy(),
        traffic_split=traffic_split_strategy()
    )
    @settings(max_examples=10, deadline=15000)
    def test_property_ab_testing_no_interruption(
        self, audio_features, candidate_version, model_data, traffic_split
    ):
        """
        Property 5.6: A/B Testing Without Interruption
        For any A/B test setup, the service must continue operating without interruption
        **Validates: Requirement 2.5 (safe model testing)**
        """
        service = DialectDetectorService()
        
        # Initialize service
        initial_result = asyncio.run(service.detect_dialect(audio_features))
        assert initial_result is not None
        
        # Start A/B test
        test_id = f"test_{candidate_version}"
        ab_result = asyncio.run(service.start_model_ab_test(
            test_id=test_id,
            candidate_version=candidate_version,
            candidate_model_data=model_data,
            traffic_split=traffic_split,
            min_samples=10
        ))
        
        # Property: A/B test should start successfully
        assert ab_result["success"] is True, (
            f"A/B test failed to start for {candidate_version}"
        )
        
        # Property: Service remains functional during A/B test
        test_result = asyncio.run(service.detect_dialect(
            audio_features,
            session_id="ab_test_session"
        ))
        assert test_result is not None, (
            "Service unavailable during A/B test"
        )
        
        # Property: Result structure remains consistent
        assert set(initial_result.keys()) == set(test_result.keys()), (
            "Result structure changed during A/B test"
        )
        
        # Property: Model version should be either control or candidate
        control_version = service.continuous_learning.model_pipeline.get_active_version()
        assert test_result["model_version"] in [control_version, candidate_version], (
            f"Unexpected model version during A/B test: {test_result['model_version']}"
        )
        
        # Stop test
        stopped = service.stop_ab_test(test_id)
        assert stopped is True, "Failed to stop A/B test"
    
    @given(
        audio_features=audio_features_strategy(),
        new_version=model_version_strategy(),
        model_data=model_data_strategy()
    )
    @settings(max_examples=20, deadline=10000)
    def test_property_gradual_rollout_stability(
        self, audio_features, new_version, model_data
    ):
        """
        Property 5.7: Gradual Rollout Stability
        For any gradual rollout, the service must remain stable throughout the process
        **Validates: Requirement 2.5 (safe deployment strategy)**
        """
        service = DialectDetectorService()
        
        # Initialize
        initial_result = asyncio.run(service.detect_dialect(audio_features))
        
        # Deploy with gradual rollout
        update_result = asyncio.run(service.deploy_model_update(
            version=new_version,
            model_data=model_data,
            gradual_rollout=True
        ))
        
        # Property: Gradual rollout should succeed
        assert update_result["success"] is True
        assert update_result["gradual_rollout"] is True
        
        # Property: Service remains stable during rollout
        rollout_result = asyncio.run(service.detect_dialect(audio_features))
        assert rollout_result is not None
        assert 0 <= rollout_result["confidence"] <= 1
        assert rollout_result["detection_time"] < 3000
        
        # Property: New version should be active after rollout
        assert rollout_result["model_version"] == new_version
    
    @given(
        audio_features=audio_features_strategy(),
        new_version=model_version_strategy()
    )
    @settings(max_examples=20, deadline=10000)
    def test_property_model_version_tracking(
        self, audio_features, new_version
    ):
        """
        Property 5.8: Model Version Tracking
        For any detection, the result must include the model version used
        **Validates: Requirement 2.5 (transparency and traceability)**
        """
        service = DialectDetectorService()
        
        # Initial detection
        result1 = asyncio.run(service.detect_dialect(audio_features))
        
        # Property: Result must include model_version field
        assert "model_version" in result1, (
            "Detection result missing model_version field"
        )
        assert result1["model_version"] is not None
        assert isinstance(result1["model_version"], str)
        
        # Deploy new version
        asyncio.run(service.deploy_model_update(version=new_version))
        
        # Detection with new version
        result2 = asyncio.run(service.detect_dialect(audio_features))
        
        # Property: Model version should be updated
        assert result2["model_version"] == new_version, (
            f"Model version not updated: expected {new_version}, "
            f"got {result2['model_version']}"
        )
    
    @given(
        audio_features=audio_features_strategy(),
        versions=st.lists(
            model_version_strategy(),
            min_size=2,
            max_size=5,
            unique=True
        )
    )
    @settings(max_examples=10, deadline=20000)
    def test_property_multiple_versions_loaded(
        self, audio_features, versions
    ):
        """
        Property 5.9: Multiple Version Management
        For any set of model versions, the system must manage multiple loaded versions
        **Validates: Requirement 2.5 (flexible version management)**
        """
        service = DialectDetectorService()
        
        # Initialize
        asyncio.run(service.detect_dialect(audio_features))
        
        # Load multiple versions
        for version in versions:
            load_success = asyncio.run(
                service.continuous_learning.model_pipeline.load_model_version(
                    version,
                    {"type": "test", "version": version}
                )
            )
            assert load_success is True, f"Failed to load version {version}"
        
        # Property: All versions should be loaded
        loaded_versions = service.continuous_learning.model_pipeline.get_loaded_versions()
        for version in versions:
            assert version in loaded_versions, (
                f"Version {version} not in loaded versions: {loaded_versions}"
            )
        
        # Property: Service remains functional with multiple versions loaded
        result = asyncio.run(service.detect_dialect(audio_features))
        assert result is not None
        assert 0 <= result["confidence"] <= 1
    
    @given(
        audio_features=audio_features_strategy(),
        new_version=model_version_strategy(),
        model_data=model_data_strategy()
    )
    @settings(max_examples=20, deadline=10000)
    def test_property_update_preserves_configuration(
        self, audio_features, new_version, model_data
    ):
        """
        Property 5.10: Configuration Preservation
        For any model update, service configuration must be preserved
        **Validates: Requirement 2.5 (no degradation of existing functionality)**
        """
        service = DialectDetectorService()
        
        # Get initial configuration
        initial_threshold = service.confidence_threshold
        initial_supported = asyncio.run(service.get_supported_dialects())
        
        # Deploy new model
        asyncio.run(service.deploy_model_update(
            version=new_version,
            model_data=model_data
        ))
        
        # Property: Configuration should be preserved
        assert service.confidence_threshold == initial_threshold, (
            f"Confidence threshold changed: {initial_threshold} -> "
            f"{service.confidence_threshold}"
        )
        
        # Property: Supported dialects should remain available
        updated_supported = asyncio.run(service.get_supported_dialects())
        assert len(updated_supported) > 0, (
            "No supported dialects after update"
        )
        
        # Property: Service functionality preserved
        result = asyncio.run(service.detect_dialect(audio_features))
        assert result is not None
        assert "primary_dialect" in result


class TestModelUpdateErrorHandling:
    """
    Property-based tests for error handling during model updates
    **Validates: Requirement 2.5 (robust update process)**
    """
    
    @given(audio_features=audio_features_strategy())
    @settings(max_examples=10, deadline=10000)
    def test_property_invalid_version_handled_gracefully(self, audio_features):
        """
        Property 5.11: Invalid Version Handling
        For any invalid version identifier, the system must handle it gracefully
        **Validates: Requirement 2.5 (robust error handling)**
        """
        service = DialectDetectorService()
        
        # Initialize
        initial_result = asyncio.run(service.detect_dialect(audio_features))
        initial_version = initial_result["model_version"]
        
        # Try to switch to non-existent version
        switch_result = asyncio.run(
            service.continuous_learning.model_pipeline.switch_active_version(
                "non_existent_version"
            )
        )
        
        # Property: Invalid switch should fail gracefully
        assert switch_result is False, (
            "Invalid version switch should return False"
        )
        
        # Property: Service should remain on original version
        current_result = asyncio.run(service.detect_dialect(audio_features))
        assert current_result["model_version"] == initial_version, (
            "Service version changed despite invalid switch"
        )
        
        # Property: Service remains functional
        assert current_result is not None
        assert 0 <= current_result["confidence"] <= 1
    
    @given(
        audio_features=audio_features_strategy(),
        new_version=model_version_strategy()
    )
    @settings(max_examples=10, deadline=10000)
    def test_property_concurrent_update_prevention(
        self, audio_features, new_version
    ):
        """
        Property 5.12: Concurrent Update Prevention
        For any concurrent update attempts, only one should proceed
        **Validates: Requirement 2.5 (safe update process)**
        """
        service = DialectDetectorService()
        
        # Initialize
        asyncio.run(service.detect_dialect(audio_features))
        
        # Load the version first
        asyncio.run(
            service.continuous_learning.model_pipeline.load_model_version(
                new_version,
                {"type": "test"}
            )
        )
        
        # Set update in progress
        service.continuous_learning.model_pipeline.update_in_progress = True
        
        # Try to switch version while update in progress
        switch_result = asyncio.run(
            service.continuous_learning.model_pipeline.switch_active_version(
                new_version
            )
        )
        
        # Property: Concurrent update should be blocked
        assert switch_result is False, (
            "Concurrent update should be prevented"
        )
        
        # Reset flag
        service.continuous_learning.model_pipeline.update_in_progress = False
        
        # Property: Service remains functional
        result = asyncio.run(service.detect_dialect(audio_features))
        assert result is not None
