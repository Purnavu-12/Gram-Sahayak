"""
TLS 1.3 configuration for secure communications.
Provides secure transmission protocols for all services.
"""

import ssl
from typing import Optional, Dict
from pathlib import Path


class TLSConfig:
    """
    TLS 1.3 configuration for secure communications.
    """
    
    # Recommended cipher suites for TLS 1.3
    TLS13_CIPHERS = [
        'TLS_AES_256_GCM_SHA384',
        'TLS_CHACHA20_POLY1305_SHA256',
        'TLS_AES_128_GCM_SHA256',
    ]
    
    # Minimum TLS version
    MIN_TLS_VERSION = ssl.TLSVersion.TLSv1_3
    
    @classmethod
    def create_ssl_context(
        cls,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_file: Optional[str] = None,
        verify_mode: ssl.VerifyMode = ssl.CERT_REQUIRED
    ) -> ssl.SSLContext:
        """
        Create an SSL context with TLS 1.3 configuration.
        
        Args:
            cert_file: Path to certificate file
            key_file: Path to private key file
            ca_file: Path to CA certificate file
            verify_mode: Certificate verification mode
            
        Returns:
            Configured SSL context
        """
        # Create context with TLS 1.3
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER if cert_file else ssl.PROTOCOL_TLS_CLIENT)
        
        # Set minimum TLS version to 1.3
        context.minimum_version = cls.MIN_TLS_VERSION
        
        # Set cipher suites
        context.set_ciphers(':'.join(cls.TLS13_CIPHERS))
        
        # Load certificates if provided
        if cert_file and key_file:
            context.load_cert_chain(cert_file, key_file)
        
        # Load CA certificates if provided
        if ca_file:
            context.load_verify_locations(ca_file)
        
        # Set verification mode
        context.verify_mode = verify_mode
        
        # Additional security settings
        context.check_hostname = True if verify_mode == ssl.CERT_REQUIRED else False
        context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_2
        
        return context
    
    @classmethod
    def get_uvicorn_ssl_config(
        cls,
        cert_file: str,
        key_file: str,
        ca_file: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Get SSL configuration for Uvicorn server.
        
        Args:
            cert_file: Path to certificate file
            key_file: Path to private key file
            ca_file: Path to CA certificate file
            
        Returns:
            Dictionary with Uvicorn SSL configuration
        """
        config = {
            'ssl_certfile': cert_file,
            'ssl_keyfile': key_file,
            'ssl_version': ssl.PROTOCOL_TLS_SERVER,
            'ssl_cert_reqs': ssl.CERT_REQUIRED,
            'ssl_ciphers': ':'.join(cls.TLS13_CIPHERS),
        }
        
        if ca_file:
            config['ssl_ca_certs'] = ca_file
        
        return config
    
    @classmethod
    def get_requests_ssl_config(
        cls,
        verify: bool = True,
        cert: Optional[tuple] = None,
        ca_bundle: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Get SSL configuration for requests library.
        
        Args:
            verify: Whether to verify SSL certificates
            cert: Tuple of (cert_file, key_file) for client certificates
            ca_bundle: Path to CA bundle file
            
        Returns:
            Dictionary with requests SSL configuration
        """
        config = {
            'verify': ca_bundle if ca_bundle else verify,
        }
        
        if cert:
            config['cert'] = cert
        
        return config


class SecureHTTPClient:
    """
    HTTP client with enforced TLS 1.3 for secure communications.
    """
    
    def __init__(
        self,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_file: Optional[str] = None
    ):
        """
        Initialize secure HTTP client.
        
        Args:
            cert_file: Path to client certificate file
            key_file: Path to client private key file
            ca_file: Path to CA certificate file
        """
        self.cert_file = cert_file
        self.key_file = key_file
        self.ca_file = ca_file
        self.ssl_context = TLSConfig.create_ssl_context(
            cert_file=cert_file,
            key_file=key_file,
            ca_file=ca_file
        )
    
    def get_session_config(self) -> Dict[str, any]:
        """
        Get configuration for requests session.
        
        Returns:
            Dictionary with session configuration
        """
        cert = (self.cert_file, self.key_file) if self.cert_file and self.key_file else None
        return TLSConfig.get_requests_ssl_config(
            verify=self.ca_file if self.ca_file else True,
            cert=cert
        )


def generate_self_signed_cert(
    cert_file: str = "./certs/cert.pem",
    key_file: str = "./certs/key.pem",
    days_valid: int = 365
) -> None:
    """
    Generate self-signed certificate for development/testing.
    
    Args:
        cert_file: Path to save certificate
        key_file: Path to save private key
        days_valid: Number of days certificate is valid
    """
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    from datetime import datetime, timedelta
    
    # Create directory if it doesn't exist
    Path(cert_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Create certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Karnataka"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Bangalore"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Gram Sahayak"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=days_valid)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.DNSName("*.localhost"),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256())
    
    # Write private key
    with open(key_file, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Write certificate
    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    print(f"Generated self-signed certificate: {cert_file}")
    print(f"Generated private key: {key_file}")
