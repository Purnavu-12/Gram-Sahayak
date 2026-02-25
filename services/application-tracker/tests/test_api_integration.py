"""
Integration tests for Application Tracker API endpoints
Tests the FastAPI application endpoints for portal integration.
"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from government_portal_integration import PortalType


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_credentials():
    """Sample credentials for testing"""
    return {
        "client_id": "test_client",
        "client_secret": "test_secret"
    }


@pytest.fixture
def sample_application():
    """Sample application data"""
    return {
        "scheme_id": "PM_KISAN_2024",
        "applicant": {
            "name": "Test User",
            "aadhaar": "1234-5678-9012",
            "phone": "+91-9876543210"
        }
    }


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Test health check returns healthy status"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "application-tracker"


class TestPortalAuthenticationEndpoint:
    """Test portal authentication endpoint"""

    def test_authenticate_portal_success(self, client, sample_credentials):
        """
        Test successful portal authentication.
        Validates: Requirement 6.1 (secure API connections)
        """
        request_data = {
            "portal_type": PortalType.MY_SCHEME.value,
            "credentials": sample_credentials
        }
        
        response = client.post("/portal/authenticate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "token" in data
        assert "expires_at" in data

    def test_authenticate_different_portals(self, client):
        """Test authentication with different portal types"""
        portals = [
            (PortalType.MY_SCHEME.value, {"client_id": "test", "client_secret": "test"}),
            (PortalType.E_SHRAM.value, {"api_key": "a" * 32}),
            (PortalType.UMANG.value, {"user_id": "test", "secret": "test"}),
            (PortalType.GENERIC.value, {"username": "test", "password": "test"})
        ]
        
        for portal_type, credentials in portals:
            request_data = {
                "portal_type": portal_type,
                "credentials": credentials
            }
            
            response = client.post("/portal/authenticate", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True

    def test_authenticate_invalid_portal(self, client, sample_credentials):
        """Test authentication with invalid portal type"""
        request_data = {
            "portal_type": "invalid_portal",
            "credentials": sample_credentials
        }
        
        response = client.post("/portal/authenticate", json=request_data)
        # Should return 422 for invalid enum value
        assert response.status_code == 422


class TestApplicationSubmissionEndpoint:
    """Test application submission endpoint"""

    def test_submit_application_success(
        self,
        client,
        sample_application,
        sample_credentials
    ):
        """
        Test successful application submission.
        Validates: Requirement 6.1 (application submission automation)
        """
        request_data = {
            "portal_type": PortalType.MY_SCHEME.value,
            "application_data": sample_application,
            "credentials": sample_credentials
        }
        
        response = client.post("/application/submit", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "submission_id" in data
        assert "confirmation_number" in data
        assert "application_id" in data
        assert data["portal"] == PortalType.MY_SCHEME.value
        assert "submitted_at" in data
        assert "expected_processing_time" in data

    def test_submit_application_returns_unique_ids(
        self,
        client,
        sample_application,
        sample_credentials
    ):
        """Test that multiple submissions return unique IDs"""
        request_data = {
            "portal_type": PortalType.MY_SCHEME.value,
            "application_data": sample_application,
            "credentials": sample_credentials
        }
        
        response1 = client.post("/application/submit", json=request_data)
        response2 = client.post("/application/submit", json=request_data)
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1["submission_id"] != data2["submission_id"]
        assert data1["confirmation_number"] != data2["confirmation_number"]

    def test_submit_to_different_portals(
        self,
        client,
        sample_application
    ):
        """Test submission to different portal types"""
        portals_and_creds = [
            (PortalType.MY_SCHEME.value, {"client_id": "test", "client_secret": "test"}),
            (PortalType.E_SHRAM.value, {"api_key": "a" * 32}),
            (PortalType.UMANG.value, {"user_id": "test", "secret": "test"})
        ]
        
        for portal_type, credentials in portals_and_creds:
            request_data = {
                "portal_type": portal_type,
                "application_data": sample_application,
                "credentials": credentials
            }
            
            response = client.post("/application/submit", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["portal"] == portal_type

    def test_submit_with_missing_fields(self, client):
        """Test submission with missing required fields"""
        # Missing application_data
        request_data = {
            "portal_type": PortalType.MY_SCHEME.value,
            "credentials": {"client_id": "test"}
        }
        
        response = client.post("/application/submit", json=request_data)
        assert response.status_code == 422  # Validation error


class TestStatusTrackingEndpoint:
    """Test application status tracking endpoint"""

    def test_get_application_status_success(self, client, sample_credentials):
        """
        Test successful status retrieval.
        Validates: Requirement 6.3 (status tracking from government systems)
        """
        request_data = {
            "portal_type": PortalType.MY_SCHEME.value,
            "application_id": "TEST-APP-12345",
            "credentials": sample_credentials
        }
        
        response = client.post("/application/status", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["application_id"] == "TEST-APP-12345"
        assert data["portal"] == PortalType.MY_SCHEME.value
        assert "status" in data
        assert "status_description" in data
        assert "last_updated" in data
        assert "progress_percentage" in data
        assert "next_steps" in data

    def test_get_status_includes_progress_info(self, client, sample_credentials):
        """Test that status response includes progress information"""
        request_data = {
            "portal_type": PortalType.MY_SCHEME.value,
            "application_id": "TEST-APP-12345",
            "credentials": sample_credentials
        }
        
        response = client.post("/application/status", json=request_data)
        data = response.json()
        
        assert isinstance(data["progress_percentage"], int)
        assert 0 <= data["progress_percentage"] <= 100
        assert isinstance(data["next_steps"], list)
        assert len(data["next_steps"]) > 0

    def test_get_status_for_different_applications(self, client, sample_credentials):
        """Test status retrieval for different applications"""
        application_ids = ["APP-001", "APP-002", "APP-003"]
        
        for app_id in application_ids:
            request_data = {
                "portal_type": PortalType.MY_SCHEME.value,
                "application_id": app_id,
                "credentials": sample_credentials
            }
            
            response = client.post("/application/status", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["application_id"] == app_id

    def test_get_status_with_missing_fields(self, client):
        """Test status request with missing required fields"""
        # Missing application_id
        request_data = {
            "portal_type": PortalType.MY_SCHEME.value,
            "credentials": {"client_id": "test"}
        }
        
        response = client.post("/application/status", json=request_data)
        assert response.status_code == 422  # Validation error


class TestMonitoringEndpoint:
    """Test application monitoring endpoint"""

    def test_monitor_application_success(self, client, sample_credentials):
        """
        Test setting up application monitoring.
        Validates: Requirement 6.3 (status tracking and monitoring system)
        """
        request_data = {
            "portal_type": PortalType.MY_SCHEME.value,
            "application_id": "TEST-APP-12345",
            "credentials": sample_credentials,
            "check_interval": 3600
        }
        
        response = client.post("/application/monitor", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["monitoring_enabled"] is True
        assert data["application_id"] == "TEST-APP-12345"
        assert data["portal"] == PortalType.MY_SCHEME.value
        assert data["check_interval_seconds"] == 3600
        assert "current_status" in data
        assert "monitoring_started_at" in data

    def test_monitor_with_default_interval(self, client, sample_credentials):
        """Test monitoring with default check interval"""
        request_data = {
            "portal_type": PortalType.MY_SCHEME.value,
            "application_id": "TEST-APP-12345",
            "credentials": sample_credentials
        }
        
        response = client.post("/application/monitor", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["check_interval_seconds"] == 3600  # Default value

    def test_monitor_with_custom_interval(self, client, sample_credentials):
        """Test monitoring with custom check interval"""
        custom_interval = 1800  # 30 minutes
        
        request_data = {
            "portal_type": PortalType.MY_SCHEME.value,
            "application_id": "TEST-APP-12345",
            "credentials": sample_credentials,
            "check_interval": custom_interval
        }
        
        response = client.post("/application/monitor", json=request_data)
        data = response.json()
        
        assert data["check_interval_seconds"] == custom_interval

    def test_monitor_includes_initial_status(self, client, sample_credentials):
        """Test that monitoring response includes initial status"""
        request_data = {
            "portal_type": PortalType.MY_SCHEME.value,
            "application_id": "TEST-APP-12345",
            "credentials": sample_credentials
        }
        
        response = client.post("/application/monitor", json=request_data)
        data = response.json()
        
        current_status = data["current_status"]
        assert current_status["success"] is True
        assert "status" in current_status
        assert "progress_percentage" in current_status


class TestInformationEndpoints:
    """Test information and metadata endpoints"""

    def test_get_supported_portals(self, client):
        """Test getting list of supported portals"""
        response = client.get("/portals/supported")
        assert response.status_code == 200
        
        data = response.json()
        assert "portals" in data
        assert len(data["portals"]) > 0
        
        # Check portal structure
        for portal in data["portals"]:
            assert "type" in portal
            assert "name" in portal
            assert "description" in portal

    def test_get_status_types(self, client):
        """Test getting list of status types"""
        response = client.get("/status/types")
        assert response.status_code == 200
        
        data = response.json()
        assert "statuses" in data
        assert len(data["statuses"]) > 0
        
        # Check status structure
        for status in data["statuses"]:
            assert "value" in status
            assert "name" in status
            assert "description" in status

    def test_supported_portals_include_major_portals(self, client):
        """Test that supported portals include major government portals"""
        response = client.get("/portals/supported")
        data = response.json()
        
        portal_types = [p["type"] for p in data["portals"]]
        
        # Check for major portals
        assert PortalType.MY_SCHEME.value in portal_types
        assert PortalType.E_SHRAM.value in portal_types
        assert PortalType.UMANG.value in portal_types

    def test_status_types_include_common_statuses(self, client):
        """Test that status types include common application statuses"""
        response = client.get("/status/types")
        data = response.json()
        
        status_values = [s["value"] for s in data["statuses"]]
        
        # Check for common statuses
        assert "submitted" in status_values
        assert "under_review" in status_values
        assert "approved" in status_values
        assert "rejected" in status_values


class TestEndToEndFlow:
    """Test complete end-to-end application flow"""

    def test_complete_application_flow(
        self,
        client,
        sample_application,
        sample_credentials
    ):
        """
        Test complete flow: authenticate -> submit -> monitor -> check status.
        Validates: Requirements 6.1, 6.3
        """
        # Step 1: Authenticate
        auth_request = {
            "portal_type": PortalType.MY_SCHEME.value,
            "credentials": sample_credentials
        }
        auth_response = client.post("/portal/authenticate", json=auth_request)
        assert auth_response.status_code == 200
        
        # Step 2: Submit application
        submit_request = {
            "portal_type": PortalType.MY_SCHEME.value,
            "application_data": sample_application,
            "credentials": sample_credentials
        }
        submit_response = client.post("/application/submit", json=submit_request)
        assert submit_response.status_code == 200
        
        submit_data = submit_response.json()
        application_id = submit_data["application_id"]
        
        # Step 3: Set up monitoring
        monitor_request = {
            "portal_type": PortalType.MY_SCHEME.value,
            "application_id": application_id,
            "credentials": sample_credentials
        }
        monitor_response = client.post("/application/monitor", json=monitor_request)
        assert monitor_response.status_code == 200
        
        # Step 4: Check status
        status_request = {
            "portal_type": PortalType.MY_SCHEME.value,
            "application_id": application_id,
            "credentials": sample_credentials
        }
        status_response = client.post("/application/status", json=status_request)
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["application_id"] == application_id
        assert "status" in status_data
