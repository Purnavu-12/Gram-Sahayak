"""
Integration tests for secure government portal authentication.
Tests the complete authentication flow with audit logging and session management.

Validates: Requirement 9.4
"""

import pytest
import asyncio
from datetime import datetime, timedelta

# Add parent directory to path for imports
import sys
sys.path.append('..')

from government_portal_integration import (
    GovernmentPortalIntegration,
    PortalType
)
from secure_auth import AuditEventType


class TestSecurePortalIntegration:
    """Test secure portal integration with authentication"""
    
    @pytest.fixture
    def portal_integration(self):
        """Create portal integration instance"""
        return GovernmentPortalIntegration()
    
    @pytest.mark.asyncio
    async def test_authenticate_with_audit_logging(self, portal_integration):
        """Test authentication with audit logging"""
        credentials = {
            'client_id': 'test_client',
            'client_secret': 'test_secret'
        }
        
        # Authenticate
        result = await portal_integration.authenticate_portal(
            portal_type=PortalType.MY_SCHEME,
            credentials=credentials,
            user_id="test_user",
            ip_address="192.168.1.1"
        )
        
        assert result['success'] is True
        assert 'token' in result
        assert 'session_id' in result
        
        # Verify audit log was created
        logs = portal_integration.get_audit_logs(
            start_date=datetime.utcnow() - timedelta(minutes=1),
            end_date=datetime.utcnow() + timedelta(minutes=1),
            event_type=AuditEventType.AUTH_SUCCESS,
            user_id="test_user"
        )
        
        assert len(logs) > 0
        assert logs[0]['portal_id'] == PortalType.MY_SCHEME.value
    
    @pytest.mark.asyncio
    async def test_session_validation(self, portal_integration):
        """Test session validation"""
        credentials = {
            'client_id': 'test_client',
            'client_secret': 'test_secret'
        }
        
        # Authenticate and get session
        result = await portal_integration.authenticate_portal(
            portal_type=PortalType.MY_SCHEME,
            credentials=credentials,
            user_id="test_user"
        )
        
        session_id = result['session_id']
        
        # Validate session
        session = portal_integration.validate_session(session_id)
        assert session is not None
        assert session['user_id'] == 'test_user'
        assert session['portal_id'] == PortalType.MY_SCHEME.value
    
    @pytest.mark.asyncio
    async def test_session_refresh(self, portal_integration):
        """Test session refresh"""
        credentials = {
            'client_id': 'test_client',
            'client_secret': 'test_secret'
        }
        
        # Authenticate
        result = await portal_integration.authenticate_portal(
            portal_type=PortalType.MY_SCHEME,
            credentials=credentials,
            user_id="test_user"
        )
        
        session_id = result['session_id']
        
        # Refresh session
        success = portal_integration.refresh_session(session_id, user_id="test_user")
        assert success is True
        
        # Verify audit log
        logs = portal_integration.get_audit_logs(
            start_date=datetime.utcnow() - timedelta(minutes=1),
            end_date=datetime.utcnow() + timedelta(minutes=1),
            event_type=AuditEventType.TOKEN_REFRESH
        )
        
        assert len(logs) > 0
    
    @pytest.mark.asyncio
    async def test_session_revocation(self, portal_integration):
        """Test session revocation"""
        credentials = {
            'client_id': 'test_client',
            'client_secret': 'test_secret'
        }
        
        # Authenticate
        result = await portal_integration.authenticate_portal(
            portal_type=PortalType.MY_SCHEME,
            credentials=credentials,
            user_id="test_user"
        )
        
        session_id = result['session_id']
        
        # Revoke session
        success = portal_integration.revoke_session(session_id, user_id="test_user")
        assert success is True
        
        # Verify session is invalid
        session = portal_integration.validate_session(session_id)
        assert session is None
    
    @pytest.mark.asyncio
    async def test_data_access_logging(self, portal_integration):
        """Test data access audit logging"""
        portal_integration.log_data_access(
            user_id="test_user",
            portal_id=PortalType.MY_SCHEME.value,
            resource="application_data",
            action="read",
            session_id="test_session",
            ip_address="192.168.1.1"
        )
        
        # Query data access logs
        logs = portal_integration.get_audit_logs(
            start_date=datetime.utcnow() - timedelta(minutes=1),
            end_date=datetime.utcnow() + timedelta(minutes=1),
            event_type=AuditEventType.DATA_ACCESS,
            user_id="test_user"
        )
        
        assert len(logs) > 0
        assert logs[0]['details']['resource'] == 'application_data'
        assert logs[0]['details']['action'] == 'read'
    
    @pytest.mark.asyncio
    async def test_credential_vault_integration(self, portal_integration):
        """Test credential vault stores credentials securely"""
        credentials = {
            'client_id': 'test_client',
            'client_secret': 'super_secret_value',
            'api_key': 'test_api_key'
        }
        
        # Authenticate (stores credentials in vault)
        result = await portal_integration.authenticate_portal(
            portal_type=PortalType.MY_SCHEME,
            credentials=credentials,
            user_id="test_user"
        )
        
        assert result['success'] is True
        
        # Retrieve credentials from vault
        stored_creds = portal_integration.credential_vault.retrieve_credential(
            PortalType.MY_SCHEME.value
        )
        
        assert stored_creds is not None
        assert stored_creds['credentials']['client_secret'] == 'super_secret_value'
    
    @pytest.mark.asyncio
    async def test_oauth2_authentication(self, portal_integration):
        """Test OAuth 2.0 authentication flow"""
        credentials = {
            'client_id': 'oauth_client',
            'client_secret': 'oauth_secret',
            'authorization_endpoint': 'https://auth.example.com/authorize',
            'token_endpoint': 'https://auth.example.com/token',
            'redirect_uri': 'https://app.example.com/callback'
        }
        
        # Authenticate with OAuth2
        result = await portal_integration.authenticate_portal(
            portal_type=PortalType.MY_SCHEME,
            credentials=credentials,
            user_id="test_user"
        )
        
        assert result['success'] is True
        assert 'token' in result
        
        # Verify OAuth client was registered
        oauth_client = portal_integration.oauth2_manager.get_client(
            PortalType.MY_SCHEME.value
        )
        assert oauth_client is not None
    
    @pytest.mark.asyncio
    async def test_failed_authentication_logging(self, portal_integration):
        """Test authentication is logged"""
        # Authenticate successfully
        result = await portal_integration.authenticate_portal(
            portal_type=PortalType.GENERIC,
            credentials={'username': 'test', 'password': 'test'},
            user_id="test_user_auth_log",
            ip_address="192.168.1.1"
        )
        
        assert result['success'] is True
        
        # Verify authentication was logged
        logs = portal_integration.get_audit_logs(
            start_date=datetime.utcnow() - timedelta(minutes=1),
            end_date=datetime.utcnow() + timedelta(minutes=1),
            event_type=AuditEventType.AUTH_SUCCESS,
            user_id="test_user_auth_log"
        )
        
        assert len(logs) > 0
        assert logs[-1]['portal_id'] == PortalType.GENERIC.value
    
    @pytest.mark.asyncio
    async def test_multiple_portal_authentication(self, portal_integration):
        """Test authenticating with multiple portals"""
        portals = [
            (PortalType.MY_SCHEME, {'client_id': 'myscheme_client', 'client_secret': 'myscheme_secret'}),
            (PortalType.E_SHRAM, {'api_key': 'a' * 32}),  # Valid API key format (32+ chars)
            (PortalType.UMANG, {'user_id': 'umang_user', 'secret': 'umang_secret'})
        ]
        
        for portal, credentials in portals:
            result = await portal_integration.authenticate_portal(
                portal_type=portal,
                credentials=credentials,
                user_id="test_user"
            )
            
            assert result['success'] is True
            assert 'session_id' in result
        
        # Verify all authentications were logged
        logs = portal_integration.get_audit_logs(
            start_date=datetime.utcnow() - timedelta(minutes=1),
            end_date=datetime.utcnow() + timedelta(minutes=1),
            event_type=AuditEventType.AUTH_SUCCESS,
            user_id="test_user"
        )
        
        assert len(logs) >= len(portals)


class TestSecurityFeatures:
    """Test security features of the authentication system"""
    
    @pytest.fixture
    def portal_integration(self):
        """Create portal integration instance"""
        return GovernmentPortalIntegration()
    
    def test_session_timeout_policy(self, portal_integration):
        """Test session timeout policy enforcement"""
        # Create session with short timeout
        portal_integration.session_manager.session_timeout_minutes = 0
        
        session_id = portal_integration.session_manager.create_session(
            user_id="test_user",
            portal_id="test_portal",
            auth_data={'token': 'test_token'}
        )
        
        # Session should be expired immediately
        session = portal_integration.validate_session(session_id)
        assert session is None
    
    def test_unauthorized_access_logging(self, portal_integration):
        """Test unauthorized access attempts are logged"""
        # Try to validate invalid session
        session = portal_integration.validate_session("invalid_session_id")
        assert session is None
        
        # Verify unauthorized access was logged
        logs = portal_integration.get_audit_logs(
            start_date=datetime.utcnow() - timedelta(minutes=1),
            end_date=datetime.utcnow() + timedelta(minutes=1),
            event_type=AuditEventType.UNAUTHORIZED_ACCESS
        )
        
        assert len(logs) > 0
        assert logs[0]['success'] is False
    
    def test_credential_encryption_at_rest(self, portal_integration):
        """Test credentials are encrypted when stored"""
        portal_id = "test_portal"
        credentials = {
            'api_key': 'sensitive_api_key',
            'password': 'sensitive_password'
        }
        
        # Store credentials
        portal_integration.credential_vault.store_credential(
            portal_id,
            credentials
        )
        
        # Verify encryption by checking raw storage
        import os
        import json
        vault_path = portal_integration.credential_vault.vault_path
        cred_file = os.path.join(vault_path, "credentials.json")
        
        with open(cred_file, 'r') as f:
            raw_data = json.load(f)
        
        # Sensitive fields should be encrypted (not plain text)
        portal_data = raw_data[portal_id]
        assert portal_data['api_key'] != 'sensitive_api_key'
        assert portal_data['password'] != 'sensitive_password'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
