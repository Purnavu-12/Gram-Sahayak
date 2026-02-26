"""
PII detection and anonymization system for conversations.
Detects and anonymizes personally identifiable information in text.
"""

import re
import hashlib
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class PIIPattern:
    """Defines patterns for detecting PII."""
    
    # Indian phone numbers (10 digits, optionally with +91 or 0)
    PHONE = r'\+?91[-\s]?\d{10}|\b0?\d{10}\b'
    
    # Aadhaar numbers (12 digits, optionally with spaces/dashes)
    AADHAAR = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    
    # PAN card (5 letters, 4 digits, 1 letter)
    PAN = r'\b[A-Z]{5}\d{4}[A-Z]\b'
    
    # Email addresses
    EMAIL = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Bank account numbers (9-18 digits)
    BANK_ACCOUNT = r'\b\d{9,18}\b'
    
    # IFSC codes (4 letters, 7 alphanumeric)
    IFSC = r'\b[A-Z]{4}0[A-Z0-9]{6}\b'
    
    # Indian addresses (simplified pattern)
    ADDRESS_KEYWORDS = [
        'village', 'block', 'district', 'state', 'pincode', 'pin',
        'house', 'street', 'road', 'lane', 'colony', 'nagar'
    ]
    
    # Names (common Indian name patterns - simplified)
    # This is a basic pattern; real implementation would use NER
    NAME_TITLES = ['mr', 'mrs', 'ms', 'dr', 'shri', 'smt', 'kumari']


class PIIAnonymizer:
    """
    Anonymizes personally identifiable information in text.
    Uses pattern matching and hashing for consistent anonymization.
    """
    
    def __init__(self, salt: Optional[str] = None):
        """
        Initialize PII anonymizer.
        
        Args:
            salt: Salt for hashing (for consistent anonymization)
        """
        self.salt = salt or "gram_sahayak_pii_salt"
        self.anonymization_map: Dict[str, str] = {}
    
    def _hash_value(self, value: str) -> str:
        """
        Create a consistent hash for a PII value.
        
        Args:
            value: PII value to hash
            
        Returns:
            Hashed value
        """
        salted = f"{self.salt}:{value}"
        return hashlib.sha256(salted.encode()).hexdigest()[:16]
    
    def _anonymize_phone(self, phone: str) -> str:
        """Anonymize phone number."""
        # Keep last 2 digits for reference
        clean_phone = re.sub(r'[^\d]', '', phone)
        if len(clean_phone) >= 10:
            last_two = clean_phone[-2:]
            return f"PHONE_***{last_two}"
        return "PHONE_REDACTED"
    
    def _anonymize_aadhaar(self, aadhaar: str) -> str:
        """Anonymize Aadhaar number."""
        # Keep last 4 digits as per standard practice
        clean_aadhaar = re.sub(r'[^\d]', '', aadhaar)
        if len(clean_aadhaar) == 12:
            last_four = clean_aadhaar[-4:]
            return f"AADHAAR_XXXX-XXXX-{last_four}"
        return "AADHAAR_REDACTED"
    
    def _anonymize_pan(self, pan: str) -> str:
        """Anonymize PAN card number."""
        # Keep first and last character
        if len(pan) == 10:
            return f"PAN_{pan[0]}XXX{pan[-1]}"
        return "PAN_REDACTED"
    
    def _anonymize_email(self, email: str) -> str:
        """Anonymize email address."""
        parts = email.split('@')
        if len(parts) == 2:
            username = parts[0]
            domain = parts[1]
            if len(username) > 2:
                return f"{username[:2]}***@{domain}"
            return f"***@{domain}"
        return "EMAIL_REDACTED"
    
    def _anonymize_bank_account(self, account: str) -> str:
        """Anonymize bank account number."""
        if len(account) >= 4:
            last_four = account[-4:]
            return f"ACCOUNT_***{last_four}"
        return "ACCOUNT_REDACTED"
    
    def _anonymize_ifsc(self, ifsc: str) -> str:
        """Anonymize IFSC code."""
        # Keep bank code (first 4 letters)
        if len(ifsc) == 11:
            return f"{ifsc[:4]}XXXXXXX"
        return "IFSC_REDACTED"
    
    def detect_pii(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        Detect PII in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of (pii_type, value, start_pos, end_pos) tuples
        """
        detections = []
        
        # Phone numbers
        for match in re.finditer(PIIPattern.PHONE, text):
            detections.append(('phone', match.group(), match.start(), match.end()))
        
        # Aadhaar numbers
        for match in re.finditer(PIIPattern.AADHAAR, text):
            detections.append(('aadhaar', match.group(), match.start(), match.end()))
        
        # PAN cards
        for match in re.finditer(PIIPattern.PAN, text):
            detections.append(('pan', match.group(), match.start(), match.end()))
        
        # Email addresses
        for match in re.finditer(PIIPattern.EMAIL, text):
            detections.append(('email', match.group(), match.start(), match.end()))
        
        # IFSC codes
        for match in re.finditer(PIIPattern.IFSC, text):
            detections.append(('ifsc', match.group(), match.start(), match.end()))
        
        # Bank accounts (be careful not to match other numbers)
        # Only match if preceded by keywords like "account"
        account_pattern = r'(?:account|a/c)[\s:]+(\d{9,18})'
        for match in re.finditer(account_pattern, text, re.IGNORECASE):
            detections.append(('bank_account', match.group(1), match.start(1), match.end(1)))
        
        return detections
    
    def anonymize_text(self, text: str, preserve_structure: bool = True) -> Tuple[str, Dict[str, List[str]]]:
        """
        Anonymize PII in text.
        
        Args:
            text: Text to anonymize
            preserve_structure: If True, maintains text structure with placeholders
            
        Returns:
            Tuple of (anonymized_text, detection_report)
        """
        detections = self.detect_pii(text)
        
        # Sort by position (reverse order for replacement)
        detections.sort(key=lambda x: x[2], reverse=True)
        
        anonymized = text
        report: Dict[str, List[str]] = {}
        
        for pii_type, value, start, end in detections:
            # Choose anonymization method
            if pii_type == 'phone':
                replacement = self._anonymize_phone(value)
            elif pii_type == 'aadhaar':
                replacement = self._anonymize_aadhaar(value)
            elif pii_type == 'pan':
                replacement = self._anonymize_pan(value)
            elif pii_type == 'email':
                replacement = self._anonymize_email(value)
            elif pii_type == 'bank_account':
                replacement = self._anonymize_bank_account(value)
            elif pii_type == 'ifsc':
                replacement = self._anonymize_ifsc(value)
            else:
                replacement = f"{pii_type.upper()}_REDACTED"
            
            # Replace in text
            anonymized = anonymized[:start] + replacement + anonymized[end:]
            
            # Add to report
            if pii_type not in report:
                report[pii_type] = []
            report[pii_type].append(value)
        
        return anonymized, report
    
    def anonymize_conversation(self, messages: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
        """
        Anonymize an entire conversation.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Returns:
            Tuple of (anonymized_messages, pii_statistics)
        """
        anonymized_messages = []
        total_pii_count: Dict[str, int] = {}
        
        for message in messages:
            content = message.get('content', '')
            anonymized_content, report = self.anonymize_text(content)
            
            anonymized_message = message.copy()
            anonymized_message['content'] = anonymized_content
            anonymized_message['pii_detected'] = len(report) > 0
            anonymized_message['anonymized_at'] = datetime.utcnow().isoformat()
            
            anonymized_messages.append(anonymized_message)
            
            # Update statistics
            for pii_type, values in report.items():
                total_pii_count[pii_type] = total_pii_count.get(pii_type, 0) + len(values)
        
        return anonymized_messages, total_pii_count


class ConversationAnonymizer:
    """
    High-level service for anonymizing conversations with storage.
    """
    
    def __init__(self, storage_path: str = "./data/conversations"):
        """
        Initialize conversation anonymizer.
        
        Args:
            storage_path: Directory for storing anonymized conversations
        """
        from pathlib import Path
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.anonymizer = PIIAnonymizer()
    
    def process_and_store(self, conversation_id: str, messages: List[Dict[str, str]]) -> Dict[str, any]:
        """
        Process conversation, anonymize PII, and store.
        
        Args:
            conversation_id: Unique conversation identifier
            messages: List of conversation messages
            
        Returns:
            Processing report with statistics
        """
        import json
        
        # Anonymize conversation
        anonymized_messages, pii_stats = self.anonymizer.anonymize_conversation(messages)
        
        # Store anonymized conversation
        conversation_file = self.storage_path / f"{conversation_id}.json"
        with open(conversation_file, 'w') as f:
            json.dump({
                'conversation_id': conversation_id,
                'messages': anonymized_messages,
                'pii_statistics': pii_stats,
                'processed_at': datetime.utcnow().isoformat()
            }, f, indent=2)
        
        return {
            'conversation_id': conversation_id,
            'message_count': len(messages),
            'pii_detected': sum(pii_stats.values()),
            'pii_types': list(pii_stats.keys()),
            'stored': True
        }
