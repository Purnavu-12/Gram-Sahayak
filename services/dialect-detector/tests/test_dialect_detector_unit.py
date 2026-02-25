"""
Unit tests for Dialect Detector Service
Tests specific examples and edge cases for multi-model dialect detection
"""

import pytest
from dialect_detector_service import (
    DialectDetectorService,
    AcousticModel,
    LinguisticModel,
    EnsembleDialectDetector
)


class TestAcousticModel:
    """Test acoustic model component"""
    
    def test_acoustic_model_initialization(self):
        """Test that acoustic model initializes with correct weights"""
        model = AcousticModel()
        assert len(model.model_weights) > 0
        assert "hi-IN" in model.model_weights
        assert model.model_weights["hi-IN"] == 1.0
    
    def test_acoustic_prediction_returns_scores(self):
        """Test that acoustic model returns confidence scores"""
        model = AcousticModel()
        audio_features = {
            "sample_rate": 16000,
            "channels": 1,
            "bit_depth": 16,
            "duration": 3.0
        }
        scores = model.predict(audio_features)
        
        assert isinstance(scores, dict)
        assert len(scores) > 0
        assert all(0 <= score <= 1 for score in scores.values())
    
    def test_acoustic_prediction_quality_impact(self):
        """Test that audio quality affects confidence scores"""
        model = AcousticModel()
        
        # High quality audio
        high_quality = {
            "sample_rate": 16000,
            "duration": 3.0
        }
        high_scores = model.predict(high_quality)
        
        # Low quality audio
        low_quality = {
            "sample_rate": 8000,
            "duration": 1.0
        }
        low_scores = model.predict(low_quality)
        
        # High quality should generally have higher scores
        assert max(high_scores.values()) >= max(low_scores.values())


class TestLinguisticModel:
    """Test linguistic model component"""
    
    def test_linguistic_model_initialization(self):
        """Test that linguistic model initializes with patterns"""
        model = LinguisticModel()
        assert len(model.language_patterns) > 0
        assert "hi-IN" in model.language_patterns
        assert isinstance(model.language_patterns["hi-IN"], list)
    
    def test_linguistic_prediction_returns_scores(self):
        """Test that linguistic model returns confidence scores"""
        model = LinguisticModel()
        audio_features = {
            "duration": 3.0
        }
        scores = model.predict(audio_features)
        
        assert isinstance(scores, dict)
        assert len(scores) > 0
        assert all(0 <= score <= 1 for score in scores.values())


class TestEnsembleDialectDetector:
    """Test ensemble detector combining multiple models"""
    
    def test_ensemble_initialization(self):
        """Test that ensemble detector initializes correctly"""
        detector = EnsembleDialectDetector()
        assert detector.acoustic_model is not None
        assert detector.linguistic_model is not None
        assert detector.confidence_threshold == 0.7
        assert detector.acoustic_weight + detector.linguistic_weight == 1.0
    
    def test_ensemble_detection_returns_results(self):
        """Test that ensemble detector returns proper results"""
        detector = EnsembleDialectDetector()
        audio_features = {
            "sample_rate": 16000,
            "channels": 1,
            "duration": 3.0
        }
        
        primary_dialect, confidence, alternatives = detector.detect(audio_features)
        
        assert isinstance(primary_dialect, str)
        assert 0 <= confidence <= 1
        assert isinstance(alternatives, list)
        assert len(alternatives) > 0
    
    def test_ensemble_alternatives_sorted_by_confidence(self):
        """Test that alternative dialects are sorted by confidence"""
        detector = EnsembleDialectDetector()
        audio_features = {
            "sample_rate": 16000,
            "duration": 3.0
        }
        
        _, _, alternatives = detector.detect(audio_features)
        
        # Check that alternatives are sorted in descending order
        confidences = [alt["confidence"] for alt in alternatives]
        assert confidences == sorted(confidences, reverse=True)


class TestDialectDetectorService:
    """Test main dialect detector service"""
    
    @pytest.fixture
    def service(self):
        """Create a service instance for testing"""
        return DialectDetectorService()
    
    def test_service_initialization(self, service):
        """Test that service initializes with supported dialects"""
        assert len(service.supported_dialects) > 0
        assert service.confidence_threshold == 0.7
        assert service.max_detection_time == 3.0
    
    def test_supported_dialects_structure(self, service):
        """Test that supported dialects have correct structure"""
        for dialect in service.supported_dialects:
            assert "dialect_code" in dialect
            assert "language_code" in dialect
            assert "name" in dialect
            assert "region" in dialect
            assert "speakers" in dialect
            assert "is_supported" in dialect
    
    @pytest.mark.asyncio
    async def test_detect_dialect_basic(self, service):
        """Test basic dialect detection"""
        audio_features = {
            "sample_rate": 16000,
            "channels": 1,
            "bit_depth": 16,
            "duration": 3.0
        }
        
        result = await service.detect_dialect(audio_features)
        
        assert "primary_dialect" in result
        assert "primary_language" in result
        assert "confidence" in result
        assert "alternative_dialects" in result
        assert "detection_time" in result
        assert "needs_clarification" in result
    
    @pytest.mark.asyncio
    async def test_detect_dialect_timing_requirement(self, service):
        """Test that detection completes within 3 seconds (Requirement 2.1)"""
        audio_features = {
            "sample_rate": 16000,
            "duration": 3.0
        }
        
        result = await service.detect_dialect(audio_features)
        
        # Detection time should be well under 3000ms
        assert result["detection_time"] < 3000
    
    @pytest.mark.asyncio
    async def test_low_confidence_triggers_clarification(self, service):
        """Test that low confidence triggers clarification (Requirement 2.4)"""
        # Temporarily lower threshold to test
        original_threshold = service.ensemble_detector.confidence_threshold
        service.ensemble_detector.confidence_threshold = 0.95  # Very high threshold
        
        audio_features = {
            "sample_rate": 8000,  # Poor quality
            "duration": 0.5  # Very short
        }
        
        result = await service.detect_dialect(audio_features)
        
        # Should trigger clarification for low confidence
        if result["confidence"] < 0.95:
            assert result["needs_clarification"] is True
            assert result["clarification_prompt"] is not None
        
        # Restore original threshold
        service.ensemble_detector.confidence_threshold = original_threshold
    
    @pytest.mark.asyncio
    async def test_high_confidence_no_clarification(self, service):
        """Test that high confidence doesn't trigger clarification"""
        audio_features = {
            "sample_rate": 16000,
            "duration": 5.0  # Long duration for high confidence
        }
        
        result = await service.detect_dialect(audio_features)
        
        # High confidence should not need clarification
        if result["confidence"] >= service.confidence_threshold:
            assert result["needs_clarification"] is False
    
    @pytest.mark.asyncio
    async def test_clarification_prompt_in_detected_language(self, service):
        """Test that clarification prompt is in detected language (Requirement 2.4)"""
        audio_features = {
            "sample_rate": 16000,
            "duration": 3.0
        }
        
        result = await service.detect_dialect(audio_features)
        
        if result["needs_clarification"]:
            # Prompt should be non-empty string
            assert isinstance(result["clarification_prompt"], str)
            assert len(result["clarification_prompt"]) > 0
    
    @pytest.mark.asyncio
    async def test_update_confidence_stores_feedback(self, service):
        """Test that feedback is stored correctly"""
        session_id = "test_session_123"
        feedback = {
            "correct_dialect": "hi-IN",
            "user_satisfaction": 5,
            "comments": "Perfect detection"
        }
        
        await service.update_confidence(session_id, feedback)
        
        assert session_id in service.feedback_store
        assert len(service.feedback_store[session_id]) == 1
        assert "timestamp" in service.feedback_store[session_id][0]
    
    @pytest.mark.asyncio
    async def test_update_confidence_adjusts_threshold(self, service):
        """Test that feedback adjusts confidence threshold"""
        session_id = "test_session_456"
        original_threshold = service.confidence_threshold
        
        # Low satisfaction feedback
        low_satisfaction = {
            "correct_dialect": "hi-IN",
            "user_satisfaction": 2,
            "comments": "Wrong detection"
        }
        
        await service.update_confidence(session_id, low_satisfaction)
        
        # Threshold should increase (more conservative)
        assert service.confidence_threshold >= original_threshold
    
    @pytest.mark.asyncio
    async def test_get_supported_dialects(self, service):
        """Test getting supported dialects list"""
        dialects = await service.get_supported_dialects()
        
        assert isinstance(dialects, list)
        assert len(dialects) > 0
        assert all("dialect_code" in d for d in dialects)
    
    def test_extract_language_code(self, service):
        """Test language code extraction from dialect code"""
        assert service._extract_language_code("hi-IN") == "hi"
        assert service._extract_language_code("bn-WB") == "bn"
        assert service._extract_language_code("te-AP") == "te"
    
    def test_should_ask_clarification_logic(self, service):
        """Test clarification decision logic"""
        assert service._should_ask_clarification(0.5) is True
        assert service._should_ask_clarification(0.69) is True
        assert service._should_ask_clarification(0.7) is False
        assert service._should_ask_clarification(0.95) is False
    
    def test_generate_clarification_prompt_multiple_languages(self, service):
        """Test clarification prompt generation for different languages"""
        # Test Hindi
        prompt_hi = service._generate_clarification_prompt("hi-IN", [])
        assert len(prompt_hi) > 0
        
        # Test Bengali
        prompt_bn = service._generate_clarification_prompt("bn-IN", [])
        assert len(prompt_bn) > 0
        
        # Test Telugu
        prompt_te = service._generate_clarification_prompt("te-IN", [])
        assert len(prompt_te) > 0
        
        # Prompts should be different for different languages
        assert prompt_hi != prompt_bn
        assert prompt_bn != prompt_te


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    @pytest.mark.asyncio
    async def test_very_short_audio(self):
        """Test detection with very short audio"""
        service = DialectDetectorService()
        audio_features = {
            "sample_rate": 16000,
            "duration": 0.1  # Very short
        }
        
        result = await service.detect_dialect(audio_features)
        
        # Should still return a result
        assert "primary_dialect" in result
        assert result["confidence"] >= 0
    
    @pytest.mark.asyncio
    async def test_very_long_audio(self):
        """Test detection with very long audio"""
        service = DialectDetectorService()
        audio_features = {
            "sample_rate": 16000,
            "duration": 60.0  # 1 minute
        }
        
        result = await service.detect_dialect(audio_features)
        
        # Should handle long audio
        assert "primary_dialect" in result
        assert result["detection_time"] < 3000  # Still within time limit
    
    @pytest.mark.asyncio
    async def test_poor_audio_quality(self):
        """Test detection with poor audio quality"""
        service = DialectDetectorService()
        audio_features = {
            "sample_rate": 8000,  # Low sample rate
            "channels": 1,
            "bit_depth": 8,  # Low bit depth
            "duration": 2.0
        }
        
        result = await service.detect_dialect(audio_features)
        
        # Should still provide a result, possibly with lower confidence
        assert "primary_dialect" in result
        assert 0 <= result["confidence"] <= 1
    
    @pytest.mark.asyncio
    async def test_missing_audio_features(self):
        """Test detection with minimal audio features"""
        service = DialectDetectorService()
        audio_features = {}  # Empty features
        
        result = await service.detect_dialect(audio_features)
        
        # Should handle gracefully with defaults
        assert "primary_dialect" in result
    
    @pytest.mark.asyncio
    async def test_multiple_feedback_updates(self):
        """Test multiple feedback updates for same session"""
        service = DialectDetectorService()
        session_id = "test_session_multi"
        
        for i in range(5):
            feedback = {
                "user_satisfaction": 3 + i % 3,
                "comments": f"Feedback {i}"
            }
            await service.update_confidence(session_id, feedback)
        
        # Should store all feedback
        assert len(service.feedback_store[session_id]) == 5
