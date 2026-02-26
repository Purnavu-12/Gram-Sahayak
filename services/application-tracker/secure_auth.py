"""
Secure Government Portal Authentication System
Implements OAuth 2.0, credential vault integration, audit logging, and session management.

Validates: Requirement 9.4 (secure token-based access for government portals)
"""

import os
import json
import time
import hashlib
import secrets
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from enum import Enum
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class AuthMethod(str, Enum):
    """Supported authentication methods"""
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    JWT = "jwt"
    BASIC = "basic"


class SessionStatus(str, Enum):
    """Session status states"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    TIMEOUT = "timeout"


class AuditEventType(str, Enum):
    """Types of audit events"""
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_REVOKE = "token_revoke"
    SESSION_CREATE = "session_create"
    SESSION_EXPIRE = "session_expire"
    SESSION_TIMEOUT = "session_timeout"
    CREDENTIAL_ACCESS = "credential_access"
    CREDENTIAL_UPDATE = "credential_update"
    DATA_ACCESS = "data_access"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


class SimpleEncryption:
    """Simple AES-256-GCM encryption for credentials"""
    
    def __init__(self, key: Optional[bytes] = None):
        """Initialize with encryption key"""
        self.key = key or AESGCM.generate_key(bit_length=256)
        self.cipher = AESGCM(self.key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext"""
        if not plaintext:
            return ""
        
        nonce = os.urandom(12)
        ciphertext = self.cipher.encrypt(nonce, plaintext.encode('utf-8'), None)
        
        # Format: nonce:ciphertext (both base64)
        nonce_b64 = base64.b64encode(nonce).decode('utf-8')
        ciphertext_b64 = base64.b64encode(ciphertext).decode('utf-8')
        
        return f"{nonce_b64}:{ciphertext_b64}"
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt encrypted data"""
        if not encrypted_data:
            return ""
        
        try:
            parts = encrypted_data.split(':')
            if len(parts) != 2:
                raise ValueError("Invalid encrypted data format")
            
            nonce = base64.b64decode(parts[0])
            ciphertext = base64.b64decode(parts[1])
            
            plaintext = self.cipher.decrypt(nonce, ciphertext, None)
            return plaintext.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")


class CredentialVault:
    """
    Secure credential storage using encryption.
    Integrates with encryption service for key management.
    """
    
    def __init__(self, vault_path: str = "./data/vault"):
        """
        Initialize credential vault.
        
        Args:
            vault_path: Directory for storing encrypted credentials
        """
        self.vault_path = vault_path
        os.makedirs(vault_path, exist_ok=True)
        
        # Initialize encryption
        self.encryption = SimpleEncryption()
        
        # Load credentials
        self.credentials: Dict[str, Dict[str, Any]] = {}
        self._load_credentials()
    
    def _load_credentials(self) -> None:
        """Load encrypted credentials from storage"""
        cred_file = os.path.join(self.vault_path, "credentials.json")
        
        if not os.path.exists(cred_file):
            return
        
        try:
            with open(cred_file, 'r') as f:
                encrypted_data = json.load(f)
            
            # Decrypt each credential set
            for portal_id, cred_data in encrypted_data.items():
                self.credentials[portal_id] = self._decrypt_credential(cred_data)
        except Exception as e:
            print(f"Error loading credentials: {e}")
    
    def _save_credentials(self) -> None:
        """Save encrypted credentials to storage"""
        cred_file = os.path.join(self.vault_path, "credentials.json")
        
        # Encrypt each credential set
        encrypted_data = {}
        for portal_id, cred_data in self.credentials.items():
            encrypted_data[portal_id] = self._encrypt_credential(cred_data)
        
        with open(cred_file, 'w') as f:
            json.dump(encrypted_data, f, indent=2)
    
    def _encrypt_credential(self, credential: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive credential fields"""
        sensitive_fields = [
            'client_secret', 'api_key', 'password', 'secret',
            'refresh_token', 'access_token', 'private_key'
        ]
        
        encrypted_data = credential.copy()
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                value = str(encrypted_data[field])
                encrypted_data[field] = self.encryption.encrypt(value)
                encrypted_data[f"{field}_encrypted"] = True
        
        return encrypted_data
    
    def _decrypt_credential(self, encrypted_credential: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive credential fields"""
        sensitive_fields = [
            'client_secret', 'api_key', 'password', 'secret',
            'refresh_token', 'access_token', 'private_key'
        ]
        
        decrypted_data = encrypted_credential.copy()
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data.get(f"{field}_encrypted"):
                encrypted_value = decrypted_data[field]
                decrypted_data[field] = self.encryption.decrypt(encrypted_value)
                decrypted_data.pop(f"{field}_encrypted", None)
        
        return decrypted_data
    
    def store_credential(
        self,
        portal_id: str,
        credential_data: Dict[str, Any]
    ) -> bool:
        """
        Store credentials securely in the vault.
        
        Args:
            portal_id: Unique identifier for the portal
            credential_data: Credential information to store
            
        Returns:
            Success status
        """
        try:
            # Add metadata
            credential_data['created_at'] = datetime.utcnow().isoformat()
            credential_data['updated_at'] = datetime.utcnow().isoformat()
            
            self.credentials[portal_id] = credential_data
            self._save_credentials()
            return True
        except Exception as e:
            print(f"Error storing credential: {e}")
            return False
    
    def retrieve_credential(self, portal_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve credentials from the vault.
        
        Args:
            portal_id: Unique identifier for the portal
            
        Returns:
            Decrypted credential data or None
        """
        return self.credentials.get(portal_id)
    
    def update_credential(
        self,
        portal_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update existing credentials.
        
        Args:
            portal_id: Unique identifier for the portal
            updates: Fields to update
            
        Returns:
            Success status
        """
        if portal_id not in self.credentials:
            return False
        
        try:
            self.credentials[portal_id].update(updates)
            self.credentials[portal_id]['updated_at'] = datetime.utcnow().isoformat()
            self._save_credentials()
            return True
        except Exception as e:
            print(f"Error updating credential: {e}")
            return False
    
    def delete_credential(self, portal_id: str) -> bool:
        """
        Delete credentials from the vault.
        
        Args:
            portal_id: Unique identifier for the portal
            
        Returns:
            Success status
        """
        if portal_id in self.credentials:
            del self.credentials[portal_id]
            self._save_credentials()
            return True
        return False
    
    def rotate_keys(self) -> bool:
        """
        Rotate encryption keys and re-encrypt all credentials.
        
        Returns:
            Success status
        """
        try:
            # Generate new key
            new_encryption = SimpleEncryption()
            
            # Re-encrypt all credentials with new key
            for portal_id, cred_data in self.credentials.items():
                # Credentials are already decrypted in memory
                pass
            
            # Update encryption instance
            self.encryption = new_encryption
            
            # Save with new encryption
            self._save_credentials()
            return True
        except Exception as e:
            print(f"Error rotating keys: {e}")
            return False


class AuditLogger:
    """
    Comprehensive audit logging for all authentication and data access events.
    """
    
    def __init__(self, log_path: str = "./data/audit"):
        """
        Initialize audit logger.
        
        Args:
            log_path: Directory for storing audit logs
        """
        self.log_path = log_path
        os.makedirs(log_path, exist_ok=True)
    
    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        portal_id: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            user_id: User identifier
            portal_id: Portal identifier
            session_id: Session identifier
            details: Additional event details
            success: Whether the event was successful
            ip_address: IP address of the request
        """
        timestamp = datetime.utcnow()
        
        # Create audit entry
        audit_entry = {
            'timestamp': timestamp.isoformat(),
            'event_type': event_type.value,
            'user_id': user_id,
            'portal_id': portal_id,
            'session_id': session_id,
            'success': success,
            'ip_address': ip_address,
            'details': details or {}
        }
        
        # Write to daily log file
        log_file = os.path.join(
            self.log_path,
            f"audit_{timestamp.strftime('%Y%m%d')}.jsonl"
        )
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')
        except Exception as e:
            print(f"Error writing audit log: {e}")
    
    def query_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        portal_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query audit logs with filters.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            event_type: Filter by event type
            user_id: Filter by user
            portal_id: Filter by portal
            
        Returns:
            List of matching audit entries
        """
        results = []
        
        # Iterate through date range
        current_date = start_date
        while current_date <= end_date:
            log_file = os.path.join(
                self.log_path,
                f"audit_{current_date.strftime('%Y%m%d')}.jsonl"
            )
            
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        for line in f:
                            entry = json.loads(line)
                            
                            # Apply filters
                            if event_type and entry['event_type'] != event_type.value:
                                continue
                            if user_id and entry['user_id'] != user_id:
                                continue
                            if portal_id and entry['portal_id'] != portal_id:
                                continue
                            
                            results.append(entry)
                except Exception as e:
                    print(f"Error reading log file {log_file}: {e}")
            
            current_date += timedelta(days=1)
        
        return results


class SessionManager:
    """
    Session management with timeout policies and security controls.
    """
    
    def __init__(
        self,
        session_timeout_minutes: int = 30,
        max_idle_minutes: int = 15
    ):
        """
        Initialize session manager.
        
        Args:
            session_timeout_minutes: Maximum session duration
            max_idle_minutes: Maximum idle time before timeout
        """
        self.session_timeout_minutes = session_timeout_minutes
        self.max_idle_minutes = max_idle_minutes
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(
        self,
        user_id: str,
        portal_id: str,
        auth_data: Dict[str, Any]
    ) -> str:
        """
        Create a new authenticated session.
        
        Args:
            user_id: User identifier
            portal_id: Portal identifier
            auth_data: Authentication data (tokens, etc.)
            
        Returns:
            Session ID
        """
        session_id = self._generate_session_id(user_id, portal_id)
        
        now = datetime.utcnow()
        self.sessions[session_id] = {
            'session_id': session_id,
            'user_id': user_id,
            'portal_id': portal_id,
            'auth_data': auth_data,
            'created_at': now,
            'last_activity': now,
            'expires_at': now + timedelta(minutes=self.session_timeout_minutes),
            'status': SessionStatus.ACTIVE.value
        }
        
        return session_id
    
    def _generate_session_id(self, user_id: str, portal_id: str) -> str:
        """Generate a secure session ID"""
        random_bytes = secrets.token_bytes(32)
        data = f"{user_id}:{portal_id}:{time.time()}:{random_bytes.hex()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if invalid/expired
        """
        session = self.sessions.get(session_id)
        
        if not session:
            return None
        
        # Check if session is revoked
        if session['status'] == SessionStatus.REVOKED.value:
            return None
        
        # Check if session is expired
        if self._is_session_expired(session):
            self._expire_session(session_id)
            return None
        
        # Check idle timeout
        if self._is_session_idle(session):
            self._timeout_session(session_id)
            return None
        
        # Update last activity
        session['last_activity'] = datetime.utcnow()
        
        return session
    
    def _is_session_expired(self, session: Dict[str, Any]) -> bool:
        """Check if session has expired"""
        return datetime.utcnow() > session['expires_at']
    
    def _is_session_idle(self, session: Dict[str, Any]) -> bool:
        """Check if session has been idle too long"""
        idle_time = datetime.utcnow() - session['last_activity']
        return idle_time.total_seconds() > (self.max_idle_minutes * 60)
    
    def _expire_session(self, session_id: str) -> None:
        """Mark session as expired"""
        if session_id in self.sessions:
            self.sessions[session_id]['status'] = SessionStatus.EXPIRED.value
    
    def _timeout_session(self, session_id: str) -> None:
        """Mark session as timed out"""
        if session_id in self.sessions:
            self.sessions[session_id]['status'] = SessionStatus.TIMEOUT.value
    
    def revoke_session(self, session_id: str) -> bool:
        """
        Revoke a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Success status
        """
        if session_id in self.sessions:
            self.sessions[session_id]['status'] = SessionStatus.REVOKED.value
            return True
        return False
    
    def refresh_session(self, session_id: str) -> bool:
        """
        Refresh session expiration.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Success status
        """
        session = self.get_session(session_id)
        
        if not session:
            return False
        
        # Extend expiration
        session['expires_at'] = datetime.utcnow() + timedelta(
            minutes=self.session_timeout_minutes
        )
        session['last_activity'] = datetime.utcnow()
        
        return True
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions from memory.
        
        Returns:
            Number of sessions cleaned up
        """
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if (session['status'] != SessionStatus.ACTIVE.value or
                self._is_session_expired(session)):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        return len(expired_sessions)
