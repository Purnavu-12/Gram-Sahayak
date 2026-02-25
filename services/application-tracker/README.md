# Application Tracker Service

The Application Tracker Service provides secure integration with government portals for automated application submission and status tracking. This service is part of the Gram Sahayak platform and enables seamless interaction with India's Digital Public Infrastructure.

## Features

### Secure API Connections (Requirement 6.1)
- **Multi-Portal Support**: Integrates with major government portals including:
  - myScheme (National Scheme Portal)
  - e-Shram (Unorganized Workers Platform)
  - UMANG (Unified Mobile Application)
  - PM-KISAN, MGNREGA, Ayushman Bharat
  - Generic portal integration framework

- **Multiple Authentication Methods**:
  - OAuth2 for modern government APIs
  - API Key authentication
  - JWT (JSON Web Tokens)
  - Basic authentication
  - Token caching and automatic renewal

- **Security Features**:
  - End-to-end encryption for sensitive data
  - Secure token management
  - Automatic credential validation
  - Rate limiting and retry logic

### Application Submission Automation (Requirement 6.1)
- **Automated Submission**: Submit applications to appropriate government portals
- **Unique Tracking**: Generate submission IDs and confirmation numbers
- **Retry Logic**: Automatic retry with exponential backoff for failed submissions
- **Data Encryption**: Encrypt sensitive application data before storage
- **Multi-Portal Support**: Submit to different portals based on scheme requirements

### Status Tracking and Monitoring (Requirement 6.3)
- **Real-Time Status**: Retrieve current application status from government systems
- **Progress Tracking**: Monitor application progress with percentage completion
- **Status Descriptions**: Human-readable status explanations in multiple languages
- **Next Steps Guidance**: Provide actionable next steps based on current status
- **Automated Monitoring**: Set up periodic status checks with configurable intervals

### Application Lifecycle Management (Requirements 6.2, 6.4)
- **Confirmation Tracking**: Track confirmation numbers and application identifiers
- **Timeline Management**: 
  - Calculate expected completion dates based on portal and scheme type
  - Generate processing milestones (submission, acknowledgment, verification, review, approval, completion)
  - Update timelines as applications progress
  - Adjust estimates based on actual processing times
  
- **Notification System**:
  - Automatic notifications for status updates
  - Priority-based notifications (low, medium, high, urgent)
  - Action-required flags for critical updates
  - Unread notification tracking
  - Notification history for each application
  
- **Additional Information Requests**:
  - Create requests for missing documents or information
  - Set due dates for information submission
  - Track request status (pending, submitted, expired)
  - Guide users through information submission process
  - Automatic notifications when additional info is required or submitted

## API Endpoints

### Authentication
```
POST /portal/authenticate
```
Authenticate with a government portal and obtain access token.

**Request:**
```json
{
  "portal_type": "myscheme",
  "credentials": {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret"
  }
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2024-01-15T10:30:00",
  "cached": false
}
```

### Application Submission
```
POST /application/submit
```
Submit an application to a government portal.

**Request:**
```json
{
  "portal_type": "myscheme",
  "application_data": {
    "scheme_id": "PM_KISAN_2024",
    "applicant": {
      "name": "राज कुमार",
      "aadhaar": "1234-5678-9012",
      "phone": "+91-9876543210"
    }
  },
  "credentials": {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret"
  }
}
```

**Response:**
```json
{
  "success": true,
  "submission_id": "A1B2C3D4E5F6G7H8",
  "confirmation_number": "MYS123456789",
  "application_id": "MYSCHEME-1705315200",
  "portal": "myscheme",
  "submitted_at": "2024-01-15T10:00:00",
  "expected_processing_time": "15-30 days"
}
```

### Status Check
```
POST /application/status
```
Retrieve current application status from government portal.

**Request:**
```json
{
  "portal_type": "myscheme",
  "application_id": "MYSCHEME-1705315200",
  "credentials": {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret"
  }
}
```

**Response:**
```json
{
  "success": true,
  "application_id": "MYSCHEME-1705315200",
  "portal": "myscheme",
  "status": "under_review",
  "status_description": "Application is under review by officials",
  "last_updated": "2024-01-15T10:00:00",
  "progress_percentage": 50,
  "next_steps": [
    "Officials are reviewing your application",
    "You may be contacted for additional information"
  ],
  "estimated_completion": "2024-01-30T10:00:00"
}
```

### Status Monitoring
```
POST /application/monitor
```
Set up monitoring for application status with periodic checks.

**Request:**
```json
{
  "portal_type": "myscheme",
  "application_id": "MYSCHEME-1705315200",
  "credentials": {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret"
  },
  "check_interval": 3600
}
```

**Response:**
```json
{
  "success": true,
  "monitoring_enabled": true,
  "application_id": "MYSCHEME-1705315200",
  "portal": "myscheme",
  "check_interval_seconds": 3600,
  "current_status": { ... },
  "monitoring_started_at": "2024-01-15T10:00:00"
}
```

### Information Endpoints
```
GET /portals/supported
GET /status/types
GET /health
```

### Timeline Management
```
GET /application/{application_id}/timeline
```
Get timeline information for an application including confirmation number, expected completion date, and processing milestones.

**Response:**
```json
{
  "success": true,
  "timeline": {
    "confirmation_number": "MYS123456789",
    "application_id": "MYSCHEME-1705315200",
    "submitted_at": "2024-01-15T10:00:00",
    "expected_completion": "2024-02-05T10:00:00",
    "estimated_days": 21,
    "milestones": [
      {
        "stage": "submission",
        "title": "Application Submitted",
        "description": "Your application has been received",
        "expected_date": "2024-01-15T10:00:00",
        "completed": true,
        "completed_at": "2024-01-15T10:00:00"
      },
      {
        "stage": "acknowledgment",
        "title": "Acknowledgment",
        "description": "Application acknowledged by department",
        "expected_date": "2024-01-17T10:00:00",
        "completed": false
      }
    ],
    "last_updated": "2024-01-15T10:00:00"
  }
}
```

### Notification Management
```
GET /application/{application_id}/notifications
```
Get all notifications for an application. Supports `unread_only=true` query parameter.

**Response:**
```json
{
  "success": true,
  "application_id": "MYSCHEME-1705315200",
  "count": 2,
  "notifications": [
    {
      "notification_id": "uuid-1234",
      "type": "status_update",
      "priority": "medium",
      "title": "Application Submitted Successfully",
      "message": "Your application has been submitted. Confirmation number: MYS123456789...",
      "created_at": "2024-01-15T10:00:00",
      "read": false,
      "action_required": false,
      "action_details": null
    }
  ]
}
```

```
POST /application/notification/read
```
Mark a notification as read.

**Request:**
```json
{
  "application_id": "MYSCHEME-1705315200",
  "notification_id": "uuid-1234"
}
```

### Additional Information Requests
```
POST /application/additional-info/request
```
Create a request for additional information from the applicant.

**Request:**
```json
{
  "application_id": "MYSCHEME-1705315200",
  "required_items": [
    {
      "name": "Income Certificate",
      "description": "Certificate from Tehsildar showing annual income"
    },
    {
      "name": "Bank Statement",
      "description": "Last 6 months bank statement"
    }
  ],
  "due_days": 7
}
```

**Response:**
```json
{
  "success": true,
  "request": {
    "request_id": "uuid-5678",
    "application_id": "MYSCHEME-1705315200",
    "requested_at": "2024-01-15T10:00:00",
    "due_date": "2024-01-22T10:00:00",
    "items": [...],
    "status": "pending"
  }
}
```

```
GET /application/{application_id}/additional-info/requests
```
Get all additional information requests for an application. Supports `status` query parameter (pending, submitted, expired).

```
POST /application/additional-info/submit
```
Submit additional information in response to a request.

**Request:**
```json
{
  "request_id": "uuid-5678",
  "application_id": "MYSCHEME-1705315200",
  "submitted_data": {
    "income_certificate": "certificate_data",
    "bank_statement": "statement_data"
  }
}
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the service:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

3. Run with Docker:
```bash
docker build -t application-tracker .
docker run -p 8000:8000 application-tracker
```

## Testing

Run all tests:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_government_portal_integration.py -v
pytest tests/test_api_integration.py -v
```

## Architecture

### Components

1. **GovernmentPortalIntegration**: Core service class that handles:
   - Portal authentication and token management
   - Application submission with retry logic
   - Status tracking and monitoring
   - Data encryption and security

2. **FastAPI Application**: REST API that exposes:
   - Authentication endpoints
   - Submission endpoints
   - Status tracking endpoints
   - Monitoring endpoints

3. **Security Layer**:
   - Fernet encryption for sensitive data
   - JWT token generation and validation
   - Secure credential management
   - Token caching with expiry

### Portal Types

The service supports multiple portal types:
- `myscheme`: National Scheme Portal
- `eshram`: e-Shram Platform
- `umang`: UMANG Application
- `digilocker`: DigiLocker Integration
- `pmkisan`: PM-KISAN Portal
- `mgnrega`: MGNREGA Portal
- `ayushmanbharat`: Ayushman Bharat Portal
- `generic`: Generic Government Portal

### Application Status Types

- `draft`: Application is being prepared
- `submitted`: Application has been submitted successfully
- `under_review`: Application is under review by officials
- `pending_documents`: Additional documents are required
- `approved`: Application has been approved
- `rejected`: Application has been rejected
- `processing`: Application is being processed
- `completed`: Application processing is complete

## Configuration

Portal configurations are defined in `government_portal_integration.py`. In production, these should be loaded from secure configuration management systems.

Each portal configuration includes:
- Base URL for API endpoints
- Authentication type (OAuth2, API Key, JWT, Basic)
- Endpoint paths for submit, status, and update operations
- Rate limits and retry attempts

## Security Considerations

1. **Encryption**: All sensitive data is encrypted using Fernet symmetric encryption
2. **Token Management**: Access tokens are cached and automatically renewed
3. **Secure Communication**: All API calls use HTTPS in production
4. **Credential Validation**: Credentials are validated before use
5. **Rate Limiting**: Built-in rate limiting to prevent abuse
6. **Retry Logic**: Exponential backoff for failed requests

## Integration with Gram Sahayak

This service integrates with other Gram Sahayak services:
- **Form Generator**: Receives completed application forms
- **Document Guide**: Validates required documents before submission
- **User Profile**: Retrieves user credentials and preferences
- **Notification Service**: Sends status updates to users

## Future Enhancements

- Real-time webhook support for status updates
- Batch submission for multiple applications
- Advanced analytics and reporting
- Multi-language support for status descriptions
- Integration with more government portals
- Offline submission queue with sync

## License

Part of the Gram Sahayak platform.
