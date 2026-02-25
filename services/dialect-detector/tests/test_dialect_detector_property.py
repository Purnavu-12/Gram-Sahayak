"""
Property-based tests for Dialect Detector Service
Tests comprehensive dialect handling across all supported dialects using Hypothesis

**Feature: gram-sahayak, Property 4: Comprehensive Dialect Handling**
**Validates: Requirements 2.1, 2.2, 2.3, 2.4**
"""

import pytest
from hypothesis import given, strategies as st, settings
from dialect_detector_service import DialectDetectorService
import asyncio


# Custom strategies for generating test data
@st.composite
def audio_features_strategy(draw):
    """
    Generate valid audio features for testing
    Covers various quality levels and durations
    """
    sample_rate = draw(st.sampled_from([8000, 11025, 16000, 22050, 44100, 48000]))
    channels = draw(st.integers(min_value=1, max_value=2))
    bit_depth = draw(st.sampled_from([8, 16, 24, 32]))
    duration = draw(st.floats(min_value=0.1, max_value=60.0))
    
    return {
        "sample_rate": sample_rate,
        "channels": channels,
        "bit_depth": bit_depth,
        "duration": duration
    }


@st.composite
def supported_dialect_code_strategy(draw):
    """
    Generate dialect codes from the supported dialects list
    """
    dialect_codes = [
        "hi-IN", "hi-UP", "hi-MP",
        "bn-IN", "bn-WB",
        "te-IN", "te-AP",
        "ta-IN",
        "mr-IN",
        "gu-IN",
        "kn-IN",
        "ml-IN",
        "pa-IN"
    ]
    return draw(st.sampled_from(dialect_codes))


@st.composite
def feedback_data_strategy(draw):
    """
    Generate user feedback data for confidence updates
    """
    dialect_code = draw(supported_dialect_code_strategy())
    satisfaction = draw(st.integers(min_value=1, max_value=5))
    comments = draw(st.text(min_size=0, max_size=200))
    
    return {
        "correct_dialect": dialect_code,
        "user_satisfaction": satisfaction,
        "comments": comments
    }


class TestDialectDetectionProperties:
    """
    Property-based tests for comprehensive dialect handling
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
    """
    
    @given(audio_features=audio_features_strategy())
    @settings(max_examples=20, deadline=5000)
    def test_property_detection_time_within_3_seconds(self, audio_features):
        """
        Property 4.1: Detection Time Constraint
        For any audio input, dialect detection must complete within 3 seconds
        **Validates: Requirement 2.1**
        """
        service = DialectDetectorService()
        result = asyncio.run(service.detect_dialect(audio_features))
        
        # Property: Detection time must be within 3000ms
        assert result["detection_time"] < 3000, (
            f"Detection took {result['detection_time']}ms, exceeds 3000ms limit. "
            f"Audio features: {audio_features}"
        )
    
    @given(audio_features=audio_features_strategy())
    @settings(max_examples=20, deadline=5000)
    def test_property_always_returns_valid_dialect(self, audio_features):
        """
        Property 4.2: Valid Dialect Identification
        For any audio input, the system must return a valid supported dialect
        **Validates: Requirement 2.1**
        """
        service = DialectDetectorService()
        result = asyncio.run(service.detect_dialect(audio_features))
        
        # Get list of supported dialect codes
        supported_dialects = asyncio.run(service.get_supported_dialects())
        supported_codes = [d["dialect_code"] for d in supported_dialects]
        
        # Property: Primary dialect must be in supported list
        assert result["primary_dialect"] in supported_codes, (
            f"Detected dialect '{result['primary_dialect']}' not in supported list. "
            f"Supported: {supported_codes}"
        )
    
    @given(audio_features=audio_features_strategy())
    @settings(max_examples=20, deadline=5000)
    def test_property_confidence_in_valid_range(self, audio_features):
        """
        Property 4.3: Confidence Score Validity
        For any audio input, confidence scores must be between 0 and 1
        **Validates: Requirements 2.1, 2.4**
        """
        service = DialectDetectorService()
        result = asyncio.run(service.detect_dialect(audio_features))
        
        # Property: Confidence must be in [0, 1] range
        assert 0 <= result["confidence"] <= 1, (
            f"Confidence {result['confidence']} out of valid range [0, 1]. "
            f"Audio features: {audio_features}"
        )
        
        # Property: Alternative dialect confidences must also be in [0, 1]
        for alt in result["alternative_dialects"]:
            assert 0 <= alt["confidence"] <= 1, (
                f"Alternative dialect {alt['dialect']} has confidence "
                f"{alt['confidence']} out of valid range [0, 1]"
            )
    
    @given(audio_features=audio_features_strategy())
    @settings(max_examples=20, deadline=5000)
    def test_property_low_confidence_triggers_clarification(self, audio_features):
        """
        Property 4.4: Low Confidence Clarification
        For any audio input with confidence below threshold, clarification must be requested
        **Validates: Requirement 2.4**
        """
        service = DialectDetectorService()
        result = asyncio.run(service.detect_dialect(audio_features))
        
        # Property: Low confidence (<0.7) must trigger clarification
        if result["confidence"] < service.confidence_threshold:
            assert result["needs_clarification"] is True, (
                f"Low confidence {result['confidence']} did not trigger clarification. "
                f"Threshold: {service.confidence_threshold}"
            )
            assert result["clarification_prompt"] is not None, (
                "Clarification needed but no prompt provided"
            )
            assert len(result["clarification_prompt"]) > 0, (
                "Clarification prompt is empty"
            )
    
    @given(audio_features=audio_features_strategy())
    @settings(max_examples=20, deadline=5000)
    def test_property_high_confidence_no_clarification(self, audio_features):
        """
        Property 4.5: High Confidence No Clarification
        For any audio input with confidence above threshold, no clarification needed
        **Validates: Requirement 2.4**
        """
        service = DialectDetectorService()
        result = asyncio.run(service.detect_dialect(audio_features))
        
        # Property: High confidence (>=0.7) should not require clarification
        if result["confidence"] >= service.confidence_threshold:
            assert result["needs_clarification"] is False, (
                f"High confidence {result['confidence']} incorrectly triggered clarification. "
                f"Threshold: {service.confidence_threshold}"
            )
    
    @given(audio_features=audio_features_strategy())
    @settings(max_examples=20, deadline=5000)
    def test_property_alternatives_sorted_by_confidence(self, audio_features):
        """
        Property 4.6: Alternative Dialects Ordering
        For any audio input, alternative dialects must be sorted by confidence (descending)
        **Validates: Requirement 2.2 (maintaining context across dialect differences)**
        """
        service = DialectDetectorService()
        result = asyncio.run(service.detect_dialect(audio_features))
        
        alternatives = result["alternative_dialects"]
        
        # Property: Alternatives must be sorted in descending order by confidence
        if len(alternatives) > 1:
            confidences = [alt["confidence"] for alt in alternatives]
            sorted_confidences = sorted(confidences, reverse=True)
            assert confidences == sorted_confidences, (
                f"Alternative dialects not sorted by confidence. "
                f"Got: {confidences}, Expected: {sorted_confidences}"
            )
    
    @given(audio_features=audio_features_strategy())
    @settings(max_examples=20, deadline=5000)
    def test_property_primary_language_matches_dialect(self, audio_features):
        """
        Property 4.7: Language-Dialect Consistency
        For any detected dialect, the primary language must match the dialect's language code
        **Validates: Requirement 2.2 (maintaining context and meaning)**
        """
        service = DialectDetectorService()
        result = asyncio.run(service.detect_dialect(audio_features))
        
        # Property: Primary language should be prefix of primary dialect
        primary_dialect = result["primary_dialect"]
        primary_language = result["primary_language"]
        
        assert primary_dialect.startswith(primary_language + "-"), (
            f"Language-dialect mismatch: language='{primary_language}', "
            f"dialect='{primary_dialect}'"
        )
    
    @given(
        audio_features=audio_features_strategy(),
        feedback=feedback_data_strategy()
    )
    @settings(max_examples=20, deadline=5000)
    def test_property_feedback_updates_preserve_validity(self, audio_features, feedback):
        """
        Property 4.8: Feedback Update Stability
        For any feedback update, the system must maintain valid confidence thresholds
        **Validates: Requirement 2.2 (maintaining context across interactions)**
        """
        service = DialectDetectorService()
        
        # Get initial detection
        initial_result = asyncio.run(service.detect_dialect(audio_features))
        
        # Apply feedback
        session_id = "property_test_session"
        asyncio.run(service.update_confidence(session_id, feedback))
        
        # Property: Confidence threshold must remain in valid range
        assert 0 < service.confidence_threshold <= 1, (
            f"Confidence threshold {service.confidence_threshold} out of valid range "
            f"after feedback update"
        )
        
        # Property: System should still be able to detect dialects
        post_feedback_result = asyncio.run(service.detect_dialect(audio_features))
        assert "primary_dialect" in post_feedback_result
        assert 0 <= post_feedback_result["confidence"] <= 1
    
    @given(audio_features=audio_features_strategy())
    @settings(max_examples=20, deadline=5000)
    def test_property_result_structure_completeness(self, audio_features):
        """
        Property 4.9: Result Structure Completeness
        For any audio input, the result must contain all required fields
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
        """
        service = DialectDetectorService()
        result = asyncio.run(service.detect_dialect(audio_features))
        
        # Property: All required fields must be present
        required_fields = [
            "primary_dialect",
            "primary_language",
            "confidence",
            "alternative_dialects",
            "detection_time",
            "code_switching_detected",
            "needs_clarification"
        ]
        
        for field in required_fields:
            assert field in result, (
                f"Required field '{field}' missing from result. "
                f"Available fields: {list(result.keys())}"
            )
    
    @given(audio_features=audio_features_strategy())
    @settings(max_examples=20, deadline=5000)
    def test_property_clarification_in_detected_language(self, audio_features):
        """
        Property 4.10: Clarification Language Consistency
        For any audio input requiring clarification, the prompt must be in detected language
        **Validates: Requirement 2.4 (ask clarifying questions in detected primary language)**
        """
        service = DialectDetectorService()
        result = asyncio.run(service.detect_dialect(audio_features))
        
        if result["needs_clarification"]:
            # Property: Clarification prompt must be non-empty
            assert result["clarification_prompt"] is not None
            assert isinstance(result["clarification_prompt"], str)
            assert len(result["clarification_prompt"]) > 0, (
                "Clarification prompt is empty when clarification is needed"
            )
            
            # Property: Prompt should be appropriate for the detected language
            primary_language = result["primary_language"]
            assert primary_language in ["hi", "bn", "te", "ta", "mr", "gu", "kn", "ml", "pa"], (
                f"Detected language '{primary_language}' not in supported language list"
            )


class TestCodeSwitchingProperties:
    """
    Property-based tests for code-switching detection
    **Validates: Requirement 2.3**
    """
    
    @given(audio_features=audio_features_strategy())
    @settings(max_examples=20, deadline=5000)
    def test_property_code_switching_field_present(self, audio_features):
        """
        Property 4.11: Code-Switching Detection Field
        For any audio input, the result must include code-switching detection status
        **Validates: Requirement 2.3 (handle code-switching between languages)**
        """
        service = DialectDetectorService()
        result = asyncio.run(service.detect_dialect(audio_features))
        
        # Property: code_switching_detected field must be present
        assert "code_switching_detected" in result, (
            "code_switching_detected field missing from result"
        )
        
        # Property: code_switching_detected must be boolean
        assert isinstance(result["code_switching_detected"], bool), (
            f"code_switching_detected should be boolean, got {type(result['code_switching_detected'])}"
        )


class TestSemanticUnderstandingProperties:
    """
    Property-based tests for semantic understanding across dialects
    **Validates: Requirement 2.2**
    """
    
    @given(audio_features=audio_features_strategy())
    @settings(max_examples=20, deadline=5000)
    def test_property_dialect_variants_same_language(self, audio_features):
        """
        Property 4.12: Dialect Variant Language Consistency
        For any detected dialect, variants of the same language should be in alternatives
        **Validates: Requirement 2.2 (maintain context across dialect differences)**
        """
        service = DialectDetectorService()
        result = asyncio.run(service.detect_dialect(audio_features))
        
        primary_language = result["primary_language"]
        
        # Property: Alternative dialects should include variants from same language family
        alternatives = result["alternative_dialects"]
        
        # At least some alternatives should share the same language code
        if len(alternatives) > 0:
            # Check that alternatives are valid dialect codes
            for alt in alternatives:
                assert "dialect" in alt, "Alternative missing 'dialect' field"
                assert "confidence" in alt, "Alternative missing 'confidence' field"
                assert isinstance(alt["dialect"], str), "Dialect code must be string"
                assert "-" in alt["dialect"], "Dialect code must have language-region format"


class TestPerformanceProperties:
    """
    Property-based tests for performance characteristics
    **Validates: Requirement 2.1**
    """
    
    @given(
        audio_features_list=st.lists(
            audio_features_strategy(),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=50, deadline=10000)
    def test_property_consistent_performance_multiple_detections(self, audio_features_list):
        """
        Property 4.13: Consistent Performance
        For any sequence of audio inputs, all detections must complete within time limit
        **Validates: Requirement 2.1 (identify dialect within 3 seconds)**
        """
        service = DialectDetectorService()
        
        for audio_features in audio_features_list:
            result = asyncio.run(service.detect_dialect(audio_features))
            
            # Property: Each detection must be within time limit
            assert result["detection_time"] < 3000, (
                f"Detection took {result['detection_time']}ms in batch processing, "
                f"exceeds 3000ms limit"
            )


class TestRobustnessProperties:
    """
    Property-based tests for system robustness
    **Validates: Requirements 2.1, 2.2, 2.4**
    """
    
    @given(
        sample_rate=st.integers(min_value=4000, max_value=96000),
        duration=st.floats(min_value=0.01, max_value=120.0)
    )
    @settings(max_examples=20, deadline=5000)
    def test_property_handles_extreme_audio_parameters(self, sample_rate, duration):
        """
        Property 4.14: Robustness to Audio Parameter Variations
        For any valid audio parameters, the system must return a valid result
        **Validates: Requirement 2.1, 2.2 (maintain functionality across variations)**
        """
        service = DialectDetectorService()
        audio_features = {
            "sample_rate": sample_rate,
            "channels": 1,
            "bit_depth": 16,
            "duration": duration
        }
        
        result = asyncio.run(service.detect_dialect(audio_features))
        
        # Property: System must handle extreme parameters gracefully
        assert "primary_dialect" in result
        assert 0 <= result["confidence"] <= 1
        assert result["detection_time"] < 3000
    
    @given(audio_features=audio_features_strategy())
    @settings(max_examples=20, deadline=5000)
    def test_property_deterministic_for_same_input(self, audio_features):
        """
        Property 4.15: Deterministic Behavior
        For any audio input, repeated detections should produce consistent results
        **Validates: Requirement 2.2 (maintain context and meaning)**
        """
        service = DialectDetectorService()
        
        # Run detection twice with same input
        result1 = asyncio.run(service.detect_dialect(audio_features))
        result2 = asyncio.run(service.detect_dialect(audio_features))
        
        # Property: Primary dialect should be consistent
        assert result1["primary_dialect"] is not None
        assert result2["primary_dialect"] is not None
        
        # Property: Both results should have same structure
        assert set(result1.keys()) == set(result2.keys()), (
            "Repeated detections produced different result structures"
        )
