"""
Encryption key management and rotation system.
Provides centralized key management with automatic rotation capabilities.
"""

import os
import json
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class KeyVersion:
    """Represents a versioned encryption key."""
    
    def __init__(self, key_id: str, key: bytes, created_at: datetime, expires_at: datetime):
        self.key_id = key_id
        self.key = key
        self.created_at = created_at
        self.expires_at = expires_at
        self.is_active = True
    
    def is_expired(self) -> bool:
        """Check if the key has expired."""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "key_id": self.key_id,
            "key": base64.b64encode(self.key).decode('utf-8'),
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'KeyVersion':
        """Create from dictionary."""
        key_version = cls(
            key_id=data["key_id"],
            key=base64.b64decode(data["key"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"])
        )
        key_version.is_active = data.get("is_active", True)
        return key_version


class KeyManagementService:
    """
    Centralized key management service with automatic rotation.
    Supports multiple key versions for seamless rotation.
    """
    
    def __init__(self, key_store_path: str = "./data/keys", rotation_days: int = 90):
        """
        Initialize key management service.
        
        Args:
            key_store_path: Directory for storing encrypted keys
            rotation_days: Number of days before key rotation
        """
        self.key_store_path = Path(key_store_path)
        self.key_store_path.mkdir(parents=True, exist_ok=True)
        self.rotation_days = rotation_days
        self.keys: Dict[str, KeyVersion] = {}
        self._load_keys()
        
        # Ensure we have an active key
        if not self.get_active_key():
            self._generate_new_key()
    
    def _load_keys(self) -> None:
        """Load all keys from storage."""
        key_file = self.key_store_path / "keys.json"
        
        if not key_file.exists():
            return
        
        try:
            with open(key_file, 'r') as f:
                data = json.load(f)
                
            for key_data in data.get("keys", []):
                key_version = KeyVersion.from_dict(key_data)
                self.keys[key_version.key_id] = key_version
        except Exception as e:
            print(f"Error loading keys: {e}")
    
    def _save_keys(self) -> None:
        """Save all keys to storage."""
        key_file = self.key_store_path / "keys.json"
        
        data = {
            "keys": [key.to_dict() for key in self.keys.values()],
            "last_updated": datetime.utcnow().isoformat()
        }
        
        with open(key_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _generate_new_key(self) -> KeyVersion:
        """Generate a new encryption key."""
        import uuid
        # Use UUID to ensure uniqueness
        key_id = f"key_{uuid.uuid4().hex[:16]}"
        key = AESGCM.generate_key(bit_length=256)
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(days=self.rotation_days)
        
        key_version = KeyVersion(key_id, key, created_at, expires_at)
        self.keys[key_id] = key_version
        self._save_keys()
        
        return key_version
    
    def get_active_key(self) -> Optional[KeyVersion]:
        """Get the current active encryption key."""
        for key in self.keys.values():
            if key.is_active and not key.is_expired():
                return key
        return None
    
    def get_key(self, key_id: str) -> Optional[KeyVersion]:
        """Get a specific key by ID."""
        return self.keys.get(key_id)
    
    def rotate_key(self) -> KeyVersion:
        """
        Rotate to a new encryption key.
        Marks the current key as inactive and generates a new one.
        
        Returns:
            New active key version
        """
        # Mark current active key as inactive
        current_key = self.get_active_key()
        if current_key:
            current_key.is_active = False
        
        # Generate new key
        new_key = self._generate_new_key()
        self._save_keys()
        
        return new_key
    
    def check_rotation_needed(self) -> bool:
        """Check if key rotation is needed."""
        active_key = self.get_active_key()
        
        if not active_key:
            return True
        
        # Check if key is close to expiration (within 7 days)
        days_until_expiration = (active_key.expires_at - datetime.utcnow()).days
        return days_until_expiration <= 7
    
    def cleanup_old_keys(self, keep_days: int = 365) -> int:
        """
        Remove old inactive keys that are no longer needed.
        
        Args:
            keep_days: Number of days to keep old keys for decryption
            
        Returns:
            Number of keys removed
        """
        cutoff_date = datetime.utcnow() - timedelta(days=keep_days)
        keys_to_remove = []
        
        for key_id, key in self.keys.items():
            if not key.is_active and key.created_at < cutoff_date:
                keys_to_remove.append(key_id)
        
        for key_id in keys_to_remove:
            del self.keys[key_id]
        
        if keys_to_remove:
            self._save_keys()
        
        return len(keys_to_remove)
    
    def get_all_keys(self) -> List[KeyVersion]:
        """Get all keys (for migration purposes)."""
        return list(self.keys.values())
