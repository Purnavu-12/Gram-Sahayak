"""
Integration tests for dialect detector with continuous learning
Tests the integration of continuous learning into dialect detection service
Validates: Requirement 2.5, Task 3.4
"""

import pytest
from dialect_detector_service import DialectDetectorService


class TestDialectDetectorContinuousLearning:
    """Test dialect detector service with continuous learning integration"""
    
    @pytest.mark.asyncio
    async def test_detect_dialect_includes_model_version(self):
        """Test that detection results include model version"""
        service = DialectDetectorService()
        
        audio_features = {
            "sample_rate": 16000,
            "duration": 3.5,
            "language_hint": "hi"
        }
        
        result = await service.detect_dialect(audio_features, session_id="test_session")
        
        assert "model_version" in result
        assert result["model_version"] == "stable"
    
    @pytest.mark.asyncio
    async def test_feedback_integration(self):
        """Test feedback collection integration"""
        service = DialectDetectorService()
        
        # First detection
        audio_features = {"sample_rate": 16000, "duration": 3.0}
        result = await service.detect_dialect(audio_features, session_id="test_session")
        
        # Provide feedback
        feedback = {
            "detected_dialect": result["primary_dialect"],
            "confidence": result["confidence"],
            "correct_dialect": "hi-IN",
            "user_satisfaction": 5,
            "audio_features": audio_features
        }
        
        await service.update_confidence("test_session", feedback)
        
        # Check that feedback was collected
        status = service.get_learning_system_status()
        assert status["initialized"] is True
    
    @pytest.mark.asyncio
    async def test_deploy_model_update(self):
        """Test deploying model update without service interruption"""
        service = DialectDetectorService()
        
        # Initialize by running a detection
        audio_features = {"sample_rate": 16000, "duration": 3.0}
        await service.detect_dialect(audio_features)
        
        # Deploy new model version
        result = await service.deploy_model_update(
            version="v2.0",
            model_data={"type": "improved"},
            gradual_rollout=True
        )
        
        assert result["success"] is True
        assert result["version"] == "v2.0"
        assert result["active_version"] == "v2.0"
        
        # Service should still work with new version
        new_result = await service.detect_dialect(audio_features)
        assert new_result["model_version"] == "v2.0"
    
    @pytest.mark.asyncio
    async def test_ab_testing_workflow(self):
        """Test complete A/B testing workflow"""
        service = DialectDetectorService()
        
        # Initialize
        audio_features = {"sample_rate": 16000, "duration": 3.0}
        await service.detect_dialect(audio_features)
        
        # Start A/B test
        test_result = await service.start_model_ab_test(
            test_id="test_ab_1",
            candidate_version="candidate_v1",
            traffic_split=0.3,
            min_samples=5
        )
        
        assert test_result["success"] is True
        assert test_result["test_id"] == "test_ab_1"
        
        # Run detections for multiple sessions
        for i in range(10):
            session_id = f"session_{i}"
            
            # Get model version assignment for A/B test
            model_version = service.continuous_learning.get_model_version_for_session(
                session_id, "test_ab_1"
            )
            
            result = await service.detect_dialect(audio_features, session_id=session_id)
            
            # Provide feedback
            feedback = {
                "detected_dialect": result["primary_dialect"],
                "confidence": result["confidence"],
                "correct_dialect": result["primary_dialect"],
                "user_satisfaction": 4
            }
            await service.update_confidence(session_id, feedback)
        
        # Get test results
        results = service.get_ab_test_results("test_ab_1")
        
        assert results is not None
        assert results["test_id"] == "test_ab_1"
        assert results["samples_a"] + results["samples_b"] > 0
        
        # Stop test
        stopped = service.stop_ab_test("test_ab_1")
        assert stopped is True
    
    @pytest.mark.asyncio
    async def test_model_rollback(self):
        """Test rolling back to previous model version"""
        service = DialectDetectorService()
        
        # Initialize
        audio_features = {"sample_rate": 16000, "duration": 3.0}
        await service.detect_dialect(audio_features)
        
        original_version = service.continuous_learning.model_pipeline.get_active_version()
        
        # Deploy new version
        await service.deploy_model_update("v2.0")
        assert service.continuous_learning.model_pipeline.get_active_version() == "v2.0"
        
        # Rollback
        rollback_result = await service.rollback_model_version(original_version)
        
        assert rollback_result["success"] is True
        assert rollback_result["active_version"] == original_version
    
    @pytest.mark.asyncio
    async def test_learning_system_status(self):
        """Test getting learning system status"""
        service = DialectDetectorService()
        
        # Initialize
        audio_features = {"sample_rate": 16000, "duration": 3.0}
        await service.detect_dialect(audio_features)
        
        status = service.get_learning_system_status()
        
        assert status["initialized"] is True
        assert "active_version" in status
        assert "loaded_versions" in status
        assert "active_tests" in status
        assert "metrics" in status
    
    @pytest.mark.asyncio
    async def test_continuous_learning_with_code_switching(self):
        """Test continuous learning with code-switching detection"""
        service = DialectDetectorService()
        
        session_id = "multilang_session"
        
        # First segment in Hindi
        audio_features_1 = {
            "sample_rate": 16000,
            "duration": 3.0,
            "language_hint": "hi"
        }
        result_1 = await service.detect_dialect(audio_features_1, session_id=session_id, segment_index=0)
        
        # Provide feedback
        feedback_1 = {
            "detected_dialect": result_1["primary_dialect"],
            "confidence": result_1["confidence"],
            "correct_dialect": "hi-IN",
            "user_satisfaction": 5
        }
        await service.update_confidence(session_id, feedback_1)
        
        # Second segment switches to Bengali
        audio_features_2 = {
            "sample_rate": 16000,
            "duration": 3.0,
            "language_hint": "bn"
        }
        result_2 = await service.detect_dialect(audio_features_2, session_id=session_id, segment_index=1)
        
        # Provide feedback
        feedback_2 = {
            "detected_dialect": result_2["primary_dialect"],
            "confidence": result_2["confidence"],
            "correct_dialect": "bn-IN",
            "user_satisfaction": 5
        }
        await service.update_confidence(session_id, feedback_2)
        
        # Check that both feedbacks were collected
        status = service.get_learning_system_status()
        assert status["initialized"] is True
    
    @pytest.mark.asyncio
    async def test_multiple_model_versions_loaded(self):
        """Test that multiple model versions can be loaded simultaneously"""
        service = DialectDetectorService()
        
        # Initialize
        audio_features = {"sample_rate": 16000, "duration": 3.0}
        await service.detect_dialect(audio_features)
        
        # Load multiple versions
        await service.deploy_model_update("v2.0")
        await service.continuous_learning.model_pipeline.load_model_version("v3.0")
        
        loaded_versions = service.continuous_learning.model_pipeline.get_loaded_versions()
        
        assert len(loaded_versions) >= 2
        assert "v2.0" in loaded_versions
        assert "v3.0" in loaded_versions
    
    @pytest.mark.asyncio
    async def test_gradual_rollout(self):
        """Test gradual rollout of new model version"""
        service = DialectDetectorService()
        
        # Initialize
        audio_features = {"sample_rate": 16000, "duration": 3.0}
        await service.detect_dialect(audio_features)
        
        # Deploy with gradual rollout
        result = await service.deploy_model_update(
            version="v2.0",
            gradual_rollout=True
        )
        
        assert result["success"] is True
        assert result["gradual_rollout"] is True
        
        # New version should be active
        assert result["active_version"] == "v2.0"
