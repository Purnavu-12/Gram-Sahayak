# Document Guide Service

The Document Guide Service provides multilingual guidance on document requirements for government schemes in India.

## Features

- **Multilingual Document Database**: Document names and descriptions in 10 Indian languages (English, Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi)
- **Scheme-Specific Document Mapping**: Maps each government scheme to its required documents
- **Alternative Document Suggestions**: Suggests acceptable alternative documents when primary documents are unavailable

## Validates Requirements

- **Requirement 5.1**: Provides complete document lists in user's language
- **Requirement 5.2**: Describes acceptable alternatives for each document type

## API Endpoints

### Get Scheme Documents
```
POST /documents/scheme
{
  "scheme_id": "PM-KISAN",
  "language": "hi"
}
```

Returns complete list of required documents for a scheme in the specified language.

### Get Document Alternatives
```
POST /documents/alternatives
{
  "document_id": "AADHAAR",
  "language": "ta"
}
```

Returns acceptable alternative documents for a specific document.

### Get Complete Scheme Documents with Alternatives
```
POST /documents/scheme/complete
{
  "scheme_id": "PM-KISAN",
  "language": "en"
}
```

Returns complete document requirements with alternatives for each document.

### Get Supported Languages
```
GET /documents/languages
```

Returns list of supported languages.

### Get All Documents
```
GET /documents/all?language=hi
```

Returns all documents in the database in the specified language.

## Supported Documents

- Aadhaar Card
- Voter ID Card
- Ration Card
- Bank Passbook
- Land Records / Land Ownership Certificate
- Income Certificate
- Caste Certificate
- Passport Size Photograph

## Supported Languages

- English (en)
- Hindi (hi)
- Tamil (ta)
- Telugu (te)
- Bengali (bn)
- Marathi (mr)
- Gujarati (gu)
- Kannada (kn)
- Malayalam (ml)
- Punjabi (pa)

## Running the Service

### Local Development
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

### Docker
```bash
docker build -t document-guide .
docker run -p 8000:8000 document-guide
```

## Testing

```bash
pytest tests/
```
