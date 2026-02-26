"""
OAuth 2.0 Client Implementation for Government Portals
Implements authorization code flow, token refresh, and PKCE for enhanced security.

Validates: Requirement 9.4 (token-based authentication for government APIs)
"""

import secrets
import hashlib
import base64
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple
from urllib.parse import urlencode, parse_qs, urlparse
import httpx


class OAuth2Client:
    """
    OAuth 2.0 client with PKCE support for secure government portal authentication.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        authorization_endpoint: str,
        token_endpoint: str,
        redirect_uri: str,
        scope: Optional[str] = None
    ):
        """
        Initialize OAuth 2.0 client.
        
        Args:
            client_id: OAuth client identifier
            client_secret: OAuth client secret
            authorization_endpoint: Authorization URL
            token_endpoint: Token exchange URL
            redirect_uri: Callback URL for authorization
            scope: Requested OAuth scopes
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorization_endpoint = authorization_endpoint
        self.token_endpoint = token_endpoint
        self.redirect_uri = redirect_uri
        self.scope = scope or "read write"
        
        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Token storage
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
    
    def generate_authorization_url(self, state: Optional[str] = None) -> Tuple[str, str, str]:
        """
        Generate authorization URL with PKCE.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Tuple of (authorization_url, state, code_verifier)
        """
        # Generate state if not provided
        if not state:
            state = secrets.token_urlsafe(32)
        
        # Generate PKCE code verifier and challenge
        code_verifier = self._generate_code_verifier()
        code_challenge = self._generate_code_challenge(code_verifier)
        
        # Build authorization URL
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.scope,
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        auth_url = f"{self.authorization_endpoint}?{urlencode(params)}"
        
        return auth_url, state, code_verifier
    
    def _generate_code_verifier(self) -> str:
        """Generate PKCE code verifier"""
        # Generate 43-128 character random string
        return secrets.token_urlsafe(64)
    
    def _generate_code_challenge(self, code_verifier: str) -> str:
        """Generate PKCE code challenge from verifier"""
        # SHA256 hash of the verifier
        digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        # Base64 URL-safe encoding without padding
        challenge = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
        return challenge
    
    async def exchange_code_for_token(
        self,
        authorization_code: str,
        code_verifier: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            authorization_code: Authorization code from callback
            code_verifier: PKCE code verifier
            
        Returns:
            Token response with access_token, refresh_token, etc.
        """
        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code_verifier': code_verifier
        }
        
        try:
            response = await self.http_client.post(
                self.token_endpoint,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            # Store tokens
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            
            # Calculate expiration
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return {
                'success': True,
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'token_type': token_data.get('token_type', 'Bearer'),
                'expires_in': expires_in,
                'expires_at': self.token_expires_at.isoformat(),
                'scope': token_data.get('scope', self.scope)
            }
        except httpx.HTTPStatusError as e:
            return {
                'success': False,
                'error': 'token_exchange_failed',
                'error_description': str(e),
                'status_code': e.response.status_code
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'token_exchange_error',
                'error_description': str(e)
            }
    
    async def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Returns:
            New token response
        """
        if not self.refresh_token:
            return {
                'success': False,
                'error': 'no_refresh_token',
                'error_description': 'No refresh token available'
            }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = await self.http_client.post(
                self.token_endpoint,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            # Update tokens
            self.access_token = token_data.get('access_token')
            if 'refresh_token' in token_data:
                self.refresh_token = token_data['refresh_token']
            
            # Calculate expiration
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return {
                'success': True,
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'token_type': token_data.get('token_type', 'Bearer'),
                'expires_in': expires_in,
                'expires_at': self.token_expires_at.isoformat()
            }
        except httpx.HTTPStatusError as e:
            return {
                'success': False,
                'error': 'token_refresh_failed',
                'error_description': str(e),
                'status_code': e.response.status_code
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'token_refresh_error',
                'error_description': str(e)
            }
    
    def is_token_expired(self) -> bool:
        """
        Check if access token is expired.
        
        Returns:
            True if token is expired or will expire in next 60 seconds
        """
        if not self.token_expires_at:
            return True
        
        # Consider token expired if it expires in next 60 seconds
        buffer = timedelta(seconds=60)
        return datetime.utcnow() + buffer >= self.token_expires_at
    
    async def get_valid_token(self) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary.
        
        Returns:
            Valid access token or None if unable to obtain
        """
        # Check if current token is valid
        if self.access_token and not self.is_token_expired():
            return self.access_token
        
        # Try to refresh token
        if self.refresh_token:
            result = await self.refresh_access_token()
            if result['success']:
                return self.access_token
        
        return None
    
    async def revoke_token(self, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Revoke an access or refresh token.
        
        Args:
            token: Token to revoke (defaults to current access token)
            
        Returns:
            Revocation result
        """
        token_to_revoke = token or self.access_token
        
        if not token_to_revoke:
            return {
                'success': False,
                'error': 'no_token',
                'error_description': 'No token to revoke'
            }
        
        # Note: Revocation endpoint varies by provider
        # This is a generic implementation
        revoke_endpoint = self.token_endpoint.replace('/token', '/revoke')
        
        data = {
            'token': token_to_revoke,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = await self.http_client.post(
                revoke_endpoint,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            # Clear stored tokens
            if token_to_revoke == self.access_token:
                self.access_token = None
                self.token_expires_at = None
            if token_to_revoke == self.refresh_token:
                self.refresh_token = None
            
            return {
                'success': True,
                'message': 'Token revoked successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'revocation_failed',
                'error_description': str(e)
            }
    
    async def make_authenticated_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make an authenticated HTTP request with automatic token refresh.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional arguments for httpx request
            
        Returns:
            HTTP response
        """
        # Get valid token
        token = await self.get_valid_token()
        
        if not token:
            raise ValueError("Unable to obtain valid access token")
        
        # Add authorization header
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {token}'
        kwargs['headers'] = headers
        
        # Make request
        response = await self.http_client.request(method, url, **kwargs)
        
        return response
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


class OAuth2TokenManager:
    """
    Manages multiple OAuth 2.0 clients for different portals.
    """
    
    def __init__(self):
        """Initialize token manager"""
        self.clients: Dict[str, OAuth2Client] = {}
    
    def register_client(
        self,
        portal_id: str,
        client_config: Dict[str, str]
    ) -> OAuth2Client:
        """
        Register an OAuth 2.0 client for a portal.
        
        Args:
            portal_id: Portal identifier
            client_config: OAuth client configuration
            
        Returns:
            OAuth2Client instance
        """
        client = OAuth2Client(
            client_id=client_config['client_id'],
            client_secret=client_config['client_secret'],
            authorization_endpoint=client_config['authorization_endpoint'],
            token_endpoint=client_config['token_endpoint'],
            redirect_uri=client_config['redirect_uri'],
            scope=client_config.get('scope')
        )
        
        self.clients[portal_id] = client
        return client
    
    def get_client(self, portal_id: str) -> Optional[OAuth2Client]:
        """
        Get OAuth client for a portal.
        
        Args:
            portal_id: Portal identifier
            
        Returns:
            OAuth2Client instance or None
        """
        return self.clients.get(portal_id)
    
    async def close_all(self):
        """Close all OAuth clients"""
        for client in self.clients.values():
            await client.close()
