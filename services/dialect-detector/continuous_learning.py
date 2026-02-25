"""
Continuous Learning System for Dialect Detector
Implements user feedback integration, model update pipeline, and A/B testing
Validates: Requirement 2.5
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import json
import hashlib


class ModelVersion(Enum):
    """Model version identifiers for A/B testing"""
    STABLE = "stable"
    CANDIDATE = "candidate"
    EXPERIMENTAL = "experimental"


@dataclass
class FeedbackEntry:
    """User feedback entry for model improvement"""
    session_id: str
    timestamp: float
    detected_dialect: str
    confidence: float
    user_correction: Optional[str] = None
    user_satisfaction: Optional[int] = None  # 1-5 scale
    audio_features: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    model_version: str = ModelVersion.STABLE.value


@dataclass
class ModelMetrics:
    """Performance metrics for a model version"""
    version: str
    total_predictions: int = 0
    correct_predictions: int = 0
    average_confidence: float = 0.0
    average_satisfaction: float = 0.0
    feedback_count: int = 0
    last_updated: float = field(default_factory=time.time)
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy from feedback"""
        if self.feedback_count == 0:
            return 0.0
        return self.correct_predictions / self.feedback_count
    
    @property
    def performance_score(self) -> float:
        """Combined performance score for model comparison"""
        # Weight: 50% accuracy, 30% satisfaction, 20% confidence
        return (
            0.5 * self.accuracy +
            0.3 * (self.average_satisfaction / 5.0) +
            0.2 * self.average_confidence
        )


class FeedbackCollector:
    """
    Collects and stores user feedback for model improvement
    Integrates feedback into training pipeline
    """
    
    def __init__(self, storage_path: str = "/tmp/feedback"):
        self.storage_path = storage_path
        self.feedback_buffer: List[FeedbackEntry] = []
        self.buffer_size = 100  # Batch size for processing
        self.metrics_by_version: Dict[str, ModelMetrics] = {}
    
    async def collect_feedback(
        self,
        session_id: str,
        detected_dialect: str,
        confidence: float,
        user_correction: Optional[str] = None,
        user_satisfaction: Optional[int] = None,
        audio_features: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        model_version: str = ModelVersion.STABLE.value
    ) -> None:
        """
        Collect user feedback for a detection
        
        Args:
            session_id: Session identifier
            detected_dialect: Dialect detected by model
            confidence: Model confidence score
            user_correction: User-provided correct dialect (if detection was wrong)
            user_satisfaction: User satisfaction rating (1-5)
            audio_features: Audio features used for detection
            context: Additional context information
            model_version: Model version that made the prediction
        """
        feedback = FeedbackEntry(
            session_id=session_id,
            timestamp=time.time(),
            detected_dialect=detected_dialect,
            confidence=confidence,
            user_correction=user_correction,
            user_satisfaction=user_satisfaction,
            audio_features=audio_features or {},
            context=context or {},
            model_version=model_version
        )
        
        self.feedback_buffer.append(feedback)
        
        # Update metrics
        await self._update_metrics(feedback)
        
        # Process buffer if full
        if len(self.feedback_buffer) >= self.buffer_size:
            await self._process_feedback_batch()
    
    async def _update_metrics(self, feedback: FeedbackEntry) -> None:
        """Update metrics for the model version"""
        version = feedback.model_version
        
        if version not in self.metrics_by_version:
            self.metrics_by_version[version] = ModelMetrics(version=version)
        
        metrics = self.metrics_by_version[version]
        metrics.total_predictions += 1
        
        # Update accuracy if user provided correction
        if feedback.user_correction is not None:
            metrics.feedback_count += 1
            is_correct = feedback.detected_dialect == feedback.user_correction
            if is_correct:
                metrics.correct_predictions += 1
        
        # Update average confidence
        total_conf = metrics.average_confidence * (metrics.total_predictions - 1)
        metrics.average_confidence = (total_conf + feedback.confidence) / metrics.total_predictions
        
        # Update average satisfaction
        if feedback.user_satisfaction is not None:
            if metrics.feedback_count > 0:
                total_sat = metrics.average_satisfaction * (metrics.feedback_count - 1)
                metrics.average_satisfaction = (total_sat + feedback.user_satisfaction) / metrics.feedback_count
            else:
                metrics.average_satisfaction = feedback.user_satisfaction
        
        metrics.last_updated = time.time()
    
    async def _process_feedback_batch(self) -> None:
        """Process accumulated feedback batch"""
        if not self.feedback_buffer:
            return
        
        # In production, this would:
        # 1. Store feedback in persistent storage
        # 2. Trigger model retraining pipeline
        # 3. Update model weights based on feedback
        
        # For now, simulate processing
        batch_data = [
            {
                "session_id": f.session_id,
                "timestamp": f.timestamp,
                "detected_dialect": f.detected_dialect,
                "confidence": f.confidence,
                "user_correction": f.user_correction,
                "user_satisfaction": f.user_satisfaction,
                "model_version": f.model_version
            }
            for f in self.feedback_buffer
        ]
        
        # Simulate async processing
        await asyncio.sleep(0.01)
        
        # Clear buffer after processing
        self.feedback_buffer.clear()
    
    def get_metrics(self, version: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for a specific version or all versions"""
        if version:
            metrics = self.metrics_by_version.get(version)
            if not metrics:
                return {}
            return {
                "version": metrics.version,
                "total_predictions": metrics.total_predictions,
                "accuracy": metrics.accuracy,
                "average_confidence": metrics.average_confidence,
                "average_satisfaction": metrics.average_satisfaction,
                "performance_score": metrics.performance_score,
                "last_updated": metrics.last_updated
            }
        
        return {
            version: {
                "version": m.version,
                "total_predictions": m.total_predictions,
                "accuracy": m.accuracy,
                "average_confidence": m.average_confidence,
                "average_satisfaction": m.average_satisfaction,
                "performance_score": m.performance_score,
                "last_updated": m.last_updated
            }
            for version, m in self.metrics_by_version.items()
        }


class ModelUpdatePipeline:
    """
    Manages model updates without service interruption
    Implements blue-green deployment strategy
    """
    
    def __init__(self):
        self.active_version = ModelVersion.STABLE.value
        self.loaded_models: Dict[str, Any] = {}
        self.update_in_progress = False
        self.update_lock = asyncio.Lock()
    
    async def load_model_version(
        self,
        version: str,
        model_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Load a new model version without interrupting service
        
        Args:
            version: Version identifier
            model_data: Model weights and configuration
        
        Returns:
            True if load successful, False otherwise
        """
        async with self.update_lock:
            try:
                # Simulate model loading
                # In production, this would load actual model weights
                self.loaded_models[version] = {
                    "version": version,
                    "loaded_at": time.time(),
                    "weights": model_data or {},
                    "status": "loaded"
                }
                
                # Simulate loading time
                await asyncio.sleep(0.1)
                
                return True
            except Exception as e:
                print(f"Error loading model version {version}: {e}")
                return False
    
    async def switch_active_version(
        self,
        new_version: str,
        gradual_rollout: bool = True,
        rollout_percentage: float = 0.1
    ) -> bool:
        """
        Switch active model version without service interruption
        
        Args:
            new_version: Version to switch to
            gradual_rollout: Whether to gradually roll out the new version
            rollout_percentage: Initial percentage of traffic for gradual rollout
        
        Returns:
            True if switch successful, False otherwise
        """
        async with self.update_lock:
            if new_version not in self.loaded_models:
                print(f"Model version {new_version} not loaded")
                return False
            
            if self.update_in_progress:
                print("Update already in progress")
                return False
            
            try:
                self.update_in_progress = True
                
                # Simulate gradual rollout
                if gradual_rollout:
                    # In production, this would gradually shift traffic
                    await asyncio.sleep(0.05)
                
                # Switch active version
                old_version = self.active_version
                self.active_version = new_version
                
                # Mark old version as inactive (but keep loaded for rollback)
                if old_version in self.loaded_models:
                    self.loaded_models[old_version]["status"] = "inactive"
                
                self.loaded_models[new_version]["status"] = "active"
                
                self.update_in_progress = False
                return True
                
            except Exception as e:
                print(f"Error switching to version {new_version}: {e}")
                self.update_in_progress = False
                return False
    
    async def rollback_version(self, target_version: Optional[str] = None) -> bool:
        """
        Rollback to a previous model version
        
        Args:
            target_version: Version to rollback to (defaults to most recent inactive)
        
        Returns:
            True if rollback successful, False otherwise
        """
        async with self.update_lock:
            if not target_version:
                # Find most recent inactive version
                inactive_versions = [
                    (v, data["loaded_at"])
                    for v, data in self.loaded_models.items()
                    if data["status"] == "inactive"
                ]
                
                if not inactive_versions:
                    print("No inactive version available for rollback")
                    return False
                
                target_version = max(inactive_versions, key=lambda x: x[1])[0]
            
            if target_version not in self.loaded_models:
                print(f"Version {target_version} not available for rollback")
                return False
            
            # Switch back to target version
            old_active = self.active_version
            self.active_version = target_version
            
            self.loaded_models[target_version]["status"] = "active"
            if old_active in self.loaded_models:
                self.loaded_models[old_active]["status"] = "inactive"
            
            return True
    
    def get_active_version(self) -> str:
        """Get currently active model version"""
        return self.active_version
    
    def get_loaded_versions(self) -> List[str]:
        """Get list of all loaded model versions"""
        return list(self.loaded_models.keys())
    
    def get_version_info(self, version: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model version"""
        return self.loaded_models.get(version)


class ABTestingManager:
    """
    Manages A/B testing for model versions
    Routes traffic between versions and tracks performance
    """
    
    def __init__(self, feedback_collector: FeedbackCollector):
        self.feedback_collector = feedback_collector
        self.active_tests: Dict[str, Dict[str, Any]] = {}
        self.test_assignments: Dict[str, str] = {}  # session_id -> version
    
    def create_ab_test(
        self,
        test_id: str,
        version_a: str,
        version_b: str,
        traffic_split: float = 0.5,
        min_samples: int = 100
    ) -> bool:
        """
        Create a new A/B test between two model versions
        
        Args:
            test_id: Unique test identifier
            version_a: First model version (control)
            version_b: Second model version (treatment)
            traffic_split: Percentage of traffic for version_b (0.0-1.0)
            min_samples: Minimum samples needed for statistical significance
        
        Returns:
            True if test created successfully
        """
        if test_id in self.active_tests:
            print(f"Test {test_id} already exists")
            return False
        
        self.active_tests[test_id] = {
            "test_id": test_id,
            "version_a": version_a,
            "version_b": version_b,
            "traffic_split": traffic_split,
            "min_samples": min_samples,
            "created_at": time.time(),
            "status": "active",
            "samples_a": 0,
            "samples_b": 0
        }
        
        return True
    
    def assign_version(self, session_id: str, test_id: str) -> str:
        """
        Assign a model version to a session for A/B testing
        
        Args:
            session_id: Session identifier
            test_id: Test identifier
        
        Returns:
            Assigned model version
        """
        if test_id not in self.active_tests:
            return ModelVersion.STABLE.value
        
        # Check if session already assigned
        if session_id in self.test_assignments:
            return self.test_assignments[session_id]
        
        test = self.active_tests[test_id]
        
        # Use consistent hashing for stable assignment
        hash_value = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
        assignment_value = (hash_value % 100) / 100.0
        
        if assignment_value < test["traffic_split"]:
            assigned_version = test["version_b"]
            test["samples_b"] += 1
        else:
            assigned_version = test["version_a"]
            test["samples_a"] += 1
        
        self.test_assignments[session_id] = assigned_version
        return assigned_version
    
    def get_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """
        Get results for an A/B test
        
        Args:
            test_id: Test identifier
        
        Returns:
            Test results including metrics for both versions
        """
        if test_id not in self.active_tests:
            return None
        
        test = self.active_tests[test_id]
        
        # Get metrics for both versions
        metrics_a = self.feedback_collector.get_metrics(test["version_a"])
        metrics_b = self.feedback_collector.get_metrics(test["version_b"])
        
        # Calculate statistical significance (simplified)
        samples_a = test["samples_a"]
        samples_b = test["samples_b"]
        min_samples = test["min_samples"]
        
        has_enough_samples = samples_a >= min_samples and samples_b >= min_samples
        
        # Determine winner based on performance score
        winner = None
        if has_enough_samples and metrics_a and metrics_b:
            score_a = metrics_a.get("performance_score", 0)
            score_b = metrics_b.get("performance_score", 0)
            
            # Require at least 5% improvement to declare winner
            if score_b > score_a * 1.05:
                winner = test["version_b"]
            elif score_a > score_b * 1.05:
                winner = test["version_a"]
        
        return {
            "test_id": test_id,
            "version_a": test["version_a"],
            "version_b": test["version_b"],
            "traffic_split": test["traffic_split"],
            "samples_a": samples_a,
            "samples_b": samples_b,
            "metrics_a": metrics_a,
            "metrics_b": metrics_b,
            "has_enough_samples": has_enough_samples,
            "winner": winner,
            "status": test["status"]
        }
    
    def stop_test(self, test_id: str) -> bool:
        """
        Stop an active A/B test
        
        Args:
            test_id: Test identifier
        
        Returns:
            True if test stopped successfully
        """
        if test_id not in self.active_tests:
            return False
        
        self.active_tests[test_id]["status"] = "stopped"
        return True
    
    def get_active_tests(self) -> List[str]:
        """Get list of active test IDs"""
        return [
            test_id
            for test_id, test in self.active_tests.items()
            if test["status"] == "active"
        ]


class ContinuousLearningSystem:
    """
    Main continuous learning system that integrates all components
    Validates: Requirement 2.5
    """
    
    def __init__(self):
        self.feedback_collector = FeedbackCollector()
        self.model_pipeline = ModelUpdatePipeline()
        self.ab_testing = ABTestingManager(self.feedback_collector)
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize the continuous learning system"""
        if self.initialized:
            return
        
        # Load stable model version
        await self.model_pipeline.load_model_version(
            ModelVersion.STABLE.value,
            {"type": "stable", "version": "1.0.0"}
        )
        
        self.initialized = True
    
    async def collect_feedback(
        self,
        session_id: str,
        detected_dialect: str,
        confidence: float,
        user_correction: Optional[str] = None,
        user_satisfaction: Optional[int] = None,
        audio_features: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Collect user feedback for model improvement
        
        Args:
            session_id: Session identifier
            detected_dialect: Dialect detected by model
            confidence: Model confidence score
            user_correction: User-provided correct dialect
            user_satisfaction: User satisfaction rating (1-5)
            audio_features: Audio features used for detection
            context: Additional context information
        """
        # Get model version for this session (from A/B test if active)
        model_version = self.ab_testing.test_assignments.get(
            session_id,
            self.model_pipeline.get_active_version()
        )
        
        await self.feedback_collector.collect_feedback(
            session_id=session_id,
            detected_dialect=detected_dialect,
            confidence=confidence,
            user_correction=user_correction,
            user_satisfaction=user_satisfaction,
            audio_features=audio_features,
            context=context,
            model_version=model_version
        )
    
    async def deploy_new_model(
        self,
        version: str,
        model_data: Optional[Dict[str, Any]] = None,
        gradual_rollout: bool = True
    ) -> bool:
        """
        Deploy a new model version without service interruption
        
        Args:
            version: Version identifier
            model_data: Model weights and configuration
            gradual_rollout: Whether to gradually roll out the new version
        
        Returns:
            True if deployment successful
        """
        # Load new model version
        load_success = await self.model_pipeline.load_model_version(version, model_data)
        if not load_success:
            return False
        
        # Switch to new version
        switch_success = await self.model_pipeline.switch_active_version(
            version,
            gradual_rollout=gradual_rollout
        )
        
        return switch_success
    
    async def start_ab_test(
        self,
        test_id: str,
        candidate_version: str,
        candidate_model_data: Optional[Dict[str, Any]] = None,
        traffic_split: float = 0.1,
        min_samples: int = 100
    ) -> bool:
        """
        Start an A/B test with a candidate model version
        
        Args:
            test_id: Unique test identifier
            candidate_version: Candidate model version to test
            candidate_model_data: Model weights and configuration
            traffic_split: Percentage of traffic for candidate (0.0-1.0)
            min_samples: Minimum samples for statistical significance
        
        Returns:
            True if test started successfully
        """
        # Load candidate model
        load_success = await self.model_pipeline.load_model_version(
            candidate_version,
            candidate_model_data
        )
        if not load_success:
            return False
        
        # Create A/B test
        control_version = self.model_pipeline.get_active_version()
        test_created = self.ab_testing.create_ab_test(
            test_id=test_id,
            version_a=control_version,
            version_b=candidate_version,
            traffic_split=traffic_split,
            min_samples=min_samples
        )
        
        return test_created
    
    def get_model_version_for_session(self, session_id: str, test_id: Optional[str] = None) -> str:
        """
        Get the model version to use for a session
        
        Args:
            session_id: Session identifier
            test_id: Optional test ID for A/B testing
        
        Returns:
            Model version identifier
        """
        if test_id:
            return self.ab_testing.assign_version(session_id, test_id)
        
        return self.model_pipeline.get_active_version()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "initialized": self.initialized,
            "active_version": self.model_pipeline.get_active_version(),
            "loaded_versions": self.model_pipeline.get_loaded_versions(),
            "active_tests": self.ab_testing.get_active_tests(),
            "metrics": self.feedback_collector.get_metrics()
        }
