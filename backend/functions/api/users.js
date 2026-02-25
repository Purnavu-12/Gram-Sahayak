// User API - Tenant-aware CRUD operations
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, GetCommand, PutCommand } = require('@aws-sdk/lib-dynamodb');

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);
const TABLE_NAME = process.env.TABLE_NAME || 'users';

exports.handler = async (event) => {
  // Extract tenant context from authorizer
  const tenantId = event.requestContext.authorizer.tenantId;
  const userId = event.requestContext.authorizer.userId;
  const roles = JSON.parse(event.requestContext.authorizer.roles);
  
  if (!tenantId) {
    return response(401, { error: 'Missing tenant context' });
  }
  
  const method = event.httpMethod;
  const pathParams = event.pathParameters || {};
  
  try {
    if (method === 'GET' && pathParams.id) {
      return await getUser(tenantId, pathParams.id);
    } else if (method === 'POST') {
      return await createUser(tenantId, JSON.parse(event.body));
    }
    
    return response(404, { error: 'Not found' });
  } catch (error) {
    console.error('Error:', error);
    return response(500, { error: 'Internal server error' });
  }
};

async function getUser(tenantId, userId) {
  // Tenant-scoped key: prevents cross-tenant access
  const pk = `${tenantId}#USER#${userId}`;
  
  const result = await docClient.send(new GetCommand({
    TableName: TABLE_NAME,
    Key: { pk }
  }));
  
  if (!result.Item) {
    return response(404, { error: 'User not found' });
  }
  
  return response(200, result.Item);
}

async function createUser(tenantId, userData) {
  const userId = `user-${Date.now()}`;
  const pk = `${tenantId}#USER#${userId}`;
  
  const item = {
    pk,
    tenantId,
    userId,
    email: userData.email,
    name: userData.name,
    createdAt: new Date().toISOString()
  };
  
  await docClient.send(new PutCommand({
    TableName: TABLE_NAME,
    Item: item
  }));
  
  return response(201, item);
}

function response(statusCode, body) {
  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*'
    },
    body: JSON.stringify(body)
  };
}
