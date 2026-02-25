# Task 7.2 Completion: Add Document Acquisition Guidance

## Overview
Successfully implemented document acquisition guidance functionality for the Document Guidance Service, including step-by-step instructions, authority contact information, and document templates.

## Implementation Summary

### Core Components Created

1. **Acquisition Data Module** (`acquisition_data.py`)
   - Step-by-step acquisition guidance for 4 key documents
   - Authority contact information for 3 government offices
   - Document templates and examples for 2 certificate types
   - Multilingual support in 4 Indian languages (English, Hindi, Tamil, Telugu)

2. **Enhanced DocumentGuideService** (`document_guide_service.py`)
   - New methods for acquisition guidance retrieval
   - Authority contact information system
   - Document template management
   - Complete guidance aggregation

3. **New API Endpoints** (`main.py`)
   - POST /documents/acquisition-guidance
   - POST /documents/template
   - POST /documents/complete-guidance
   - POST /authorities/contact
   - GET /authorities/all

### Document Acquisition Guidance

Implemented for 4 document types:
1. **Aadhaar Card**
   - 7-step process from enrollment to receipt
   - UIDAI center contact information
   - Processing time: 60-90 days
   - Fees: Free for first enrollment

2. **Income Certificate**
   - 9-step process through Tehsil office
   - Revenue department contact details
   - Processing time: 15-30 days
   - Fees: ₹10-50 (varies by state)

3. **Caste Certificate**
   - 9-step process with verification
   - Tehsil office contact information
   - Processing time: 30-45 days
   - Fees: ₹10-50 (varies by state)

4. **Land Records**
   - 7-step process for obtaining records
   - Land records office contact details
   - Processing time: 7-15 days
   - Fees: ₹20-100 (varies by state)

### Authority Contact Information

Implemented for 3 authority types:
1. **UIDAI Center / CSC**
   - Toll-free helpline: 1947
   - Website: https://uidai.gov.in
   - Email: help@uidai.gov.in
   - Center locator tool

2. **Tehsil / Block Office**
   - District collectorate contact guidance
   - State revenue department website references
   - Local office location guidance

3. **District Collectorate**
   - District-specific contact information
   - Website search guidance
   - Headquarters location information

### Document Templates

Implemented for 2 certificate types:
1. **Income Certificate**
   - Official format description
   - 7 key elements required
   - Sample certificate text
   - Multilingual templates

2. **Caste Certificate**
   - Official format description
   - 7 key elements required
   - Sample certificate text
   - Multilingual templates

## API Endpoints

### POST /documents/acquisition-guidance
Get step-by-step guidance for obtaining a specific document.
**Validates: Requirements 5.3, 5.5**

**Request:**
```json
{
  "document_id": "INCOME_CERTIFICATE",
  "language": "en"
}
```

**Response:**
```json
{
  "document_id": "INCOME_CERTIFICATE",
  "document_name": "Income Certificate",
  "language": "en",
  "steps": [
    "Visit Tehsil or Block office (Revenue Department)",
    "Collect income certificate application form",
    ...
  ],
  "authority": {
    "name": "Tehsil / Taluka / Block Office (Revenue Department)",
    "contact": {
      "phone": "Contact your district collectorate...",
      "website": "Check your state revenue department website",
      ...
    }
  },
  "processing_time": "15-30 days",
  "fees": "₹10-50 (varies by state)"
}
```

### POST /documents/template
Get template and example information for a specific document.
**Validates: Requirement 5.4**

**Request:**
```json
{
  "document_id": "INCOME_CERTIFICATE",
  "language": "en"
}
```

**Response:**
```json
{
  "document_id": "INCOME_CERTIFICATE",
  "document_name": "Income Certificate",
  "language": "en",
  "template_info": {
    "format": "Official certificate on government letterhead",
    "key_elements": [
      "Applicant's full name and father's/husband's name",
      ...
    ],
    "sample_text": "This is to certify that..."
  }
}
```

### POST /documents/complete-guidance
Get complete guidance including acquisition steps, authority contacts, and templates.
**Validates: Requirements 5.3, 5.4, 5.5**

**Response includes:**
- Document name and description
- Acquisition guidance with steps
- Authority contact information
- Document template (if available)
- Alternative documents (if available)

### POST /authorities/contact
Get contact information for a specific authority.
**Validates: Requirement 5.3**

### GET /authorities/all
Get list of all authorities with contact information.

## Requirements Validation

### Requirement 5.3: Document Acquisition Guidance from Authorities
✅ **VALIDATED**
- Step-by-step guidance for obtaining each document
- Authority contact information (phone, website, email, locator)
- Clear instructions on which office to visit
- Processing times and fees included

### Requirement 5.4: Document Examples and Templates
✅ **VALIDATED**
- Document format descriptions
- Key elements required in each document
- Sample certificate text
- Multilingual template support

### Requirement 5.5: Step-by-Step Acquisition Guidance
✅ **VALIDATED**
- Detailed step-by-step instructions
- Sequential process from application to receipt
- Authority information integrated with steps
- Processing time and fee information

## Testing

### Unit Tests (18 tests in test_acquisition_guidance.py)
- Acquisition guidance in multiple languages
- Authority contact information retrieval
- Document template retrieval
- Complete guidance aggregation
- Invalid document/authority handling
- Multilingual template support
- Processing time and fees validation

### API Integration Tests (13 tests in test_acquisition_api.py)
- All new API endpoints tested
- Multilingual API responses
- Default language behavior
- Error handling for invalid inputs
- Complete guidance endpoint validation

### Existing Tests (26 tests from Task 7.1)
- All previous tests still passing
- No regression in existing functionality

**Total: 57 tests - ALL PASSING ✅**

## Files Created/Modified

```
services/document-guide/
├── acquisition_data.py                      # NEW: Acquisition guidance data
├── document_guide_service.py                # MODIFIED: Added new methods
├── main.py                                  # MODIFIED: Added new endpoints
├── tests/
│   ├── test_acquisition_guidance.py         # NEW: Unit tests
│   └── test_acquisition_api.py              # NEW: API tests
└── TASK_7.2_COMPLETION.md                   # NEW: This file
```

## Multilingual Support

All acquisition guidance, authority contacts, and templates available in:
1. English (en)
2. Hindi (hi)
3. Tamil (ta)
4. Telugu (te)

## Key Features

1. **Step-by-Step Guidance**: Clear, sequential instructions for obtaining each document
2. **Authority Integration**: Contact information embedded in guidance
3. **Processing Information**: Time and cost estimates for each document
4. **Document Templates**: Format specifications and sample text
5. **Complete Guidance**: Aggregated view combining all information
6. **Multilingual Support**: All content available in 4 Indian languages
7. **RESTful API**: Clean, well-documented endpoints
8. **Comprehensive Testing**: 31 new tests covering all functionality

## Integration with Task 7.1

The new functionality seamlessly integrates with Task 7.1:
- Uses existing document database
- Extends existing service class
- Maintains consistent API patterns
- Preserves all existing functionality
- All 26 existing tests still passing

## Usage Example

A user can now:
1. Get list of required documents for a scheme (Task 7.1)
2. Get alternatives if documents are missing (Task 7.1)
3. Get step-by-step guidance on how to obtain each document (Task 7.2)
4. Get authority contact information (Task 7.2)
5. Get document templates and examples (Task 7.2)
6. Get complete guidance in one API call (Task 7.2)

## Next Steps

Task 7.3 will add:
- Property-based testing for comprehensive document guidance validation
- Testing across all document types and languages
- Edge case validation

## Status

✅ **TASK 7.2 COMPLETE**
- All sub-tasks implemented:
  - ✅ Implement step-by-step guidance generation
  - ✅ Create authority contact information system
  - ✅ Add document template and example management
- All tests passing (57 total)
- Requirements 5.3, 5.4, 5.5 validated
- Service ready for integration
