// Lambda Authorizer - Validates JWT and injects tenant context
exports.handler = async (event) => {
  const token = event.authorizationToken?.replace('Bearer ', '');
  
  if (!token) {
    throw new Error('Unauthorized');
  }
  
  // In production, validate JWT with Cognito/Auth0
  // For demo, we'll extract a mock tenant ID
  const decoded = { tenantId: 'tenant-123', userId: 'user-456', roles: ['user'] };
  
  return {
    principalId: decoded.userId,
    policyDocument: {
      Version: '2012-10-17',
      Statement: [{
        Action: 'execute-api:Invoke',
        Effect: 'Allow',
        Resource: event.methodArn
      }]
    },
    context: {
      tenantId: decoded.tenantId,
      userId: decoded.userId,
      roles: JSON.stringify(decoded.roles)
    }
  };
};
