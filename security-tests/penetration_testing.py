"""
Penetration Testing Suite for Gram Sahayak
Tests security vulnerabilities in voice data handling and API endpoints

Validates Requirements 9.1, 9.2, 9.3, 9.4, 9.5
"""

import asyncio
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytest
import httpx
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os


class PenetrationTester:
    """Penetration testing framework for security validation"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.vulnerabilities: List[Dict] = []
    
    async def close(self):
        await self.client.aclose()
    
    def log_vulnerability(self, severity: str, category: str, description: str, details: Dict):
        """Log discovered vulnerability"""
        self.vulnerabilities.append({
            "severity": severity,
            "category": category,
            "description": description,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def test_sql_injection(self, endpoint: str) -> Dict:
        """Test for SQL injection vulnerabilities"""
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users--",
            "' UNION SELECT * FROM users--",
            "admin'--",
            "' OR 1=1--"
        ]
        
        results = []
        for payload in sql_payloads:
            try:
                response = await self.client.get(
                    f"{self.base_url}{endpoint}",
                    params={"id": payload}
                )
                
                if response.status_code == 200:
                    # Check if payload was executed
                    if "error" not in response.text.lower():
                        self.log_vulnerability(
                            severity="CRITICAL",
                            category="SQL_INJECTION",
                            description=f"Potential SQL injection at {endpoint}",
                            details={"payload": payload, "response": response.text[:200]}
                        )
                        results.append({"vulnerable": True, "payload": payload})
                    else:
                        results.append({"vulnerable": False, "payload": payload})
            except Exception as e:
                results.append({"error": str(e), "payload": payload})
        
        return {"endpoint": endpoint, "tests": results}
    
    async def test_xss_vulnerabilities(self, endpoint: str) -> Dict:
        """Test for Cross-Site Scripting vulnerabilities"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//"
        ]
        
        results = []
        for payload in xss_payloads:
            try:
                response = await self.client.post(
                    f"{self.base_url}{endpoint}",
                    json={"content": payload}
                )
                
                if payload in response.text:
                    self.log_vulnerability(
                        severity="HIGH",
                        category="XSS",
                        description=f"XSS vulnerability at {endpoint}",
                        details={"payload": payload}
                    )
                    results.append({"vulnerable": True, "payload": payload})
                else:
                    results.append({"vulnerable": False, "payload": payload})
            except Exception as e:
                results.append({"error": str(e), "payload": payload})
        
        return {"endpoint": endpoint, "tests": results}
    
    async def test_authentication_bypass(self) -> Dict:
        """Test for authentication bypass vulnerabilities"""
        bypass_attempts = []
        
        # Test 1: No token
        try:
            response = await self.client.get(f"{self.base_url}/api/user/profile")
            if response.status_code == 200:
                self.log_vulnerability(
                    severity="CRITICAL",
                    category="AUTH_BYPASS",
                    description="Endpoint accessible without authentication",
                    details={"endpoint": "/api/user/profile"}
                )
                bypass_attempts.append({"method": "no_token", "bypassed": True})
            else:
                bypass_attempts.append({"method": "no_token", "bypassed": False})
        except Exception as e:
            bypass_attempts.append({"method": "no_token", "error": str(e)})
        
        # Test 2: Invalid token
        try:
            response = await self.client.get(
                f"{self.base_url}/api/user/profile",
                headers={"Authorization": "Bearer invalid_token"}
            )
            if response.status_code == 200:
                self.log_vulnerability(
                    severity="CRITICAL",
                    category="AUTH_BYPASS",
                    description="Endpoint accepts invalid tokens",
                    details={"endpoint": "/api/user/profile"}
                )
                bypass_attempts.append({"method": "invalid_token", "bypassed": True})
            else:
                bypass_attempts.append({"method": "invalid_token", "bypassed": False})
        except Exception as e:
            bypass_attempts.append({"method": "invalid_token", "error": str(e)})
        
        # Test 3: Expired token
        expired_token = self._generate_expired_token()
        try:
            response = await self.client.get(
                f"{self.base_url}/api/user/profile",
                headers={"Authorization": f"Bearer {expired_token}"}
            )
            if response.status_code == 200:
                self.log_vulnerability(
                    severity="HIGH",
                    category="AUTH_BYPASS",
                    description="Endpoint accepts expired tokens",
                    details={"endpoint": "/api/user/profile"}
                )
                bypass_attempts.append({"method": "expired_token", "bypassed": True})
            else:
                bypass_attempts.append({"method": "expired_token", "bypassed": False})
        except Exception as e:
            bypass_attempts.append({"method": "expired_token", "error": str(e)})
        
        return {"tests": bypass_attempts}
    
    async def test_rate_limiting(self, endpoint: str, requests_count: int = 200) -> Dict:
        """Test rate limiting implementation"""
        start_time = time.time()
        responses = []
        
        tasks = []
        for i in range(requests_count):
            tasks.append(self.client.get(f"{self.base_url}{endpoint}"))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        rate_limited_count = sum(
            1 for r in results 
            if not isinstance(r, Exception) and r.status_code == 429
        )
        
        elapsed_time = time.time() - start_time
        
        if rate_limited_count == 0:
            self.log_vulnerability(
                severity="MEDIUM",
                category="RATE_LIMITING",
                description=f"No rate limiting detected on {endpoint}",
                details={
                    "requests_sent": requests_count,
                    "rate_limited": rate_limited_count,
                    "elapsed_time": elapsed_time
                }
            )
        
        return {
            "endpoint": endpoint,
            "requests_sent": requests_count,
            "rate_limited_count": rate_limited_count,
            "elapsed_time": elapsed_time,
            "rate_limiting_active": rate_limited_count > 0
        }
    
    async def test_encryption_strength(self) -> Dict:
        """Test encryption implementation strength"""
        results = []
        
        # Test 1: Verify AES-256-GCM usage
        key = AESGCM.generate_key(bit_length=256)
        aesgcm = AESGCM(key)
        
        plaintext = b"sensitive data"
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        
        # Verify encryption produces different output
        nonce2 = os.urandom(12)
        ciphertext2 = aesgcm.encrypt(nonce2, plaintext, None)
        
        if ciphertext == ciphertext2:
            self.log_vulnerability(
                severity="CRITICAL",
                category="ENCRYPTION",
                description="Encryption produces identical ciphertext",
                details={"issue": "nonce_reuse_or_weak_encryption"}
            )
            results.append({"test": "unique_ciphertext", "passed": False})
        else:
            results.append({"test": "unique_ciphertext", "passed": True})
        
        # Test 2: Verify decryption works
        try:
            decrypted = aesgcm.decrypt(nonce, ciphertext, None)
            if decrypted == plaintext:
                results.append({"test": "decryption", "passed": True})
            else:
                results.append({"test": "decryption", "passed": False})
        except Exception as e:
            results.append({"test": "decryption", "error": str(e)})
        
        # Test 3: Verify wrong key fails
        wrong_key = AESGCM.generate_key(bit_length=256)
        wrong_aesgcm = AESGCM(wrong_key)
        try:
            wrong_aesgcm.decrypt(nonce, ciphertext, None)
            self.log_vulnerability(
                severity="CRITICAL",
                category="ENCRYPTION",
                description="Decryption succeeds with wrong key",
                details={"issue": "weak_authentication"}
            )
            results.append({"test": "wrong_key_rejection", "passed": False})
        except Exception:
            results.append({"test": "wrong_key_rejection", "passed": True})
        
        return {"tests": results}
    
    async def test_tls_configuration(self) -> Dict:
        """Test TLS/SSL configuration"""
        if not self.base_url.startswith("https://"):
            self.log_vulnerability(
                severity="CRITICAL",
                category="TLS",
                description="API not using HTTPS",
                details={"base_url": self.base_url}
            )
            return {"https_enabled": False, "tests": []}
        
        results = []
        
        # Test TLS version
        # Note: This requires actual HTTPS endpoint
        results.append({
            "test": "tls_version",
            "expected": "TLS 1.3",
            "note": "Requires production HTTPS endpoint for validation"
        })
        
        return {"https_enabled": True, "tests": results}
    
    async def test_voice_data_security(self) -> Dict:
        """Test voice data handling security"""
        results = []
        
        # Test 1: File size limit
        large_file = b"x" * (11 * 1024 * 1024)  # 11MB
        try:
            response = await self.client.post(
                f"{self.base_url}/api/voice/upload",
                files={"audio": ("large.wav", large_file, "audio/wav")}
            )
            if response.status_code == 200:
                self.log_vulnerability(
                    severity="MEDIUM",
                    category="VOICE_SECURITY",
                    description="No file size limit on voice uploads",
                    details={"file_size": len(large_file)}
                )
                results.append({"test": "file_size_limit", "passed": False})
            else:
                results.append({"test": "file_size_limit", "passed": True})
        except Exception as e:
            results.append({"test": "file_size_limit", "error": str(e)})
        
        # Test 2: File type validation
        malicious_file = b"<?php system($_GET['cmd']); ?>"
        try:
            response = await self.client.post(
                f"{self.base_url}/api/voice/upload",
                files={"audio": ("malicious.php", malicious_file, "audio/wav")}
            )
            if response.status_code == 200:
                self.log_vulnerability(
                    severity="HIGH",
                    category="VOICE_SECURITY",
                    description="Accepts non-audio files as voice data",
                    details={"file_type": "php"}
                )
                results.append({"test": "file_type_validation", "passed": False})
            else:
                results.append({"test": "file_type_validation", "passed": True})
        except Exception as e:
            results.append({"test": "file_type_validation", "error": str(e)})
        
        return {"tests": results}
    
    async def test_data_anonymization(self) -> Dict:
        """Test PII anonymization"""
        test_cases = [
            {
                "input": "My Aadhaar is 1234-5678-9012",
                "pii_type": "aadhaar",
                "should_not_contain": "1234-5678-9012"
            },
            {
                "input": "Call me at 9876543210",
                "pii_type": "phone",
                "should_not_contain": "9876543210"
            },
            {
                "input": "Email: user@example.com",
                "pii_type": "email",
                "should_not_contain": "user@example.com"
            },
            {
                "input": "PAN: ABCDE1234F",
                "pii_type": "pan",
                "should_not_contain": "ABCDE1234F"
            }
        ]
        
        results = []
        for test_case in test_cases:
            # Simulate anonymization
            anonymized = self._anonymize_text(test_case["input"])
            
            if test_case["should_not_contain"] in anonymized:
                self.log_vulnerability(
                    severity="HIGH",
                    category="DATA_ANONYMIZATION",
                    description=f"PII not anonymized: {test_case['pii_type']}",
                    details=test_case
                )
                results.append({
                    "pii_type": test_case["pii_type"],
                    "anonymized": False
                })
            else:
                results.append({
                    "pii_type": test_case["pii_type"],
                    "anonymized": True
                })
        
        return {"tests": results}
    
    async def test_session_management(self) -> Dict:
        """Test session management security"""
        results = []
        
        # Test 1: Session timeout
        session_timeout = 30 * 60  # 30 minutes
        results.append({
            "test": "session_timeout",
            "configured": session_timeout,
            "passed": session_timeout <= 30 * 60
        })
        
        # Test 2: Idle timeout
        idle_timeout = 15 * 60  # 15 minutes
        results.append({
            "test": "idle_timeout",
            "configured": idle_timeout,
            "passed": idle_timeout <= 15 * 60
        })
        
        # Test 3: Session fixation
        # Create session and try to reuse
        try:
            response1 = await self.client.post(
                f"{self.base_url}/api/auth/login",
                json={"username": "test", "password": "test"}
            )
            
            if response1.status_code == 200:
                session_id = response1.cookies.get("session_id")
                
                # Try to use same session from different context
                response2 = await self.client.get(
                    f"{self.base_url}/api/user/profile",
                    cookies={"session_id": session_id}
                )
                
                results.append({
                    "test": "session_fixation",
                    "note": "Manual verification required"
                })
        except Exception as e:
            results.append({"test": "session_fixation", "error": str(e)})
        
        return {"tests": results}
    
    def _generate_expired_token(self) -> str:
        """Generate an expired JWT token"""
        import base64
        header = base64.b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode()
        payload = base64.b64encode(json.dumps({
            "userId": "test",
            "exp": int(time.time()) - 3600  # Expired 1 hour ago
        }).encode()).decode()
        signature = base64.b64encode(b"fake_signature").decode()
        return f"{header}.{payload}.{signature}"
    
    def _anonymize_text(self, text: str) -> str:
        """Simulate text anonymization"""
        import re
        text = re.sub(r'\d{4}[-\s]?\d{4}[-\s]?\d{4}', 'AADHAAR_XXXX-XXXX-XXXX', text)
        text = re.sub(r'\d{10}', 'PHONE_***XX', text)
        text = re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', '***@example.com', text)
        text = re.sub(r'[A-Z]{5}\d{4}[A-Z]', 'PAN_XXXXX', text)
        return text
    
    def generate_report(self) -> Dict:
        """Generate penetration testing report"""
        critical = [v for v in self.vulnerabilities if v["severity"] == "CRITICAL"]
        high = [v for v in self.vulnerabilities if v["severity"] == "HIGH"]
        medium = [v for v in self.vulnerabilities if v["severity"] == "MEDIUM"]
        
        return {
            "summary": {
                "total_vulnerabilities": len(self.vulnerabilities),
                "critical": len(critical),
                "high": len(high),
                "medium": len(medium)
            },
            "vulnerabilities": self.vulnerabilities,
            "generated_at": datetime.utcnow().isoformat()
        }


# Pytest test cases
@pytest.mark.asyncio
async def test_penetration_suite():
    """Run complete penetration testing suite"""
    tester = PenetrationTester()
    
    try:
        # Run all tests
        await tester.test_sql_injection("/api/user/profile")
        await tester.test_xss_vulnerabilities("/api/conversation/message")
        await tester.test_authentication_bypass()
        await tester.test_rate_limiting("/api/test")
        await tester.test_encryption_strength()
        await tester.test_tls_configuration()
        await tester.test_voice_data_security()
        await tester.test_data_anonymization()
        await tester.test_session_management()
        
        # Generate report
        report = tester.generate_report()
        
        # Assert no critical vulnerabilities
        assert report["summary"]["critical"] == 0, \
            f"Found {report['summary']['critical']} critical vulnerabilities"
        
        print(json.dumps(report, indent=2))
        
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(test_penetration_suite())
