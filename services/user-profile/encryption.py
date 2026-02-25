"""
Encryption module for secure user profile data storage.
Uses AES-256-GCM for encryption with secure key management.
"""

import os
import base64
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionService:
    """Service for encrypting and decrypting user profile data."""
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption service with a master key.
        
        Args:
            master_key: Base64-encoded 256-bit key. If None, generates a new key.
        """
        if master_key:
            self.key = base64.b64decode(master_key)
        else:
            # Generate a new 256-bit key
            self.key = AESGCM.generate_key(bit_length=256)
        
        self.aesgcm = AESGCM(self.key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext using AES-256-GCM.
        
        Args:
            plaintext: The text to encrypt
            
        Returns:
            Base64-encoded encrypted data with nonce prepended
        """
        if not plaintext:
            return ""
        
        # Generate a random 96-bit nonce
        nonce = os.urandom(12)
        
        # Encrypt the data
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        
        # Prepend nonce to ciphertext and encode as base64
        encrypted_data = nonce + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data encrypted with AES-256-GCM.
        
        Args:
            encrypted_data: Base64-encoded encrypted data with nonce
            
        Returns:
            Decrypted plaintext
            
        Raises:
            ValueError: If decryption fails
        """
        if not encrypted_data:
            return ""
        
        try:
            # Decode from base64
            data = base64.b64decode(encrypted_data)
            
            # Extract nonce (first 12 bytes) and ciphertext
            nonce = data[:12]
            ciphertext = data[12:]
            
            # Decrypt the data
            plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def get_key_base64(self) -> str:
        """
        Get the encryption key as a base64-encoded string.
        
        Returns:
            Base64-encoded encryption key
        """
        return base64.b64encode(self.key).decode('utf-8')


def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """
    Derive a 256-bit encryption key from a password using PBKDF2.
    
    Args:
        password: The password to derive the key from
        salt: Salt for key derivation (should be at least 16 bytes)
        
    Returns:
        256-bit derived key
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bits
        salt=salt,
        iterations=100000,
    )
    return kdf.derive(password.encode('utf-8'))
