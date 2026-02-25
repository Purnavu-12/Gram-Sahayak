"""
Unit tests for Code-Switching Detection
Tests mixed-language speech handling, context preservation, and semantic understanding
Validates: Requirement 2.3, Task 3.3
"""

import pytest
from dialect_detector_service import (
    DialectDetectorService,
    CodeSwitchingDetector,
    EnsembleDialectDetector
)


class TestCodeSwitchingDetector:
    """Test code-switching detection component"""
    
    def test_initialization(self):
        """Test that code-switching detector initializes correctly"""
        detector = CodeSwitchingDetector()
        assert detector.switch_threshold == 0.3
        assert detector.context_window == 5
        assert len(detector.language_history) == 0
    
    def test_no_switching_on_first_segment(self):
        """Test that first segment doesn't detect switching"""
        detector = CodeSwitchingDetector()
        scores = {"hi-IN": 0.9, "bn-IN": 0.1}
        
        result = detector.detect_code_switching(scores, previous_dialect=None, segment_index=0)
        
        assert result["code_switching_detected"] is False
        assert result["primary_language"] == "hi"
        assert result["secondary_language"] is None
        assert result["context_preserved"] is True
    
    def test_detect_language_switch(self):
        """Test detection of language switching"""
        detector = CodeSwitchingDetector()
        
        # First segment in Hindi
        scores1 = {"hi-IN": 0.9, "bn-IN": 0.1}
        result1 = detector.detect_code_switching(scores1, previous_dialect=None, segment_index=0)
        
        # Second segment switches to Bengali
        scores2 = {"bn-IN": 0.85, "hi-IN": 0.15}
        result2 = detector.detect_code_switching(scores2, previous_dialect="hi-IN", segment_index=1)
        
        assert result2["code_switching_detected"] is True
        assert result2["primary_language"] == "bn"
    
    def test_no_switch_same_language(self):
        """Test that same language doesn't trigger switching"""
        detector = CodeSwitchingDetector()
        
        # First segment in Hindi
        scores1 = {"hi-IN": 0.9, "bn-IN": 0.1}
        detector.detect_code_switching(scores1, previous_dialect=None, segment_index=0)
        
        # Second segment also in Hindi
        scores2 = {"hi-IN": 0.85, "bn-IN": 0.15}
        result2 = detector.detect_code_switching(scores2, previous_dialect="hi-IN", segment_index=1)
        
        assert result2["code_switching_detected"] is False
        assert result2["primary_language"] == "hi"
    
    def test_detect_secondary_language(self):
        """Test detection of secondary language in mixed speech"""
        detector = CodeSwitchingDetector()
        
        # Mixed language scores (Hindi primary, Bengali secondary)
        scores = {"hi-IN": 0.6, "bn-IN": 0.35, "te-IN": 0.05}
        result = detector.detect_code_switching(scores, previous_dialect=None, segment_index=0)
        
        assert result["primary_language"] == "hi"
        assert result["secondary_language"] == "bn"
    
    def test_context_preservation(self):
        """Test that context is preserved across segments"""
        detector = CodeSwitchingDetector()
        
        # Process multiple segments
        for i in range(3):
            scores = {"hi-IN": 0.8, "bn-IN": 0.2}
            detector.detect_code_switching(scores, previous_dialect="hi-IN" if i > 0 else None, segment_index=i)
        
        context = detector.get_context()
        
        assert context["context_window_size"] == 3
        assert len(context["language_history"]) == 3
        assert context["dominant_language"] == "hi"
    
    def test_switch_points_tracking(self):
        """Test tracking of language switch points"""
        detector = CodeSwitchingDetector()
        
        # Hindi -> Bengali -> Hindi
        segments = [
            ({"hi-IN": 0.9, "bn-IN": 0.1}, None, 0),
            ({"bn-IN": 0.85, "hi-IN": 0.15}, "hi-IN", 1),
            ({"hi-IN": 0.9, "bn-IN": 0.1}, "bn-IN", 2)
        ]
        
        for scores, prev_dialect, idx in segments:
            detector.detect_code_switching(scores, prev_dialect, idx)
        
        switch_points = detector._get_switch_points()
        
        assert len(switch_points) == 2  # Two switches occurred
        assert 1 in switch_points  # First switch at segment 1
        assert 2 in switch_points  # Second switch at segment 2
    
    def test_language_distribution(self):
        """Test language distribution calculation"""
        detector = CodeSwitchingDetector()
        
        # 3 Hindi segments, 2 Bengali segments
        segments = [
            ({"hi-IN": 0.9}, None, 0),
            ({"hi-IN": 0.9}, "hi-IN", 1),
            ({"bn-IN": 0.9}, "hi-IN", 2),
            ({"hi-IN": 0.9}, "bn-IN", 3),
            ({"bn-IN": 0.9}, "hi-IN", 4)
        ]
        
        for scores, prev_dialect, idx in segments:
            detector.detect_code_switching(scores, prev_dialect, idx)
        
        distribution = detector._get_language_distribution()
        
        assert "hi" in distribution
        assert "bn" in distribution
        assert distribution["hi"] == 0.6  # 3 out of 5
        assert distribution["bn"] == 0.4  # 2 out of 5
    
    def test_context_window_limit(self):
        """Test that context window maintains size limit"""
        detector = CodeSwitchingDetector()
        
        # Process more segments than context window
        for i in range(10):
            scores = {"hi-IN": 0.9}
            detector.detect_code_switching(scores, "hi-IN" if i > 0 else None, i)
        
        # Should only keep last 5 (context_window size)
        assert len(detector.language_history) == 5
    
    def test_reset_context(self):
        """Test context reset functionality"""
        detector = CodeSwitchingDetector()
        
        # Add some history
        for i in range(3):
            scores = {"hi-IN": 0.9}
            detector.detect_code_switching(scores, "hi-IN" if i > 0 else None, i)
        
        assert len(detector.language_history) > 0
        
        # Reset
        detector.reset_context()
        
        assert len(detector.language_history) == 0
    
    def test_extract_language(self):
        """Test language code extraction"""
        detector = CodeSwitchingDetector()
        
        assert detector._extract_language("hi-IN") == "hi"
        assert detector._extract_language("bn-WB") == "bn"
        assert detector._extract_language("te-AP") == "te"
    
    def test_dominant_language(self):
        """Test dominant language identification"""
        detector = CodeSwitchingDetector()
        
        # Mostly Hindi with some Bengali
        segments = [
            ({"hi-IN": 0.9}, None, 0),
            ({"hi-IN": 0.9}, "hi-IN", 1),
            ({"hi-IN": 0.9}, "hi-IN", 2),
            ({"bn-IN": 0.9}, "hi-IN", 3)
        ]
        
        for scores, prev_dialect, idx in segments:
            detector.detect_code_switching(scores, prev_dialect, idx)
        
        context = detector.get_context()
        
        assert context["dominant_language"] == "hi"


class TestDialectDetectorServiceWithCodeSwitching:
    """Test dialect detector service with code-switching capabilities"""
    
    @pytest.fixture
    def service(self):
        """Create a service instance for testing"""
        return DialectDetectorService()
    
    @pytest.mark.asyncio
    async def test_detect_dialect_with_session(self, service):
        """Test dialect detection with session tracking"""
        session_id = "test_session_cs_001"
        audio_features = {
            "sample_rate": 16000,
            "duration": 3.0
        }
        
        result = await service.detect_dialect(audio_features, session_id=session_id, segment_index=0)
        
        assert "code_switching_detected" in result
        assert "secondary_language" in result
        assert "switch_points" in result
        assert "language_distribution" in result
        assert "context_preserved" in result
    
    @pytest.mark.asyncio
    async def test_detect_code_switching_across_segments(self, service):
        """Test code-switching detection across multiple segments"""
        session_id = "test_session_cs_002"
        
        # First segment in Hindi
        audio1 = {"sample_rate": 16000, "duration": 3.0}
        result1 = await service.detect_dialect(audio1, session_id=session_id, segment_index=0)
        first_language = result1["primary_language"]
        
        # Process several more segments to potentially trigger switching
        for i in range(1, 5):
            audio = {"sample_rate": 16000, "duration": 3.0}
            result = await service.detect_dialect(audio, session_id=session_id, segment_index=i)
            
            # Check that code-switching info is present
            assert "code_switching_detected" in result
            assert "context_preserved" in result
            assert result["context_preserved"] is True
    
    @pytest.mark.asyncio
    async def test_session_context_retrieval(self, service):
        """Test retrieving session context"""
        session_id = "test_session_cs_003"
        
        # Process some segments
        for i in range(3):
            audio = {"sample_rate": 16000, "duration": 3.0}
            await service.detect_dialect(audio, session_id=session_id, segment_index=i)
        
        # Get context
        context = service.get_session_context(session_id)
        
        assert context is not None
        assert "language_history" in context
        assert "dominant_language" in context
        assert "switch_frequency" in context
        assert len(context["language_history"]) == 3
    
    @pytest.mark.asyncio
    async def test_reset_session_context(self, service):
        """Test resetting session context"""
        session_id = "test_session_cs_004"
        
        # Process some segments
        for i in range(3):
            audio = {"sample_rate": 16000, "duration": 3.0}
            await service.detect_dialect(audio, session_id=session_id, segment_index=i)
        
        # Verify context exists
        context_before = service.get_session_context(session_id)
        assert len(context_before["language_history"]) > 0
        
        # Reset context
        service.reset_session_context(session_id)
        
        # Verify context is cleared
        context_after = service.get_session_context(session_id)
        assert len(context_after["language_history"]) == 0
    
    @pytest.mark.asyncio
    async def test_clear_session(self, service):
        """Test clearing entire session"""
        session_id = "test_session_cs_005"
        
        # Process some segments
        audio = {"sample_rate": 16000, "duration": 3.0}
        await service.detect_dialect(audio, session_id=session_id, segment_index=0)
        
        # Add feedback
        await service.update_confidence(session_id, {"user_satisfaction": 5})
        
        # Verify session exists
        assert session_id in service.session_contexts
        assert session_id in service.feedback_store
        
        # Clear session
        service.clear_session(session_id)
        
        # Verify session is removed
        assert session_id not in service.session_contexts
        assert session_id not in service.feedback_store
    
    @pytest.mark.asyncio
    async def test_no_session_id_still_works(self, service):
        """Test that detection works without session ID"""
        audio = {"sample_rate": 16000, "duration": 3.0}
        
        result = await service.detect_dialect(audio)
        
        # Should still return valid result
        assert "primary_dialect" in result
        assert "code_switching_detected" in result
        # Without session, code-switching should be False
        assert result["code_switching_detected"] is False
    
    @pytest.mark.asyncio
    async def test_context_preserved_flag(self, service):
        """Test that context_preserved flag is always True"""
        session_id = "test_session_cs_006"
        
        for i in range(5):
            audio = {"sample_rate": 16000, "duration": 3.0}
            result = await service.detect_dialect(audio, session_id=session_id, segment_index=i)
            
            # Context should always be preserved (Requirement 2.3)
            assert result["context_preserved"] is True
    
    @pytest.mark.asyncio
    async def test_language_distribution_in_result(self, service):
        """Test that language distribution is included in result"""
        session_id = "test_session_cs_007"
        
        # Process multiple segments
        for i in range(4):
            audio = {"sample_rate": 16000, "duration": 3.0}
            result = await service.detect_dialect(audio, session_id=session_id, segment_index=i)
        
        # Last result should have language distribution
        assert "language_distribution" in result
        assert isinstance(result["language_distribution"], dict)


class TestCodeSwitchingEdgeCases:
    """Test edge cases for code-switching detection"""
    
    @pytest.mark.asyncio
    async def test_rapid_language_switching(self):
        """Test handling of rapid language switches"""
        service = DialectDetectorService()
        session_id = "test_rapid_switch"
        
        # Simulate rapid switching between languages
        for i in range(10):
            audio = {"sample_rate": 16000, "duration": 1.0}
            result = await service.detect_dialect(audio, session_id=session_id, segment_index=i)
            
            # Should handle gracefully
            assert "code_switching_detected" in result
            assert result["context_preserved"] is True
    
    @pytest.mark.asyncio
    async def test_three_language_mixing(self):
        """Test handling of three languages in conversation"""
        detector = CodeSwitchingDetector()
        
        # Mix of Hindi, Bengali, and Telugu
        segments = [
            {"hi-IN": 0.8, "bn-IN": 0.1, "te-IN": 0.1},
            {"bn-IN": 0.7, "hi-IN": 0.2, "te-IN": 0.1},
            {"te-IN": 0.75, "hi-IN": 0.15, "bn-IN": 0.1}
        ]
        
        prev_dialect = None
        for i, scores in enumerate(segments):
            result = detector.detect_code_switching(scores, prev_dialect, i)
            prev_dialect = f"{result['primary_language']}-IN"
        
        # Should track all three languages
        distribution = detector._get_language_distribution()
        assert len(distribution) == 3
    
    @pytest.mark.asyncio
    async def test_low_confidence_with_code_switching(self):
        """Test code-switching detection with low confidence scores"""
        detector = CodeSwitchingDetector()
        
        # Low confidence scores
        scores = {"hi-IN": 0.4, "bn-IN": 0.35, "te-IN": 0.25}
        result = detector.detect_code_switching(scores, previous_dialect=None, segment_index=0)
        
        # Should still provide result
        assert result["primary_language"] is not None
        assert result["context_preserved"] is True
    
    @pytest.mark.asyncio
    async def test_empty_session_context(self):
        """Test getting context for non-existent session"""
        service = DialectDetectorService()
        
        context = service.get_session_context("non_existent_session")
        
        assert context is None
    
    @pytest.mark.asyncio
    async def test_reset_non_existent_session(self):
        """Test resetting non-existent session doesn't error"""
        service = DialectDetectorService()
        
        # Should not raise error
        service.reset_session_context("non_existent_session")
        service.clear_session("non_existent_session")
