"""
Unit tests for encryption service.
"""

import pytest
from encryption import EncryptionService, derive_key_from_password


def test_encryption_decryption():
    """Test basic encryption and decryption."""
    service = EncryptionService()
    plaintext = "sensitive user data"
    
    encrypted = service.encrypt(plaintext)
    decrypted = service.decrypt(encrypted)
    
    assert decrypted == plaintext
    assert encrypted != plaintext


def test_encryption_with_master_key():
    """Test encryption with a provided master key."""
    service1 = EncryptionService()
    key = service1.get_key_base64()
    
    # Create second service with same key
    service2 = EncryptionService(key)
    
    plaintext = "test data"
    encrypted = service1.encrypt(plaintext)
    decrypted = service2.decrypt(encrypted)
    
    assert decrypted == plaintext


def test_empty_string_encryption():
    """Test encryption of empty string."""
    service = EncryptionService()
    
    encrypted = service.encrypt("")
    decrypted = service.decrypt("")
    
    assert encrypted == ""
    assert decrypted == ""


def test_unicode_encryption():
    """Test encryption of unicode characters."""
    service = EncryptionService()
    plaintext = "नमस्ते दुनिया 🌍"
    
    encrypted = service.encrypt(plaintext)
    decrypted = service.decrypt(encrypted)
    
    assert decrypted == plaintext


def test_large_data_encryption():
    """Test encryption of large data."""
    service = EncryptionService()
    plaintext = "x" * 10000
    
    encrypted = service.encrypt(plaintext)
    decrypted = service.decrypt(encrypted)
    
    assert decrypted == plaintext


def test_invalid_decryption():
    """Test decryption with invalid data."""
    service = EncryptionService()
    
    with pytest.raises(ValueError):
        service.decrypt("invalid_encrypted_data")


def test_different_keys_fail():
    """Test that different keys cannot decrypt data."""
    service1 = EncryptionService()
    service2 = EncryptionService()
    
    plaintext = "secret data"
    encrypted = service1.encrypt(plaintext)
    
    with pytest.raises(ValueError):
        service2.decrypt(encrypted)


def test_derive_key_from_password():
    """Test key derivation from password."""
    password = "secure_password"
    salt = b"random_salt_1234"
    
    key1 = derive_key_from_password(password, salt)
    key2 = derive_key_from_password(password, salt)
    
    assert key1 == key2
    assert len(key1) == 32  # 256 bits


def test_different_salts_produce_different_keys():
    """Test that different salts produce different keys."""
    password = "secure_password"
    salt1 = b"salt_1"
    salt2 = b"salt_2"
    
    key1 = derive_key_from_password(password, salt1)
    key2 = derive_key_from_password(password, salt2)
    
    assert key1 != key2
