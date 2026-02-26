"""
Enhanced encryption service with key rotation support.
Provides AES-256-GCM encryption with versioned keys.
"""

import os
import base64
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .key_management import KeyManagementService, KeyVersion


class EncryptionService:
    """
    Enhanced encryption service with automatic key rotation.
    Uses AES-256-GCM for authenticated encryption.
    """
    
    def __init__(self, key_manager: Optional[KeyManagementService] = None):
        """
        Initialize encryption service.
        
        Args:
            key_manager: Key management service instance
        """
        self.key_manager = key_manager or KeyManagementService()
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext using the current active key.
        
        Args:
            plaintext: The text to encrypt
            
        Returns:
            Base64-encoded encrypted data with key_id and nonce
            Format: key_id:nonce:ciphertext (all base64 encoded)
        """
        if not plaintext:
            return ""
        
        # Get active key
        key_version = self.key_manager.get_active_key()
        if not key_version:
            raise ValueError("No active encryption key available")
        
        # Create AESGCM cipher
        aesgcm = AESGCM(key_version.key)
        
        # Generate a random 96-bit nonce
        nonce = os.urandom(12)
        
        # Encrypt the data
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        
        # Format: key_id:nonce:ciphertext
        key_id_b64 = base64.b64encode(key_version.key_id.encode('utf-8')).decode('utf-8')
        nonce_b64 = base64.b64encode(nonce).decode('utf-8')
        ciphertext_b64 = base64.b64encode(ciphertext).decode('utf-8')
        
        return f"{key_id_b64}:{nonce_b64}:{ciphertext_b64}"
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data encrypted with any version of the key.
        
        Args:
            encrypted_data: Encrypted data in format key_id:nonce:ciphertext
            
        Returns:
            Decrypted plaintext
            
        Raises:
            ValueError: If decryption fails or key not found
        """
        if not encrypted_data:
            return ""
        
        try:
            # Parse encrypted data
            parts = encrypted_data.split(':')
            if len(parts) != 3:
                raise ValueError("Invalid encrypted data format")
            
            key_id_b64, nonce_b64, ciphertext_b64 = parts
            
            # Decode components
            key_id = base64.b64decode(key_id_b64).decode('utf-8')
            nonce = base64.b64decode(nonce_b64)
            ciphertext = base64.b64decode(ciphertext_b64)
            
            # Get the key version
            key_version = self.key_manager.get_key(key_id)
            if not key_version:
                raise ValueError(f"Encryption key not found: {key_id}")
            
            # Create AESGCM cipher
            aesgcm = AESGCM(key_version.key)
            
            # Decrypt the data
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def re_encrypt(self, encrypted_data: str) -> str:
        """
        Re-encrypt data with the current active key.
        Useful for key rotation.
        
        Args:
            encrypted_data: Data encrypted with an old key
            
        Returns:
            Data encrypted with the current active key
        """
        # Decrypt with old key
        plaintext = self.decrypt(encrypted_data)
        
        # Encrypt with current key
        return self.encrypt(plaintext)
    
    def check_key_rotation_needed(self) -> bool:
        """Check if key rotation is needed."""
        return self.key_manager.check_rotation_needed()
    
    def rotate_key(self) -> KeyVersion:
        """Rotate to a new encryption key."""
        return self.key_manager.rotate_key()


class FieldEncryption:
    """
    Helper class for encrypting specific fields in data structures.
    """
    
    def __init__(self, encryption_service: EncryptionService):
        """
        Initialize field encryption helper.
        
        Args:
            encryption_service: Encryption service instance
        """
        self.encryption_service = encryption_service
    
    def encrypt_dict_fields(self, data: dict, fields_to_encrypt: list) -> dict:
        """
        Encrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary containing data
            fields_to_encrypt: List of field names to encrypt
            
        Returns:
            Dictionary with encrypted fields
        """
        encrypted_data = data.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field]:
                value = str(encrypted_data[field])
                encrypted_data[field] = self.encryption_service.encrypt(value)
                encrypted_data[f"{field}_encrypted"] = True
        
        return encrypted_data
    
    def decrypt_dict_fields(self, data: dict, fields_to_decrypt: list) -> dict:
        """
        Decrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary containing encrypted data
            fields_to_decrypt: List of field names to decrypt
            
        Returns:
            Dictionary with decrypted fields
        """
        decrypted_data = data.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data.get(f"{field}_encrypted"):
                encrypted_value = decrypted_data[field]
                decrypted_data[field] = self.encryption_service.decrypt(encrypted_value)
                decrypted_data.pop(f"{field}_encrypted", None)
        
        return decrypted_data
