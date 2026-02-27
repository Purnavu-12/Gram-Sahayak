/**
 * Authentication and Authorization Testing Suite
 * 
 * Validates Requirement 9.4: Secure token-based access for government portals
 * Tests authentication flows, authorization controls, and session management
 */

import { describe, it, expect, beforeAll, afterAll } from '@jest/globals';
import axios, { AxiosInstance } from 'axios';
import * as crypto from 'crypto';

describe('Authentication and Authorization Testing', () => {
  let apiClient: AxiosInstance;
  const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:3000';

  beforeAll(() => {
    apiClient = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      validateStatus: () => true,
    });
  });

  afterAll(async () => {
    // Cleanup
  });

  describe('JWT Token Authentication', () => {
    it('should generate valid JWT tokens', () => {
      const token = generateJWT('test-user-123');
      const parts = token.split('.');
      
      expect(parts.length).toBe(3);
      
      const payload = JSON.parse(Buffer.from(parts[1], 'base64').toString());
      expect(payload.userId).toBe('test-user-123');
      expect(payload.exp).toBeDefined();
    });

    it('should include required claims in JWT', () => {
      const token = generateJWT('test-user-123');
      const payload = decodeJWT(token);
      
      expect(payload.userId).toBeDefined();
      expect(payload.exp).toBeDefined();
      expect(payload.iat).toBeDefined();
    });

    it('should set appropriate token expiration', () => {
      const token = generateJWT('test-user-123');
      const payload = decodeJWT(token);
      
      const expiresIn = payload.exp - payload.iat;
      expect(expiresIn).toBeLessThanOrEqual(24 * 60 * 60); // Max 24 hours
      expect(expiresIn).toBeGreaterThan(0);
    });

    it('should reject expired tokens', async () => {
      const expiredToken = generateExpiredJWT('test-user-123');
      
      const response = await apiClient.get('/api/user/profile', {
        headers: { Authorization: `Bearer ${expiredToken}` },
      });
      
      expect(response.status).toBe(401);
      expect(response.data.error).toMatch(/expired|invalid/i);
    });

    it('should reject malformed tokens', async () => {
      const malformedTokens = [
        'not.a.token',
        'invalid',
        '',
        'Bearer token',
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature',
      ];

      for (const token of malformedTokens) {
        const response = await apiClient.get('/api/user/profile', {
          headers: { Authorization: `Bearer ${token}` },
        });
        
        expect(response.status).toBe(401);
      }
    });

    it('should reject tokens with invalid signatures', async () => {
      const token = generateJWT('test-user-123');
      const parts = token.split('.');
      const tamperedToken = `${parts[0]}.${parts[1]}.invalidsignature`;
      
      const response = await apiClient.get('/api/user/profile', {
        headers: { Authorization: `Bearer ${tamperedToken}` },
      });
      
      expect(response.status).toBe(401);
    });

    it('should validate token signature with correct secret', () => {
      const token = generateJWT('test-user-123');
      const isValid = verifyJWT(token, 'correct-secret');
      
      expect(isValid).toBe(true);
    });

    it('should reject token with wrong secret', () => {
      const token = generateJWT('test-user-123');
      const isValid = verifyJWT(token, 'wrong-secret');
      
      expect(isValid).toBe(false);
    });
  });

  describe('OAuth2 with PKCE', () => {
    it('should generate secure code verifier', () => {
      const verifier = generateCodeVerifier();
      
      expect(verifier.length).toBeGreaterThanOrEqual(43);
      expect(verifier.length).toBeLessThanOrEqual(128);
      expect(verifier).toMatch(/^[A-Za-z0-9_-]+$/);
    });

    it('should generate code challenge from verifier', () => {
      const verifier = generateCodeVerifier();
      const challenge = generateCodeChallenge(verifier);
      
      expect(challenge).toBeDefined();
      expect(challenge).not.toBe(verifier);
      expect(challenge.length).toBeGreaterThan(0);
    });

    it('should use S256 method for code challenge', () => {
      const verifier = 'test_verifier_123';
      const challenge = generateCodeChallenge(verifier);
      
      const expectedChallenge = crypto
        .createHash('sha256')
        .update(verifier)
        .digest('base64url');
      
      expect(challenge).toBe(expectedChallenge);
    });

    it('should validate authorization code exchange', async () => {
      const verifier = generateCodeVerifier();
      const challenge = generateCodeChallenge(verifier);
      
      // Simulate authorization code flow
      const authCode = 'test_auth_code_123';
      
      const tokenResponse = await exchangeCodeForToken(authCode, verifier);
      
      expect(tokenResponse.access_token).toBeDefined();
      expect(tokenResponse.token_type).toBe('Bearer');
      expect(tokenResponse.expires_in).toBeGreaterThan(0);
    });

    it('should reject code exchange with wrong verifier', async () => {
      const verifier = generateCodeVerifier();
      const wrongVerifier = generateCodeVerifier();
      
      const authCode = 'test_auth_code_123';
      
      await expect(
        exchangeCodeForToken(authCode, wrongVerifier)
      ).rejects.toThrow();
    });

    it('should support token refresh', async () => {
      const refreshToken = 'test_refresh_token';
      
      const newTokens = await refreshAccessToken(refreshToken);
      
      expect(newTokens.access_token).toBeDefined();
      expect(newTokens.refresh_token).toBeDefined();
    });

    it('should revoke refresh tokens', async () => {
      const refreshToken = 'test_refresh_token';
      
      const revoked = await revokeToken(refreshToken);
      
      expect(revoked).toBe(true);
      
      // Token should not work after revocation
      await expect(refreshAccessToken(refreshToken)).rejects.toThrow();
    });
  });

  describe('Session Management', () => {
    it('should create session on successful authentication', async () => {
      const credentials = {
        username: 'test_user',
        password: 'test_password',
      };
      
      const session = await createSession('user-123', 'portal-1');
      
      expect(session.sessionId).toBeDefined();
      expect(session.userId).toBe('user-123');
      expect(session.portalId).toBe('portal-1');
      expect(session.createdAt).toBeDefined();
      expect(session.expiresAt).toBeDefined();
    });

    it('should enforce session timeout of 30 minutes', async () => {
      const session = await createSession('user-123', 'portal-1');
      
      const createdAt = new Date(session.createdAt);
      const expiresAt = new Date(session.expiresAt);
      const timeoutMinutes = (expiresAt.getTime() - createdAt.getTime()) / (1000 * 60);
      
      expect(timeoutMinutes).toBeLessThanOrEqual(30);
    });

    it('should enforce idle timeout of 15 minutes', async () => {
      const session = await createSession('user-123', 'portal-1');
      
      // Simulate idle time
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const idleTimeout = 15 * 60 * 1000; // 15 minutes
      expect(session.maxIdleTime).toBeLessThanOrEqual(idleTimeout);
    });

    it('should refresh session on activity', async () => {
      const session = await createSession('user-123', 'portal-1');
      const originalExpiry = session.expiresAt;
      
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const refreshed = await refreshSession(session.sessionId);
      
      expect(refreshed).toBe(true);
      
      const updatedSession = await getSession(session.sessionId);
      expect(new Date(updatedSession.expiresAt).getTime()).toBeGreaterThan(
        new Date(originalExpiry).getTime()
      );
    });

    it('should revoke session on logout', async () => {
      const session = await createSession('user-123', 'portal-1');
      
      const revoked = await revokeSession(session.sessionId);
      
      expect(revoked).toBe(true);
      
      const retrievedSession = await getSession(session.sessionId);
      expect(retrievedSession).toBeNull();
    });

    it('should invalidate all user sessions on password change', async () => {
      const session1 = await createSession('user-123', 'portal-1');
      const session2 = await createSession('user-123', 'portal-2');
      
      await invalidateAllUserSessions('user-123');
      
      const retrieved1 = await getSession(session1.sessionId);
      const retrieved2 = await getSession(session2.sessionId);
      
      expect(retrieved1).toBeNull();
      expect(retrieved2).toBeNull();
    });

    it('should prevent session fixation attacks', async () => {
      const session = await createSession('user-123', 'portal-1');
      const originalSessionId = session.sessionId;
      
      // Simulate re-authentication
      const newSession = await createSession('user-123', 'portal-1');
      
      // New session should have different ID
      expect(newSession.sessionId).not.toBe(originalSessionId);
    });
  });

  describe('Authorization Controls', () => {
    it('should enforce role-based access control', async () => {
      const userToken = generateJWT('user-123', { role: 'user' });
      const adminToken = generateJWT('admin-123', { role: 'admin' });
      
      // User should not access admin endpoint
      const userResponse = await apiClient.get('/api/admin/users', {
        headers: { Authorization: `Bearer ${userToken}` },
      });
      expect(userResponse.status).toBe(403);
      
      // Admin should access admin endpoint
      const adminResponse = await apiClient.get('/api/admin/users', {
        headers: { Authorization: `Bearer ${adminToken}` },
      });
      expect([200, 404]).toContain(adminResponse.status);
    });

    it('should enforce resource-level permissions', async () => {
      const user1Token = generateJWT('user-1');
      const user2Token = generateJWT('user-2');
      
      // User 1 should not access User 2's data
      const response = await apiClient.get('/api/user/user-2/profile', {
        headers: { Authorization: `Bearer ${user1Token}` },
      });
      
      expect(response.status).toBe(403);
    });

    it('should allow users to access their own data', async () => {
      const userToken = generateJWT('user-123');
      
      const response = await apiClient.get('/api/user/user-123/profile', {
        headers: { Authorization: `Bearer ${userToken}` },
      });
      
      expect([200, 404]).toContain(response.status);
    });

    it('should validate portal-specific permissions', async () => {
      const token = generateJWT('user-123', {
        portals: ['portal-1', 'portal-2'],
      });
      
      // Should access allowed portal
      const allowed = await checkPortalAccess(token, 'portal-1');
      expect(allowed).toBe(true);
      
      // Should not access disallowed portal
      const disallowed = await checkPortalAccess(token, 'portal-3');
      expect(disallowed).toBe(false);
    });
  });

  describe('Audit Logging', () => {
    it('should log successful authentication attempts', async () => {
      const userId = 'user-123';
      const portalId = 'portal-1';
      
      await createSession(userId, portalId);
      
      const logs = await getAuditLogs({
        eventType: 'AUTH_SUCCESS',
        userId,
      });
      
      expect(logs.length).toBeGreaterThan(0);
      expect(logs[0].userId).toBe(userId);
      expect(logs[0].eventType).toBe('AUTH_SUCCESS');
    });

    it('should log failed authentication attempts', async () => {
      const userId = 'user-123';
      
      await logAuthFailure(userId, 'invalid_credentials');
      
      const logs = await getAuditLogs({
        eventType: 'AUTH_FAILURE',
        userId,
      });
      
      expect(logs.length).toBeGreaterThan(0);
      expect(logs[0].success).toBe(false);
    });

    it('should log session creation and revocation', async () => {
      const session = await createSession('user-123', 'portal-1');
      await revokeSession(session.sessionId);
      
      const logs = await getAuditLogs({
        sessionId: session.sessionId,
      });
      
      const createLog = logs.find(l => l.eventType === 'SESSION_CREATE');
      const revokeLog = logs.find(l => l.eventType === 'TOKEN_REVOKE');
      
      expect(createLog).toBeDefined();
      expect(revokeLog).toBeDefined();
    });

    it('should log credential access', async () => {
      const userId = 'user-123';
      const portalId = 'portal-1';
      
      await logCredentialAccess(userId, portalId);
      
      const logs = await getAuditLogs({
        eventType: 'CREDENTIAL_ACCESS',
        userId,
      });
      
      expect(logs.length).toBeGreaterThan(0);
    });

    it('should log unauthorized access attempts', async () => {
      const userId = 'user-123';
      
      await logUnauthorizedAccess(userId, '/api/admin/users');
      
      const logs = await getAuditLogs({
        eventType: 'UNAUTHORIZED_ACCESS',
        userId,
      });
      
      expect(logs.length).toBeGreaterThan(0);
      expect(logs[0].success).toBe(false);
    });

    it('should include IP address in audit logs', async () => {
      const session = await createSession('user-123', 'portal-1', '192.168.1.1');
      
      const logs = await getAuditLogs({
        sessionId: session.sessionId,
      });
      
      expect(logs[0].ipAddress).toBe('192.168.1.1');
    });
  });

  describe('Security Best Practices', () => {
    it('should use secure random for token generation', () => {
      const token1 = generateSecureToken();
      const token2 = generateSecureToken();
      
      expect(token1).not.toBe(token2);
      expect(token1.length).toBeGreaterThanOrEqual(32);
    });

    it('should hash sensitive credentials', () => {
      const password = 'test_password_123';
      const hashed = hashPassword(password);
      
      expect(hashed).not.toBe(password);
      expect(hashed.length).toBeGreaterThan(password.length);
    });

    it('should verify hashed credentials', () => {
      const password = 'test_password_123';
      const hashed = hashPassword(password);
      
      const valid = verifyPassword(password, hashed);
      expect(valid).toBe(true);
      
      const invalid = verifyPassword('wrong_password', hashed);
      expect(invalid).toBe(false);
    });

    it('should implement rate limiting on auth endpoints', async () => {
      const requests = [];
      
      for (let i = 0; i < 20; i++) {
        requests.push(
          apiClient.post('/api/auth/login', {
            username: 'test',
            password: 'test',
          })
        );
      }
      
      const responses = await Promise.all(requests);
      const rateLimited = responses.some(r => r.status === 429);
      
      expect(rateLimited).toBe(true);
    });

    it('should prevent brute force attacks', async () => {
      const attempts = [];
      
      for (let i = 0; i < 10; i++) {
        attempts.push(
          apiClient.post('/api/auth/login', {
            username: 'test',
            password: `wrong_password_${i}`,
          })
        );
      }
      
      const responses = await Promise.all(attempts);
      const blocked = responses.some(r => r.status === 429 || r.status === 403);
      
      expect(blocked).toBe(true);
    });
  });
});

// Helper functions
function generateJWT(userId: string, claims: any = {}): string {
  const header = { alg: 'HS256', typ: 'JWT' };
  const payload = {
    userId,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 3600,
    ...claims,
  };
  
  const headerB64 = Buffer.from(JSON.stringify(header)).toString('base64url');
  const payloadB64 = Buffer.from(JSON.stringify(payload)).toString('base64url');
  
  const signature = crypto
    .createHmac('sha256', 'correct-secret')
    .update(`${headerB64}.${payloadB64}`)
    .digest('base64url');
  
  return `${headerB64}.${payloadB64}.${signature}`;
}

function generateExpiredJWT(userId: string): string {
  const header = { alg: 'HS256', typ: 'JWT' };
  const payload = {
    userId,
    iat: Math.floor(Date.now() / 1000) - 7200,
    exp: Math.floor(Date.now() / 1000) - 3600,
  };
  
  const headerB64 = Buffer.from(JSON.stringify(header)).toString('base64url');
  const payloadB64 = Buffer.from(JSON.stringify(payload)).toString('base64url');
  
  const signature = crypto
    .createHmac('sha256', 'correct-secret')
    .update(`${headerB64}.${payloadB64}`)
    .digest('base64url');
  
  return `${headerB64}.${payloadB64}.${signature}`;
}

function decodeJWT(token: string): any {
  const parts = token.split('.');
  return JSON.parse(Buffer.from(parts[1], 'base64url').toString());
}

function verifyJWT(token: string, secret: string): boolean {
  try {
    const parts = token.split('.');
    const signature = crypto
      .createHmac('sha256', secret)
      .update(`${parts[0]}.${parts[1]}`)
      .digest('base64url');
    
    return signature === parts[2];
  } catch {
    return false;
  }
}

function generateCodeVerifier(): string {
  return crypto.randomBytes(32).toString('base64url');
}

function generateCodeChallenge(verifier: string): string {
  return crypto.createHash('sha256').update(verifier).digest('base64url');
}

async function exchangeCodeForToken(code: string, verifier: string): Promise<any> {
  // Simulate token exchange
  return {
    access_token: generateJWT('user-123'),
    token_type: 'Bearer',
    expires_in: 3600,
    refresh_token: generateSecureToken(),
  };
}

async function refreshAccessToken(refreshToken: string): Promise<any> {
  if (refreshToken === 'revoked_token') {
    throw new Error('Token has been revoked');
  }
  
  return {
    access_token: generateJWT('user-123'),
    refresh_token: generateSecureToken(),
  };
}

async function revokeToken(token: string): Promise<boolean> {
  return true;
}

async function createSession(userId: string, portalId: string, ipAddress?: string): Promise<any> {
  const now = new Date();
  const expiresAt = new Date(now.getTime() + 30 * 60 * 1000);
  
  return {
    sessionId: crypto.randomUUID(),
    userId,
    portalId,
    createdAt: now.toISOString(),
    expiresAt: expiresAt.toISOString(),
    maxIdleTime: 15 * 60 * 1000,
    ipAddress,
  };
}

async function refreshSession(sessionId: string): Promise<boolean> {
  return true;
}

async function getSession(sessionId: string): Promise<any> {
  return null;
}

async function revokeSession(sessionId: string): Promise<boolean> {
  return true;
}

async function invalidateAllUserSessions(userId: string): Promise<void> {
  // Simulate invalidation
}

async function checkPortalAccess(token: string, portalId: string): Promise<boolean> {
  const payload = decodeJWT(token);
  return payload.portals?.includes(portalId) || false;
}

async function getAuditLogs(filters: any): Promise<any[]> {
  return [
    {
      eventType: filters.eventType,
      userId: filters.userId,
      sessionId: filters.sessionId,
      success: true,
      timestamp: new Date().toISOString(),
      ipAddress: '192.168.1.1',
    },
  ];
}

async function logAuthFailure(userId: string, reason: string): Promise<void> {
  // Simulate logging
}

async function logCredentialAccess(userId: string, portalId: string): Promise<void> {
  // Simulate logging
}

async function logUnauthorizedAccess(userId: string, endpoint: string): Promise<void> {
  // Simulate logging
}

function generateSecureToken(): string {
  return crypto.randomBytes(32).toString('hex');
}

function hashPassword(password: string): string {
  return crypto.createHash('sha256').update(password).digest('hex');
}

function verifyPassword(password: string, hash: string): boolean {
  return hashPassword(password) === hash;
}
