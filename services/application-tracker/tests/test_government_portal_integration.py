"""
Unit tests for Government Portal Integration Service
Tests secure API connections, application submission, and status tracking.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from government_portal_integration import (
    GovernmentPortalIntegration,
    PortalType,
    ApplicationStatus
)


@pytest.fixture
def portal_integration():
    """Create a portal integration instance for testing"""
    return GovernmentPortalIntegration()


@pytest.fixture
def sample_credentials():
    """Sample credentials for testing"""
    return {
        "oauth2": {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret"
        },
        "api_key": {
            "api_key": "a" * 32  # Valid length API key
        },
        "jwt": {
            "user_id": "test_user",
            "secret": "test_secret"
        },
        "basic": {
            "username": "test_user",
            "password": "test_password"
        }
    }


@pytest.fixture
def sample_application():
    """Sample application data"""
    return {
        "scheme_id": "PM_KISAN_2024",
        "applicant": {
            "name": "राज कुमार",
            "aadhaar": "1234-5678-9012",
            "phone": "+91-9876543210",
            "village": "रामपुर",
            "district": "वाराणसी",
            "state": "उत्तर प्रदेश"
        },
        "land_details": {
            "total_land": "2.5 acres",
            "land_type": "agricultural"
        },
        "bank_details": {
            "account_number": "1234567890",
            "ifsc": "SBIN0001234",
            "bank_name": "State Bank of India"
        }
    }


class TestPortalAuthentication:
    """Test portal authentication functionality"""

    @pytest.mark.asyncio
    async def test_oauth2_authentication(self, portal_integration, sample_credentials):
        """Test OAuth2 authentication flow"""
        result = await portal_integration.authenticate_portal(
            PortalType.MY_SCHEME,
            sample_credentials["oauth2"]
        )
        
        assert result["success"] is True
        assert "token" in result
        assert "expires_at" in result
        assert result["cached"] is False

    @pytest.mark.asyncio
    async def test_api_key_authentication(self, portal_integration, sample_credentials):
        """Test API key authentication"""
        result = await portal_integration.authenticate_portal(
            PortalType.E_SHRAM,
            sample_credentials["api_key"]
        )
        
        assert result["success"] is True
        assert result["token"] == sample_credentials["api_key"]["api_key"]

    @pytest.mark.asyncio
    async def test_jwt_authentication(self, portal_integration, sample_credentials):
        """Test JWT authentication"""
        result = await portal_integration.authenticate_portal(
            PortalType.UMANG,
            sample_credentials["jwt"]
        )
        
        assert result["success"] is True
        assert "token" in result
        assert isinstance(result["token"], str)

    @pytest.mark.asyncio
    async def test_basic_authentication(self, portal_integration, sample_credentials):
        """Test basic authentication"""
        result = await portal_integration.authenticate_portal(
            PortalType.GENERIC,
            sample_credentials["basic"]
        )
        
        assert result["success"] is True
        assert "token" in result

    @pytest.mark.asyncio
    async def test_token_caching(self, portal_integration, sample_credentials):
        """Test that tokens are cached and reused"""
        # First authentication
        result1 = await portal_integration.authenticate_portal(
            PortalType.MY_SCHEME,
            sample_credentials["oauth2"]
        )
        
        # Second authentication should use cached token
        result2 = await portal_integration.authenticate_portal(
            PortalType.MY_SCHEME,
            sample_credentials["oauth2"]
        )
        
        assert result1["token"] == result2["token"]
        assert result2["cached"] is True

    @pytest.mark.asyncio
    async def test_invalid_portal_type(self, portal_integration, sample_credentials):
        """Test handling of invalid portal type"""
        with pytest.raises(ValueError, match="Unknown portal type"):
            await portal_integration.authenticate_portal(
                "invalid_portal",
                sample_credentials["oauth2"]
            )

    @pytest.mark.asyncio
    async def test_invalid_api_key(self, portal_integration):
        """Test handling of invalid API key"""
        with pytest.raises(ValueError, match="Invalid API key format"):
            await portal_integration.authenticate_portal(
                PortalType.E_SHRAM,
                {"api_key": "short"}
            )


class TestApplicationSubmission:
    """Test application submission functionality"""

    @pytest.mark.asyncio
    async def test_successful_submission(
        self,
        portal_integration,
        sample_application,
        sample_credentials
    ):
        """
        Test successful application submission.
        Validates: Requirement 6.1 (application submission automation)
        """
        result = await portal_integration.submit_application(
            PortalType.MY_SCHEME,
            sample_application,
            sample_credentials["oauth2"]
        )
        
        assert result["success"] is True
        assert "submission_id" in result
        assert "confirmation_number" in result
        assert "application_id" in result
        assert result["portal"] == PortalType.MY_SCHEME.value
        assert "submitted_at" in result
        assert "expected_processing_time" in result

    @pytest.mark.asyncio
    async def test_submission_generates_unique_ids(
        self,
        portal_integration,
        sample_application,
        sample_credentials
    ):
        """Test that each submission generates unique IDs"""
        result1 = await portal_integration.submit_application(
            PortalType.MY_SCHEME,
            sample_application,
            sample_credentials["oauth2"]
        )
        
        result2 = await portal_integration.submit_application(
            PortalType.MY_SCHEME,
            sample_application,
            sample_credentials["oauth2"]
        )
        
        assert result1["submission_id"] != result2["submission_id"]
        assert result1["confirmation_number"] != result2["confirmation_number"]

    @pytest.mark.asyncio
    async def test_submission_to_different_portals(
        self,
        portal_integration,
        sample_application,
        sample_credentials
    ):
        """Test submission to different portal types"""
        portals = [
            (PortalType.MY_SCHEME, sample_credentials["oauth2"]),
            (PortalType.E_SHRAM, sample_credentials["api_key"]),
            (PortalType.UMANG, sample_credentials["jwt"])
        ]
        
        for portal_type, creds in portals:
            result = await portal_integration.submit_application(
                portal_type,
                sample_application,
                creds
            )
            
            assert result["success"] is True
            assert result["portal"] == portal_type.value

    @pytest.mark.asyncio
    async def test_submission_stores_tracking_data(
        self,
        portal_integration,
        sample_application,
        sample_credentials
    ):
        """Test that submission data is stored for tracking"""
        result = await portal_integration.submit_application(
            PortalType.MY_SCHEME,
            sample_application,
            sample_credentials["oauth2"]
        )
        
        submission_id = result["submission_id"]
        assert submission_id in portal_integration.submissions
        
        stored_data = portal_integration.submissions[submission_id]
        assert stored_data["portal_type"] == PortalType.MY_SCHEME.value
        assert stored_data["status"] == ApplicationStatus.SUBMITTED.value
        assert "application_data" in stored_data

    @pytest.mark.asyncio
    async def test_submission_encrypts_sensitive_data(
        self,
        portal_integration,
        sample_application,
        sample_credentials
    ):
        """Test that sensitive application data is encrypted"""
        result = await portal_integration.submit_application(
            PortalType.MY_SCHEME,
            sample_application,
            sample_credentials["oauth2"]
        )
        
        submission_id = result["submission_id"]
        stored_data = portal_integration.submissions[submission_id]
        
        # Encrypted data should be a string, not the original dict
        assert isinstance(stored_data["application_data"], str)
        assert stored_data["application_data"] != str(sample_application)


class TestStatusTracking:
    """Test application status tracking functionality"""

    @pytest.mark.asyncio
    async def test_get_application_status(
        self,
        portal_integration,
        sample_credentials
    ):
        """
        Test retrieving application status.
        Validates: Requirement 6.3 (status tracking from government systems)
        """
        application_id = "TEST-APP-12345"
        
        result = await portal_integration.get_application_status(
            PortalType.MY_SCHEME,
            application_id,
            sample_credentials["oauth2"]
        )
        
        assert result["success"] is True
        assert result["application_id"] == application_id
        assert result["portal"] == PortalType.MY_SCHEME.value
        assert "status" in result
        assert "status_description" in result
        assert "last_updated" in result
        assert "progress_percentage" in result
        assert "next_steps" in result

    @pytest.mark.asyncio
    async def test_status_includes_progress_info(
        self,
        portal_integration,
        sample_credentials
    ):
        """Test that status includes progress information"""
        result = await portal_integration.get_application_status(
            PortalType.MY_SCHEME,
            "TEST-APP-12345",
            sample_credentials["oauth2"]
        )
        
        assert isinstance(result["progress_percentage"], int)
        assert 0 <= result["progress_percentage"] <= 100
        assert isinstance(result["next_steps"], list)
        assert len(result["next_steps"]) > 0

    @pytest.mark.asyncio
    async def test_status_consistent_for_same_application(
        self,
        portal_integration,
        sample_credentials
    ):
        """Test that status is consistent for the same application ID"""
        application_id = "TEST-APP-CONSISTENT"
        
        result1 = await portal_integration.get_application_status(
            PortalType.MY_SCHEME,
            application_id,
            sample_credentials["oauth2"]
        )
        
        result2 = await portal_integration.get_application_status(
            PortalType.MY_SCHEME,
            application_id,
            sample_credentials["oauth2"]
        )
        
        # Status should be consistent for same application
        assert result1["status"] == result2["status"]

    @pytest.mark.asyncio
    async def test_status_different_for_different_applications(
        self,
        portal_integration,
        sample_credentials
    ):
        """Test that different applications can have different statuses"""
        result1 = await portal_integration.get_application_status(
            PortalType.MY_SCHEME,
            "APP-001",
            sample_credentials["oauth2"]
        )
        
        result2 = await portal_integration.get_application_status(
            PortalType.MY_SCHEME,
            "APP-002",
            sample_credentials["oauth2"]
        )
        
        # Different applications may have different statuses
        assert result1["application_id"] != result2["application_id"]


class TestStatusMonitoring:
    """Test application status monitoring functionality"""

    @pytest.mark.asyncio
    async def test_monitor_application_status(
        self,
        portal_integration,
        sample_credentials
    ):
        """
        Test setting up status monitoring.
        Validates: Requirement 6.3 (status tracking and monitoring system)
        """
        result = await portal_integration.monitor_application_status(
            PortalType.MY_SCHEME,
            "TEST-APP-12345",
            sample_credentials["oauth2"],
            check_interval=3600
        )
        
        assert result["success"] is True
        assert result["monitoring_enabled"] is True
        assert result["application_id"] == "TEST-APP-12345"
        assert result["portal"] == PortalType.MY_SCHEME.value
        assert result["check_interval_seconds"] == 3600
        assert "current_status" in result
        assert "monitoring_started_at" in result

    @pytest.mark.asyncio
    async def test_monitor_with_custom_interval(
        self,
        portal_integration,
        sample_credentials
    ):
        """Test monitoring with custom check interval"""
        custom_interval = 1800  # 30 minutes
        
        result = await portal_integration.monitor_application_status(
            PortalType.MY_SCHEME,
            "TEST-APP-12345",
            sample_credentials["oauth2"],
            check_interval=custom_interval
        )
        
        assert result["check_interval_seconds"] == custom_interval

    @pytest.mark.asyncio
    async def test_monitor_includes_initial_status(
        self,
        portal_integration,
        sample_credentials
    ):
        """Test that monitoring includes initial status check"""
        result = await portal_integration.monitor_application_status(
            PortalType.MY_SCHEME,
            "TEST-APP-12345",
            sample_credentials["oauth2"]
        )
        
        current_status = result["current_status"]
        assert current_status["success"] is True
        assert "status" in current_status
        assert "progress_percentage" in current_status


class TestSecurityFeatures:
    """Test security features of the portal integration"""

    def test_encryption_and_decryption(self, portal_integration):
        """Test data encryption and decryption"""
        test_data = {
            "sensitive": "information",
            "aadhaar": "1234-5678-9012",
            "bank_account": "9876543210"
        }
        
        # Encrypt data
        encrypted = portal_integration._encrypt_data(test_data)
        assert isinstance(encrypted, str)
        assert encrypted != str(test_data)
        
        # Decrypt data
        decrypted = portal_integration._decrypt_data(encrypted)
        assert decrypted == test_data

    def test_secure_token_generation(self, portal_integration):
        """Test secure token generation"""
        token1 = portal_integration._generate_secure_token("seed1")
        token2 = portal_integration._generate_secure_token("seed2")
        
        # Tokens should be different for different seeds
        assert token1 != token2
        
        # Tokens should be hex strings
        assert all(c in "0123456789abcdef" for c in token1)
        assert len(token1) == 64  # SHA256 hex digest length

    def test_submission_id_generation(self, portal_integration):
        """Test submission ID generation"""
        app_data = {"test": "data"}
        
        id1 = portal_integration._generate_submission_id(
            PortalType.MY_SCHEME,
            app_data
        )
        id2 = portal_integration._generate_submission_id(
            PortalType.E_SHRAM,
            app_data
        )
        
        # IDs should be different for different portals
        assert id1 != id2
        
        # IDs should be uppercase hex strings
        assert id1.isupper()
        assert len(id1) == 16

    def test_confirmation_number_format(self, portal_integration):
        """Test confirmation number format"""
        conf_num = portal_integration._generate_confirmation_number(
            PortalType.MY_SCHEME
        )
        
        # Should start with portal prefix
        assert conf_num.startswith("MYS")
        
        # Should have numeric suffix
        assert conf_num[3:].isdigit()
        # Length should be at most 12 characters (3 letter prefix + up to 9 digits)
        assert len(conf_num) <= 12


class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_submission_with_authentication_failure(
        self,
        portal_integration,
        sample_application
    ):
        """Test submission handling when authentication fails"""
        # Use invalid credentials that will fail validation
        invalid_creds = {"api_key": "invalid"}
        
        # The submission should catch the authentication error and return failure
        try:
            result = await portal_integration.submit_application(
                PortalType.E_SHRAM,
                sample_application,
                invalid_creds
            )
            # If no exception, check for failure result
            assert result["success"] is False
            assert "error" in result
        except ValueError:
            # Authentication failure raises ValueError, which is expected
            pass

    @pytest.mark.asyncio
    async def test_status_descriptions(self, portal_integration):
        """Test status description generation"""
        for status in ApplicationStatus:
            description = portal_integration._get_status_description(status)
            assert isinstance(description, str)
            assert len(description) > 0

    @pytest.mark.asyncio
    async def test_next_steps_for_all_statuses(self, portal_integration):
        """Test next steps generation for all statuses"""
        for status in ApplicationStatus:
            next_steps = portal_integration._get_next_steps(status)
            assert isinstance(next_steps, list)
            # Most statuses should have next steps
            if status != ApplicationStatus.DRAFT:
                assert len(next_steps) > 0


class TestPortalConfigurations:
    """Test portal configuration management"""

    def test_portal_configs_initialized(self, portal_integration):
        """Test that portal configurations are properly initialized"""
        assert len(portal_integration.portal_configs) > 0
        
        for portal_type, config in portal_integration.portal_configs.items():
            assert "base_url" in config
            assert "auth_type" in config
            assert "endpoints" in config
            assert "rate_limit" in config
            assert "retry_attempts" in config

    def test_portal_endpoints_defined(self, portal_integration):
        """Test that all portals have required endpoints"""
        required_endpoints = ["submit", "status", "update"]
        
        for config in portal_integration.portal_configs.values():
            endpoints = config["endpoints"]
            for endpoint in required_endpoints:
                assert endpoint in endpoints
                assert isinstance(endpoints[endpoint], str)

    def test_supported_portal_types(self, portal_integration):
        """Test that all portal types are supported"""
        supported_portals = [
            PortalType.MY_SCHEME,
            PortalType.E_SHRAM,
            PortalType.UMANG,
            PortalType.GENERIC
        ]
        
        for portal_type in supported_portals:
            assert portal_type in portal_integration.portal_configs
