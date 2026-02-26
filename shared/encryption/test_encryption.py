"""
Unit tests for comprehensive encryption module.
Tests AES-256 encryption, key management, PII anonymization, and TLS configuration.
"""

import pytest
import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from .key_management import KeyManagementService, KeyVersion
from .encryption_service import EncryptionService, FieldEncryption
from .pii_anonymizer import PIIAnonymizer, ConversationAnonymizer, PIIPattern
from .tls_config import TLSConfig, SecureHTTPClient


class TestKeyManagement:
    """Tests for key management and rotation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.key_manager = KeyManagementService(
            key_store_path=self.temp_dir,
            rotation_days=90
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_key_generation(self):
        """Test automatic key generation on initialization."""
        active_key = self.key_manager.get_active_key()
        assert active_key is not None
        assert active_key.is_active
        assert not active_key.is_expired()
    
    def test_key_rotation(self):
        """Test key rotation creates new active key."""
        old_key = self.key_manager.get_active_key()
        old_key_id = old_key.key_id
        
        new_key = self.key_manager.rotate_key()
        
        assert new_key.key_id != old_key_id
        assert new_key.is_active
        assert not old_key.is_active
        assert self.key_manager.get_active_key().key_id == new_key.key_id
    
    def test_key_persistence(self):
        """Test keys are persisted to storage."""
        key_id = self.key_manager.get_active_key().key_id
        
        # Create new manager with same storage
        new_manager = KeyManagementService(key_store_path=self.temp_dir)
        
        assert new_manager.get_active_key().key_id == key_id
    
    def test_rotation_check(self):
        """Test rotation needed check."""
        # New key should not need rotation
        assert not self.key_manager.check_rotation_needed()
        
        # Manually expire the key
        active_key = self.key_manager.get_active_key()
        active_key.expires_at = datetime.utcnow() + timedelta(days=5)
        
        # Should need rotation (within 7 days)
        assert self.key_manager.check_rotation_needed()
    
    def test_old_key_cleanup(self):
        """Test cleanup of old inactive keys."""
        # Create multiple keys
        for _ in range(3):
            self.key_manager.rotate_key()
        
        # Manually age some keys
        for key in list(self.key_manager.keys.values())[:-1]:
            key.created_at = datetime.utcnow() - timedelta(days=400)
            key.is_active = False
        
        # Save the modified keys
        self.key_manager._save_keys()
        
        # Cleanup old keys
        removed = self.key_manager.cleanup_old_keys(keep_days=365)
        
        assert removed > 0


class TestEncryptionService:
    """Tests for encryption service with key rotation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.key_manager = KeyManagementService(key_store_path=self.temp_dir)
        self.encryption_service = EncryptionService(self.key_manager)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_encrypt_decrypt(self):
        """Test basic encryption and decryption."""
        plaintext = "Sensitive user data"
        
        encrypted = self.encryption_service.encrypt(plaintext)
        decrypted = self.encryption_service.decrypt(encrypted)
        
        assert decrypted == plaintext
        assert encrypted != plaintext
    
    def test_empty_string(self):
        """Test encryption of empty string."""
        encrypted = self.encryption_service.encrypt("")
        assert encrypted == ""
        
        decrypted = self.encryption_service.decrypt("")
        assert decrypted == ""
    
    def test_unicode_text(self):
        """Test encryption of Unicode text."""
        plaintext = "नमस्ते, यह परीक्षण है"
        
        encrypted = self.encryption_service.encrypt(plaintext)
        decrypted = self.encryption_service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_decrypt_with_old_key(self):
        """Test decryption with rotated keys."""
        plaintext = "Data encrypted with old key"
        
        # Encrypt with current key
        encrypted = self.encryption_service.encrypt(plaintext)
        old_key_id = self.key_manager.get_active_key().key_id
        
        # Rotate key
        new_key = self.encryption_service.rotate_key()
        
        # Verify rotation happened
        assert new_key.key_id != old_key_id
        
        # Old key should still exist in key manager
        old_key = self.key_manager.get_key(old_key_id)
        assert old_key is not None
        
        # Should still decrypt with old key
        decrypted = self.encryption_service.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_re_encryption(self):
        """Test re-encryption with new key."""
        plaintext = "Data to re-encrypt"
        
        # Encrypt with current key
        old_encrypted = self.encryption_service.encrypt(plaintext)
        old_key_id = self.key_manager.get_active_key().key_id
        
        # Rotate key
        self.encryption_service.rotate_key()
        
        # Re-encrypt
        new_encrypted = self.encryption_service.re_encrypt(old_encrypted)
        new_key_id = self.key_manager.get_active_key().key_id
        
        # Verify different keys used
        assert old_key_id != new_key_id
        
        # Verify decryption works
        decrypted = self.encryption_service.decrypt(new_encrypted)
        assert decrypted == plaintext
    
    def test_invalid_encrypted_data(self):
        """Test decryption of invalid data."""
        with pytest.raises(ValueError):
            self.encryption_service.decrypt("invalid:data:format")


class TestFieldEncryption:
    """Tests for field-level encryption."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        key_manager = KeyManagementService(key_store_path=self.temp_dir)
        encryption_service = EncryptionService(key_manager)
        self.field_encryption = FieldEncryption(encryption_service)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_encrypt_dict_fields(self):
        """Test encrypting specific fields in dictionary."""
        data = {
            'name': 'Rajesh Kumar',
            'phone': '9876543210',
            'age': 35,
            'village': 'Rampur'
        }
        
        encrypted = self.field_encryption.encrypt_dict_fields(
            data,
            ['name', 'phone']
        )
        
        assert encrypted['name'] != data['name']
        assert encrypted['phone'] != data['phone']
        assert encrypted['age'] == data['age']
        assert encrypted['name_encrypted'] is True
        assert encrypted['phone_encrypted'] is True
    
    def test_decrypt_dict_fields(self):
        """Test decrypting specific fields in dictionary."""
        data = {
            'name': 'Rajesh Kumar',
            'phone': '9876543210',
            'age': 35
        }
        
        encrypted = self.field_encryption.encrypt_dict_fields(data, ['name', 'phone'])
        decrypted = self.field_encryption.decrypt_dict_fields(encrypted, ['name', 'phone'])
        
        assert decrypted['name'] == data['name']
        assert decrypted['phone'] == data['phone']
        assert 'name_encrypted' not in decrypted
        assert 'phone_encrypted' not in decrypted


class TestPIIAnonymizer:
    """Tests for PII detection and anonymization."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.anonymizer = PIIAnonymizer()
    
    def test_detect_phone_numbers(self):
        """Test detection of Indian phone numbers."""
        text = "My phone is 9876543210 and alternate is +919123456789"
        detections = self.anonymizer.detect_pii(text)
        
        phone_detections = [d for d in detections if d[0] == 'phone']
        assert len(phone_detections) == 2
    
    def test_detect_aadhaar(self):
        """Test detection of Aadhaar numbers."""
        text = "My Aadhaar is 1234 5678 9012"
        detections = self.anonymizer.detect_pii(text)
        
        aadhaar_detections = [d for d in detections if d[0] == 'aadhaar']
        assert len(aadhaar_detections) == 1
    
    def test_detect_pan(self):
        """Test detection of PAN card numbers."""
        text = "PAN card: ABCDE1234F"
        detections = self.anonymizer.detect_pii(text)
        
        pan_detections = [d for d in detections if d[0] == 'pan']
        assert len(pan_detections) == 1
    
    def test_detect_email(self):
        """Test detection of email addresses."""
        text = "Contact me at rajesh.kumar@example.com"
        detections = self.anonymizer.detect_pii(text)
        
        email_detections = [d for d in detections if d[0] == 'email']
        assert len(email_detections) == 1
    
    def test_anonymize_phone(self):
        """Test phone number anonymization."""
        text = "Call me at 9876543210"
        anonymized, report = self.anonymizer.anonymize_text(text)
        
        assert "9876543210" not in anonymized
        assert "PHONE_" in anonymized
        assert "10" in anonymized  # Last 2 digits preserved
        assert 'phone' in report
    
    def test_anonymize_aadhaar(self):
        """Test Aadhaar anonymization."""
        text = "Aadhaar: 1234 5678 9012"
        anonymized, report = self.anonymizer.anonymize_text(text)
        
        assert "1234 5678 9012" not in anonymized
        assert "AADHAAR_" in anonymized
        assert "9012" in anonymized  # Last 4 digits preserved
        assert 'aadhaar' in report
    
    def test_anonymize_multiple_pii(self):
        """Test anonymization of multiple PII types."""
        text = "I am Rajesh, phone 9876543210, Aadhaar 1234-5678-9012, email raj@example.com"
        anonymized, report = self.anonymizer.anonymize_text(text)
        
        assert "9876543210" not in anonymized
        assert "1234-5678-9012" not in anonymized
        assert "raj@example.com" not in anonymized
        assert len(report) >= 3
    
    def test_preserve_non_pii(self):
        """Test that non-PII text is preserved."""
        text = "I need help with PM-KISAN scheme"
        anonymized, report = self.anonymizer.anonymize_text(text)
        
        assert anonymized == text
        assert len(report) == 0


class TestConversationAnonymizer:
    """Tests for conversation anonymization."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.conv_anonymizer = ConversationAnonymizer(storage_path=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_anonymize_conversation(self):
        """Test anonymization of conversation messages."""
        messages = [
            {'role': 'user', 'content': 'My phone is 9876543210'},
            {'role': 'assistant', 'content': 'Thank you. What is your Aadhaar?'},
            {'role': 'user', 'content': 'My Aadhaar is 1234-5678-9012'}
        ]
        
        anonymized, stats = self.conv_anonymizer.anonymizer.anonymize_conversation(messages)
        
        assert len(anonymized) == 3
        assert "9876543210" not in anonymized[0]['content']
        assert "1234-5678-9012" not in anonymized[2]['content']
        assert stats['phone'] == 1
        assert stats['aadhaar'] == 1
    
    def test_process_and_store(self):
        """Test processing and storing anonymized conversation."""
        messages = [
            {'role': 'user', 'content': 'Help me with scheme, phone 9876543210'}
        ]
        
        report = self.conv_anonymizer.process_and_store('conv_123', messages)
        
        assert report['conversation_id'] == 'conv_123'
        assert report['message_count'] == 1
        assert report['pii_detected'] > 0
        assert report['stored'] is True
        
        # Verify file was created
        conv_file = Path(self.temp_dir) / 'conv_123.json'
        assert conv_file.exists()
        
        # Verify content
        with open(conv_file, 'r') as f:
            stored_data = json.load(f)
        
        assert stored_data['conversation_id'] == 'conv_123'
        assert "9876543210" not in stored_data['messages'][0]['content']


class TestTLSConfig:
    """Tests for TLS configuration."""
    
    def test_tls13_ciphers(self):
        """Test TLS 1.3 cipher suites are defined."""
        assert len(TLSConfig.TLS13_CIPHERS) > 0
        assert 'TLS_AES_256_GCM_SHA384' in TLSConfig.TLS13_CIPHERS
    
    def test_uvicorn_config(self):
        """Test Uvicorn SSL configuration generation."""
        config = TLSConfig.get_uvicorn_ssl_config(
            cert_file='cert.pem',
            key_file='key.pem'
        )
        
        assert config['ssl_certfile'] == 'cert.pem'
        assert config['ssl_keyfile'] == 'key.pem'
        assert 'ssl_ciphers' in config
    
    def test_requests_config(self):
        """Test requests SSL configuration generation."""
        config = TLSConfig.get_requests_ssl_config(verify=True)
        
        assert config['verify'] is True
    
    def test_requests_config_with_cert(self):
        """Test requests SSL configuration with client certificate."""
        config = TLSConfig.get_requests_ssl_config(
            verify=True,
            cert=('cert.pem', 'key.pem')
        )
        
        assert config['cert'] == ('cert.pem', 'key.pem')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
