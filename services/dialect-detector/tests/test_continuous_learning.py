"""
Unit tests for continuous learning system
Tests feedback collection, model updates, and A/B testing
Validates: Requirement 2.5, Task 3.4
"""

import pytest
import asyncio
from continuous_learning import (
    ContinuousLearningSystem,
    FeedbackCollector,
    ModelUpdatePipeline,
    ABTestingManager,
    ModelVersion,
    FeedbackEntry,
    ModelMetrics
)


class TestFeedbackCollector:
    """Test feedback collection and metrics tracking"""
    
    @pytest.mark.asyncio
    async def test_collect_feedback_basic(self):
        """Test basic feedback collection"""
        collector = FeedbackCollector()
        
        await collector.collect_feedback(
            session_id="test_session_1",
            detected_dialect="hi-IN",
            confidence=0.85,
            user_correction="hi-IN",
            user_satisfaction=5
        )
        
        assert len(collector.feedback_buffer) == 1
        assert collector.feedback_buffer[0].session_id == "test_session_1"
        assert collector.feedback_buffer[0].detected_dialect == "hi-IN"
    
    @pytest.mark.asyncio
    async def test_metrics_update_accuracy(self):
        """Test accuracy metrics calculation"""
        collector = FeedbackCollector()
        
        # Correct prediction
        await collector.collect_feedback(
            session_id="test_1",
            detected_dialect="hi-IN",
            confidence=0.9,
            user_correction="hi-IN"
        )
        
        # Incorrect prediction
        await collector.collect_feedback(
            session_id="test_2",
            detected_dialect="hi-IN",
            confidence=0.7,
            user_correction="bn-IN"
        )
        
        metrics = collector.get_metrics(ModelVersion.STABLE.value)
        assert metrics["accuracy"] == 0.5  # 1 correct out of 2
        assert metrics["total_predictions"] == 2
    
    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """Test feedback batch processing"""
        collector = FeedbackCollector()
        collector.buffer_size = 5
        
        # Add feedback up to buffer size
        for i in range(5):
            await collector.collect_feedback(
                session_id=f"test_{i}",
                detected_dialect="hi-IN",
                confidence=0.8
            )
        
        # Buffer should be cleared after processing
        assert len(collector.feedback_buffer) == 0


class TestModelUpdatePipeline:
    """Test model update pipeline without service interruption"""
    
    @pytest.mark.asyncio
    async def test_load_model_version(self):
        """Test loading a new model version"""
        pipeline = ModelUpdatePipeline()
        
        success = await pipeline.load_model_version(
            "v2.0",
            {"weights": "test_weights"}
        )
        
        assert success is True
        assert "v2.0" in pipeline.loaded_models
        assert pipeline.loaded_models["v2.0"]["status"] == "loaded"
    
    @pytest.mark.asyncio
    async def test_switch_active_version(self):
        """Test switching active version without interruption"""
        pipeline = ModelUpdatePipeline()
        
        # Load new version
        await pipeline.load_model_version("v2.0")
        
        # Switch to new version
        success = await pipeline.switch_active_version("v2.0")
        
        assert success is True
        assert pipeline.get_active_version() == "v2.0"
        assert pipeline.loaded_models["v2.0"]["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_rollback_version(self):
        """Test rolling back to previous version"""
        pipeline = ModelUpdatePipeline()
        
        # Load initial stable version
        await pipeline.load_model_version(ModelVersion.STABLE.value)
        
        # Load and switch to v2.0
        await pipeline.load_model_version("v2.0")
        await pipeline.switch_active_version("v2.0")
        
        old_version = ModelVersion.STABLE.value
        
        # Rollback
        success = await pipeline.rollback_version(old_version)
        
        assert success is True
        assert pipeline.get_active_version() == old_version
    
    @pytest.mark.asyncio
    async def test_concurrent_updates_blocked(self):
        """Test that concurrent updates are blocked"""
        pipeline = ModelUpdatePipeline()
        
        await pipeline.load_model_version("v2.0")
        await pipeline.load_model_version("v3.0")
        
        # Start first update
        pipeline.update_in_progress = True
        
        # Try second update
        success = await pipeline.switch_active_version("v3.0")
        
        assert success is False  # Should be blocked


class TestABTestingManager:
    """Test A/B testing for model versions"""
    
    def test_create_ab_test(self):
        """Test creating an A/B test"""
        collector = FeedbackCollector()
        ab_manager = ABTestingManager(collector)
        
        success = ab_manager.create_ab_test(
            test_id="test_1",
            version_a="stable",
            version_b="candidate",
            traffic_split=0.2
        )
        
        assert success is True
        assert "test_1" in ab_manager.active_tests
        assert ab_manager.active_tests["test_1"]["traffic_split"] == 0.2
    
    def test_assign_version_consistent(self):
        """Test that version assignment is consistent for same session"""
        collector = FeedbackCollector()
        ab_manager = ABTestingManager(collector)
        
        ab_manager.create_ab_test(
            test_id="test_1",
            version_a="stable",
            version_b="candidate",
            traffic_split=0.5
        )
        
        # Same session should get same version
        version1 = ab_manager.assign_version("session_123", "test_1")
        version2 = ab_manager.assign_version("session_123", "test_1")
        
        assert version1 == version2
    
    def test_traffic_split_distribution(self):
        """Test that traffic split is approximately correct"""
        collector = FeedbackCollector()
        ab_manager = ABTestingManager(collector)
        
        ab_manager.create_ab_test(
            test_id="test_1",
            version_a="stable",
            version_b="candidate",
            traffic_split=0.3
        )
        
        # Assign many sessions
        assignments = []
        for i in range(1000):
            version = ab_manager.assign_version(f"session_{i}", "test_1")
            assignments.append(version)
        
        # Check distribution (should be ~30% candidate, ~70% stable)
        candidate_count = assignments.count("candidate")
        ratio = candidate_count / len(assignments)
        
        assert 0.25 < ratio < 0.35  # Allow some variance
    
    @pytest.mark.asyncio
    async def test_get_test_results(self):
        """Test getting A/B test results"""
        collector = FeedbackCollector()
        ab_manager = ABTestingManager(collector)
        
        ab_manager.create_ab_test(
            test_id="test_1",
            version_a="stable",
            version_b="candidate",
            traffic_split=0.5,
            min_samples=5  # Lower threshold for test
        )
        
        # Assign sessions to get samples
        for i in range(10):
            ab_manager.assign_version(f"session_{i}", "test_1")
        
        # Add some feedback for both versions
        for i in range(10):
            await collector.collect_feedback(
                session_id=f"session_{i}",
                detected_dialect="hi-IN",
                confidence=0.85,
                user_correction="hi-IN",
                model_version="stable" if i < 5 else "candidate"
            )
        
        results = ab_manager.get_test_results("test_1")
        
        assert results is not None
        assert results["test_id"] == "test_1"
        assert results["samples_a"] + results["samples_b"] >= 10


class TestContinuousLearningSystem:
    """Test integrated continuous learning system"""
    
    @pytest.mark.asyncio
    async def test_system_initialization(self):
        """Test system initialization"""
        system = ContinuousLearningSystem()
        
        await system.initialize()
        
        assert system.initialized is True
        assert ModelVersion.STABLE.value in system.model_pipeline.loaded_models
    
    @pytest.mark.asyncio
    async def test_collect_feedback_integration(self):
        """Test feedback collection through system"""
        system = ContinuousLearningSystem()
        await system.initialize()
        
        await system.collect_feedback(
            session_id="test_session",
            detected_dialect="hi-IN",
            confidence=0.9,
            user_correction="hi-IN",
            user_satisfaction=5
        )
        
        metrics = system.feedback_collector.get_metrics(ModelVersion.STABLE.value)
        assert metrics["total_predictions"] > 0
    
    @pytest.mark.asyncio
    async def test_deploy_new_model(self):
        """Test deploying new model without interruption"""
        system = ContinuousLearningSystem()
        await system.initialize()
        
        success = await system.deploy_new_model(
            version="v2.0",
            model_data={"type": "improved", "version": "2.0.0"}
        )
        
        assert success is True
        assert system.model_pipeline.get_active_version() == "v2.0"
    
    @pytest.mark.asyncio
    async def test_start_ab_test_integration(self):
        """Test starting A/B test through system"""
        system = ContinuousLearningSystem()
        await system.initialize()
        
        success = await system.start_ab_test(
            test_id="integration_test",
            candidate_version="candidate_v1",
            traffic_split=0.2
        )
        
        assert success is True
        assert "integration_test" in system.ab_testing.active_tests
    
    @pytest.mark.asyncio
    async def test_model_version_assignment(self):
        """Test model version assignment for sessions"""
        system = ContinuousLearningSystem()
        await system.initialize()
        
        # Without A/B test, should get active version
        version = system.get_model_version_for_session("session_1")
        assert version == ModelVersion.STABLE.value
        
        # With A/B test, should get assigned version
        await system.start_ab_test(
            test_id="test_1",
            candidate_version="candidate",
            traffic_split=0.5
        )
        
        version = system.get_model_version_for_session("session_2", "test_1")
        assert version in ["stable", "candidate"]
    
    @pytest.mark.asyncio
    async def test_system_status(self):
        """Test getting system status"""
        system = ContinuousLearningSystem()
        await system.initialize()
        
        status = system.get_system_status()
        
        assert status["initialized"] is True
        assert "active_version" in status
        assert "loaded_versions" in status
        assert "metrics" in status


class TestModelMetrics:
    """Test model metrics calculations"""
    
    def test_accuracy_calculation(self):
        """Test accuracy calculation"""
        metrics = ModelMetrics(version="test")
        metrics.feedback_count = 10
        metrics.correct_predictions = 8
        
        assert metrics.accuracy == 0.8
    
    def test_performance_score(self):
        """Test combined performance score"""
        metrics = ModelMetrics(version="test")
        metrics.feedback_count = 10
        metrics.correct_predictions = 9
        metrics.average_confidence = 0.85
        metrics.average_satisfaction = 4.5
        
        # Score = 0.5 * 0.9 + 0.3 * 0.9 + 0.2 * 0.85
        expected_score = 0.5 * 0.9 + 0.3 * (4.5/5.0) + 0.2 * 0.85
        
        assert abs(metrics.performance_score - expected_score) < 0.01
