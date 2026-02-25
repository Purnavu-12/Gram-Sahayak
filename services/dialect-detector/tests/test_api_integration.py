"""
Integration tests for Dialect Detector API endpoints
Tests the FastAPI endpoints with the multi-model detection system
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestDialectDetectorAPI:
    """Test API endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_detect_dialect_endpoint(self):
        """Test dialect detection endpoint"""
        audio_features = {
            "sample_rate": 16000,
            "channels": 1,
            "bit_depth": 16,
            "duration": 3.0
        }
        
        response = client.post("/detect", json=audio_features)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields
        assert "primary_dialect" in data
        assert "primary_language" in data
        assert "confidence" in data
        assert "alternative_dialects" in data
        assert "detection_time" in data
        assert "code_switching_detected" in data
        assert "needs_clarification" in data
        
        # Validate data types
        assert isinstance(data["primary_dialect"], str)
        assert isinstance(data["primary_language"], str)
        assert isinstance(data["confidence"], float)
        assert isinstance(data["alternative_dialects"], list)
        assert isinstance(data["detection_time"], float)
        assert isinstance(data["needs_clarification"], bool)
    
    def test_detect_dialect_timing_requirement(self):
        """Test that detection meets timing requirement (Requirement 2.1)"""
        audio_features = {
            "sample_rate": 16000,
            "channels": 1,
            "bit_depth": 16,
            "duration": 3.0
        }
        
        response = client.post("/detect", json=audio_features)
        
        assert response.status_code == 200
        data = response.json()
        
        # Detection should complete within 3 seconds (3000ms)
        assert data["detection_time"] < 3000
    
    def test_detect_dialect_low_confidence_clarification(self):
        """Test that low confidence triggers clarification (Requirement 2.4)"""
        # Use poor quality audio to potentially trigger low confidence
        audio_features = {
            "sample_rate": 8000,
            "channels": 1,
            "bit_depth": 8,
            "duration": 0.5
        }
        
        response = client.post("/detect", json=audio_features)
        
        assert response.status_code == 200
        data = response.json()
        
        # If confidence is low, should have clarification
        if data["confidence"] < 0.7:
            assert data["needs_clarification"] is True
            assert data["clarification_prompt"] is not None
    
    def test_detect_dialect_alternatives_sorted(self):
        """Test that alternative dialects are sorted by confidence"""
        audio_features = {
            "sample_rate": 16000,
            "channels": 1,
            "bit_depth": 16,
            "duration": 3.0
        }
        
        response = client.post("/detect", json=audio_features)
        
        assert response.status_code == 200
        data = response.json()
        
        alternatives = data["alternative_dialects"]
        if len(alternatives) > 1:
            # Check that alternatives are sorted in descending order
            confidences = [alt["confidence"] for alt in alternatives]
            assert confidences == sorted(confidences, reverse=True)
    
    def test_get_supported_dialects_endpoint(self):
        """Test getting supported dialects"""
        response = client.get("/dialects")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "dialects" in data
        assert isinstance(data["dialects"], list)
        assert len(data["dialects"]) > 0
        
        # Check structure of first dialect
        first_dialect = data["dialects"][0]
        assert "dialect_code" in first_dialect
        assert "language_code" in first_dialect
        assert "name" in first_dialect
        assert "region" in first_dialect
        assert "speakers" in first_dialect
        assert "is_supported" in first_dialect
    
    def test_update_confidence_endpoint(self):
        """Test feedback update endpoint"""
        feedback = {
            "correct_dialect": "hi-IN",
            "user_satisfaction": 5,
            "comments": "Perfect detection"
        }
        
        response = client.post(
            "/feedback",
            params={"session_id": "test_session_123"},
            json=feedback
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_detect_dialect_invalid_input(self):
        """Test detection with invalid input"""
        invalid_features = {
            "sample_rate": "invalid",  # Should be int
            "channels": 1
        }
        
        response = client.post("/detect", json=invalid_features)
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_multiple_detections_consistency(self):
        """Test that multiple detections with same input are consistent"""
        audio_features = {
            "sample_rate": 16000,
            "channels": 1,
            "bit_depth": 16,
            "duration": 3.0
        }
        
        # Make multiple requests
        results = []
        for _ in range(3):
            response = client.post("/detect", json=audio_features)
            assert response.status_code == 200
            results.append(response.json())
        
        # All should have valid results
        for result in results:
            assert "primary_dialect" in result
            assert result["confidence"] > 0
            assert len(result["alternative_dialects"]) > 0


class TestAPIEdgeCases:
    """Test API edge cases"""
    
    def test_very_short_audio_duration(self):
        """Test with very short audio"""
        audio_features = {
            "sample_rate": 16000,
            "channels": 1,
            "bit_depth": 16,
            "duration": 0.1
        }
        
        response = client.post("/detect", json=audio_features)
        
        assert response.status_code == 200
        data = response.json()
        assert "primary_dialect" in data
    
    def test_very_long_audio_duration(self):
        """Test with very long audio"""
        audio_features = {
            "sample_rate": 16000,
            "channels": 1,
            "bit_depth": 16,
            "duration": 120.0  # 2 minutes
        }
        
        response = client.post("/detect", json=audio_features)
        
        assert response.status_code == 200
        data = response.json()
        assert "primary_dialect" in data
        # Should still complete quickly
        assert data["detection_time"] < 3000
    
    def test_feedback_without_correct_dialect(self):
        """Test feedback with only satisfaction rating"""
        feedback = {
            "user_satisfaction": 4
        }
        
        response = client.post(
            "/feedback",
            params={"session_id": "test_session_456"},
            json=feedback
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
    
    def test_feedback_with_comments_only(self):
        """Test feedback with comments"""
        feedback = {
            "user_satisfaction": 3,
            "comments": "Good but could be better"
        }
        
        response = client.post(
            "/feedback",
            params={"session_id": "test_session_789"},
            json=feedback
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
