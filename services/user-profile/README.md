# User Profile Service

Secure user profile management service for Gram Sahayak with industry-standard encryption.

## Features

- **Encrypted Storage**: All user data encrypted at rest using AES-256-GCM
- **User Recognition**: Identify returning users by phone number
- **Profile Management**: Complete CRUD operations for user profiles
- **Data Validation**: Comprehensive validation for all profile fields
- **Secure API**: RESTful API with proper error handling

## Architecture

The service implements a three-layer architecture:

1. **API Layer** (`main.py`): FastAPI endpoints for profile operations
2. **Storage Layer** (`storage.py`): Profile persistence with encryption
3. **Encryption Layer** (`encryption.py`): AES-256-GCM encryption service

## Data Model

User profiles contain:

- **Personal Information**: Name, age, gender, phone, Aadhaar (optional)
- **Demographics**: State, district, block, village, caste, religion, family size
- **Economic Data**: Income, occupation, land ownership, bank details
- **Preferences**: Language, dialect, communication mode
- **Application History**: Record of scheme applications

## API Endpoints

### Health Check
```
GET /health
```

### Create Profile
```
POST /profiles
Body: CreateUserProfileRequest
Response: UserProfileResponse
```

### Get Profile
```
GET /profiles/{user_id}
Response: UserProfileResponse
```

### Update Profile
```
PUT /profiles
Body: UpdateUserProfileRequest
Response: UserProfileResponse
```

### Delete Profile
```
DELETE /profiles/{user_id}
Response: Success message
```

### Recognize User
```
GET /profiles/recognize/{phone_number}
Response: UserProfileResponse
```

## Security

### Encryption
- **Algorithm**: AES-256-GCM (Authenticated Encryption)
- **Key Management**: 256-bit keys with secure generation
- **Nonce**: Random 96-bit nonce for each encryption operation
- **Storage**: Encrypted data stored with nonce prepended

### Data Protection
- All sensitive data encrypted at rest
- Secure key derivation using PBKDF2 with SHA-256
- No plaintext storage of personal information
- Encrypted files use `.enc` extension

## Installation

```bash
cd services/user-profile
pip install -r requirements.txt
```

## Running the Service

```bash
# Development
python main.py

# Production with environment variables
ENCRYPTION_KEY=<base64-key> STORAGE_PATH=/data/profiles uvicorn main:app --host 0.0.0.0 --port 8009
```

## Docker

```bash
docker build -t user-profile-service .
docker run -p 8009:8009 -e ENCRYPTION_KEY=<key> user-profile-service
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_storage.py

# Run with coverage
pytest --cov=. --cov-report=html
```

## Environment Variables

- `ENCRYPTION_KEY`: Base64-encoded 256-bit encryption key (optional, generates if not provided)
- `STORAGE_PATH`: Directory for encrypted profile storage (default: `./data/profiles`)

## Requirements Validation

This service implements:

- **Requirement 7.1**: Secure collection and storage of demographic information with industry-standard encryption
- **Requirement 7.2**: User recognition and context loading from secure storage

## Implementation Details

### Encryption Service
- Uses `cryptography` library for AES-256-GCM
- Generates random nonce for each encryption
- Supports key derivation from passwords using PBKDF2
- Provides base64 encoding for key storage

### Storage Service
- File-based storage with encrypted profiles
- In-memory caching for performance
- Atomic file operations for data integrity
- Support for profile persistence across service restarts

### Validation
- Pydantic models for comprehensive data validation
- Phone number format validation
- Aadhaar number format validation (12 digits)
- IFSC code validation (11 characters)
- Age, income, and family size range validation

## Future Enhancements

- Database backend (PostgreSQL with encryption)
- Multi-factor authentication
- Audit logging for all operations
- Data retention policies
- Backup and recovery mechanisms
