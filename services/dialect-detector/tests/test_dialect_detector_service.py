import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dialect_detector_service import DialectDetectorService


@pytest.fixture
def detector():
    return DialectDetectorService()


@pytest.mark.asyncio
async def test_detect_dialect_returns_result(detector):
    """Test that dialect detection returns a valid result"""
    audio_features = {
        "sample_rate": 16000,
        "channels": 1,
        "bit_depth": 16,
        "duration": 2.5
    }

    result = await detector.detect_dialect(audio_features)

    assert result is not None
    assert "primary_dialect" in result
    assert "primary_language" in result
    assert "confidence" in result
    assert 0 <= result["confidence"] <= 1
    assert result["detection_time"] < 3000  # Must be under 3 seconds (Requirement 2.1)


@pytest.mark.asyncio
async def test_detect_dialect_includes_alternatives(detector):
    """Test that dialect detection includes alternative dialects"""
    audio_features = {
        "sample_rate": 16000,
        "channels": 1,
        "bit_depth": 16,
        "duration": 2.5
    }

    result = await detector.detect_dialect(audio_features)

    assert "alternative_dialects" in result
    assert isinstance(result["alternative_dialects"], list)


@pytest.mark.asyncio
async def test_get_supported_dialects(detector):
    """Test that supported dialects list is returned"""
    dialects = await detector.get_supported_dialects()

    assert isinstance(dialects, list)
    assert len(dialects) > 0
    assert all("dialect_code" in d for d in dialects)
    assert all("language_code" in d for d in dialects)


@pytest.mark.asyncio
async def test_update_confidence_stores_feedback(detector):
    """Test that feedback is stored correctly"""
    session_id = "test_session_123"
    feedback = {
        "correct_dialect": "hi-IN",
        "user_satisfaction": 5,
        "comments": "Accurate detection"
    }

    await detector.update_confidence(session_id, feedback)

    assert session_id in detector.feedback_store
    assert len(detector.feedback_store[session_id]) == 1
