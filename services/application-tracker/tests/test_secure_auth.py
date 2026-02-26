"""
Unit tests for secure government portal authentication.
Tests OAuth 2.0, credential vault, audit logging, and session management.

Validates: Requirement 9.4
"""

import pytest
import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.append('..')

from secure_auth import (
    CredentialVault,
    AuditLogger,
    SessionManager,
    AuthMethod,
    AuditEventType,
    SessionStatus
)
from oauth2_client import OAuth2Client, OAuth2TokenManager


class TestCredentialVault:
    """Test credential vault functionality"""
    
    @pytest.fixture
    def temp_vault_path(self):
        """Create temporary vault directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def vault(self, temp_vault_path):
        """Create credential vault instance"""
        return CredentialVault(vault_path=temp_vault_path)
    
    def test_store_and_retrieve_credential(self, vault):
        """Test storing and retrieving credentials"""
        portal_id = "test_portal"
        credential_data = {
            'client_id': 'test_client',
            'client_secret': 'super_secret_key',
            'api_key': 'test_api_key_12345'
        }
        
        # Store credential
        success = vault.store_credential(portal_id, credential_data)
        assert success is True
        
        # Retrieve credential
        retrieved = vault.retrieve_credential(portal_id)
        assert retrieved is not None
        assert retrieved['client_id'] == 'test_client'
        assert retrieved['client_secret'] == 'super_secret_key'
        assert retrieved['api_key'] == 'test_api_key_12345'
        assert 'created_at' in retrieved
        assert 'updated_at' in retrieved
    
    def test_credential_encryption(self, vault, temp_vault_path):
        """Test that credentials are encrypted on disk"""
        portal_id = "test_portal"
        credential_data = {
            'client_secret': 'super_secret_key',
            'password': 'my_password'
        }
        
        # Store credential
        vault.store_credential(portal_id, credential_data)
        
        # Read raw file to verify encryption
        cred_file = os.path.join(temp_vault_path, "credentials.json")
        with open(cred_file, 'r') as f:
            raw_data = json.load(f)
        
        # Verify sensitive fields are encrypted (not plain text)
        portal_data = raw_data[portal_id]
        assert portal_data['client_secret'] != 'super_secret_key'
        assert portal_data['password'] != 'my_password'
        assert portal_data['client_secret_encrypted'] is True
        assert portal_data['password_encrypted'] is True
    
    def test_update_credential(self, vault):
        """Test updating existing credentials"""
        portal_id = "test_portal"
        
        # Store initial credential
        vault.store_credential(portal_id, {'api_key': 'old_key'})
        
        # Update credential
        success = vault.update_credential(portal_id, {'api_key': 'new_key'})
        assert success is True
        
        # Verify update
        retrieved = vault.retrieve_credential(portal_id)
        assert retrieved['api_key'] == 'new_key'
    
    def test_delete_credential(self, vault):
        """Test deleting credentials"""
        portal_id = "test_portal"
        
        # Store credential
        vault.store_credential(portal_id, {'api_key': 'test_key'})
        
        # Delete credential
        success = vault.delete_credential(portal_id)
        assert success is True
        
        # Verify deletion
        retrieved = vault.retrieve_credential(portal_id)
        assert retrieved is None
    
    def test_nonexistent_credential(self, vault):
        """Test retrieving non-existent credential"""
        retrieved = vault.retrieve_credential("nonexistent_portal")
        assert retrieved is None
    
    def test_key_rotation(self, vault):
        """Test encryption key rotation"""
        portal_id = "test_portal"
        credential_data = {'client_secret': 'secret_value'}
        
        # Store credential with original key
        vault.store_credential(portal_id, credential_data)
        
        # Rotate keys
        success = vault.rotate_keys()
        assert success is True
        
        # Verify credential can still be retrieved
        retrieved = vault.retrieve_credential(portal_id)
        assert retrieved is not None
        assert retrieved['client_secret'] == 'secret_value'


class TestAuditLogger:
    """Test audit logging functionality"""
    
    @pytest.fixture
    def temp_log_path(self):
        """Create temporary log directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def logger(self, temp_log_path):
        """Create audit logger instance"""
        return AuditLogger(log_path=temp_log_path)
    
    def test_log_auth_success(self, logger):
        """Test logging successful authentication"""
        logger.log_event(
            event_type=AuditEventType.AUTH_SUCCESS,
            user_id="user123",
            portal_id="test_portal",
            session_id="session456",
            success=True,
            ip_address="192.168.1.1"
        )
        
        # Verify log file was created
        today = datetime.utcnow().strftime('%Y%m%d')
        log_file = os.path.join(logger.log_path, f"audit_{today}.jsonl")
        assert os.path.exists(log_file)
        
        # Read and verify log entry
        with open(log_file, 'r') as f:
            entry = json.loads(f.readline())
        
        assert entry['event_type'] == 'auth_success'
        assert entry['user_id'] == 'user123'
        assert entry['portal_id'] == 'test_portal'
        assert entry['session_id'] == 'session456'
        assert entry['success'] is True
        assert entry['ip_address'] == '192.168.1.1'
    
    def test_log_auth_failure(self, logger):
        """Test logging failed authentication"""
        logger.log_event(
            event_type=AuditEventType.AUTH_FAILURE,
            user_id="user123",
            portal_id="test_portal",
            details={'error': 'invalid_credentials'},
            success=False,
            ip_address="192.168.1.1"
        )
        
        # Query logs
        logs = logger.query_logs(
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow() + timedelta(days=1),
            event_type=AuditEventType.AUTH_FAILURE
        )
        
        assert len(logs) == 1
        assert logs[0]['success'] is False
        assert logs[0]['details']['error'] == 'invalid_credentials'
    
    def test_query_logs_by_user(self, logger):
        """Test querying logs by user ID"""
        # Log events for different users
        logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id="user1",
            portal_id="portal1"
        )
        logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id="user2",
            portal_id="portal1"
        )
        
        # Query for specific user
        logs = logger.query_logs(
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow() + timedelta(days=1),
            user_id="user1"
        )
        
        assert len(logs) == 1
        assert logs[0]['user_id'] == 'user1'
    
    def test_query_logs_by_portal(self, logger):
        """Test querying logs by portal ID"""
        # Log events for different portals
        logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id="user1",
            portal_id="portal1"
        )
        logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id="user1",
            portal_id="portal2"
        )
        
        # Query for specific portal
        logs = logger.query_logs(
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow() + timedelta(days=1),
            portal_id="portal1"
        )
        
        assert len(logs) == 1
        assert logs[0]['portal_id'] == 'portal1'


class TestSessionManager:
    """Test session management functionality"""
    
    @pytest.fixture
    def session_manager(self):
        """Create session manager instance"""
        return SessionManager(
            session_timeout_minutes=30,
            max_idle_minutes=15
        )
    
    def test_create_session(self, session_manager):
        """Test creating a new session"""
        session_id = session_manager.create_session(
            user_id="user123",
            portal_id="test_portal",
            auth_data={'token': 'test_token'}
        )
        
        assert session_id is not None
        assert len(session_id) == 64  # SHA256 hex digest
        
        # Retrieve session
        session = session_manager.get_session(session_id)
        assert session is not None
        assert session['user_id'] == 'user123'
        assert session['portal_id'] == 'test_portal'
        assert session['status'] == SessionStatus.ACTIVE.value
    
    def test_session_expiration(self, session_manager):
        """Test session expiration"""
        # Create session with short timeout
        session_manager.session_timeout_minutes = 0  # Immediate expiration
        
        session_id = session_manager.create_session(
            user_id="user123",
            portal_id="test_portal",
            auth_data={'token': 'test_token'}
        )
        
        # Try to retrieve expired session
        session = session_manager.get_session(session_id)
        assert session is None
        
        # Verify session is marked as expired
        expired_session = session_manager.sessions.get(session_id)
        assert expired_session['status'] == SessionStatus.EXPIRED.value
    
    def test_session_refresh(self, session_manager):
        """Test refreshing session expiration"""
        session_id = session_manager.create_session(
            user_id="user123",
            portal_id="test_portal",
            auth_data={'token': 'test_token'}
        )
        
        # Get original expiration
        original_session = session_manager.sessions[session_id]
        original_expires = original_session['expires_at']
        
        # Refresh session
        import time
        time.sleep(0.1)  # Small delay to ensure time difference
        success = session_manager.refresh_session(session_id)
        assert success is True
        
        # Verify expiration was extended
        refreshed_session = session_manager.sessions[session_id]
        assert refreshed_session['expires_at'] > original_expires
    
    def test_revoke_session(self, session_manager):
        """Test revoking a session"""
        session_id = session_manager.create_session(
            user_id="user123",
            portal_id="test_portal",
            auth_data={'token': 'test_token'}
        )
        
        # Revoke session
        success = session_manager.revoke_session(session_id)
        assert success is True
        
        # Verify session is revoked
        session = session_manager.get_session(session_id)
        assert session is None
        
        revoked_session = session_manager.sessions.get(session_id)
        assert revoked_session['status'] == SessionStatus.REVOKED.value
    
    def test_cleanup_expired_sessions(self, session_manager):
        """Test cleaning up expired sessions"""
        # Create multiple sessions with immediate expiration
        session_manager.session_timeout_minutes = 0
        
        session_ids = []
        for i in range(3):
            session_id = session_manager.create_session(
                user_id=f"user{i}",
                portal_id="test_portal",
                auth_data={'token': f'token{i}'}
            )
            session_ids.append(session_id)
        
        # Cleanup expired sessions
        cleaned = session_manager.cleanup_expired_sessions()
        assert cleaned == 3
        
        # Verify sessions were removed
        for session_id in session_ids:
            assert session_id not in session_manager.sessions


class TestOAuth2Client:
    """Test OAuth 2.0 client functionality"""
    
    @pytest.fixture
    def oauth_client(self):
        """Create OAuth2 client instance"""
        return OAuth2Client(
            client_id="test_client_id",
            client_secret="test_client_secret",
            authorization_endpoint="https://auth.example.com/authorize",
            token_endpoint="https://auth.example.com/token",
            redirect_uri="https://app.example.com/callback",
            scope="read write"
        )
    
    def test_generate_authorization_url(self, oauth_client):
        """Test generating authorization URL with PKCE"""
        auth_url, state, code_verifier = oauth_client.generate_authorization_url()
        
        # Verify URL components
        assert "https://auth.example.com/authorize" in auth_url
        assert "response_type=code" in auth_url
        assert f"client_id={oauth_client.client_id}" in auth_url
        assert "code_challenge=" in auth_url
        assert "code_challenge_method=S256" in auth_url
        
        # Verify state and code_verifier
        assert len(state) > 0
        assert len(code_verifier) > 0
    
    def test_code_challenge_generation(self, oauth_client):
        """Test PKCE code challenge generation"""
        code_verifier = oauth_client._generate_code_verifier()
        code_challenge = oauth_client._generate_code_challenge(code_verifier)
        
        # Verify code verifier length
        assert len(code_verifier) > 43
        
        # Verify code challenge is base64 URL-safe
        assert len(code_challenge) > 0
        assert '=' not in code_challenge  # No padding
    
    def test_token_expiration_check(self, oauth_client):
        """Test token expiration checking"""
        # No token set
        assert oauth_client.is_token_expired() is True
        
        # Set token with future expiration
        oauth_client.access_token = "test_token"
        oauth_client.token_expires_at = datetime.utcnow() + timedelta(hours=1)
        assert oauth_client.is_token_expired() is False
        
        # Set token with past expiration
        oauth_client.token_expires_at = datetime.utcnow() - timedelta(hours=1)
        assert oauth_client.is_token_expired() is True


class TestOAuth2TokenManager:
    """Test OAuth 2.0 token manager"""
    
    @pytest.fixture
    def token_manager(self):
        """Create token manager instance"""
        return OAuth2TokenManager()
    
    def test_register_and_get_client(self, token_manager):
        """Test registering and retrieving OAuth clients"""
        portal_id = "test_portal"
        client_config = {
            'client_id': 'test_client',
            'client_secret': 'test_secret',
            'authorization_endpoint': 'https://auth.example.com/authorize',
            'token_endpoint': 'https://auth.example.com/token',
            'redirect_uri': 'https://app.example.com/callback'
        }
        
        # Register client
        client = token_manager.register_client(portal_id, client_config)
        assert client is not None
        assert isinstance(client, OAuth2Client)
        
        # Retrieve client
        retrieved_client = token_manager.get_client(portal_id)
        assert retrieved_client is client
    
    def test_get_nonexistent_client(self, token_manager):
        """Test retrieving non-existent client"""
        client = token_manager.get_client("nonexistent_portal")
        assert client is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
