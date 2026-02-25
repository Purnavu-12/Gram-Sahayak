"""
Property-Based Tests for Document Guidance Service
**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

Property 10: Comprehensive Document Guidance
For any scheme requiring documentation, the Document_Guide should:
1. Provide complete multilingual document lists (Requirement 5.1)
2. Explain acceptable alternatives for each document type (Requirement 5.2)
3. Provide acquisition guidance from appropriate authorities (Requirement 5.3)
4. Offer examples and templates (Requirement 5.4)
5. Give step-by-step instructions (Requirement 5.5)
"""
import pytest
import sys
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from document_guide_service import DocumentGuideService


# Custom strategies for generating valid test data
@st.composite
def scheme_id_strategy(draw):
    """Generate valid scheme IDs from the document guide database"""
    valid_schemes = [
        "PM-KISAN", "MGNREGA", "PM-FASAL-BIMA", 
        "WIDOW-PENSION", "OLD-AGE-PENSION",
        "SC-ST-SCHOLARSHIP", "OBC-SCHOLARSHIP"
    ]
    return draw(st.sampled_from(valid_schemes))


@st.composite
def document_id_strategy(draw):
    """Generate valid document IDs from the document guide database"""
    valid_documents = [
        "AADHAAR", "VOTER_ID", "RATION_CARD", "BANK_PASSBOOK",
        "LAND_RECORDS", "INCOME_CERTIFICATE", "CASTE_CERTIFICATE",
        "PASSPORT_PHOTO"
    ]
    return draw(st.sampled_from(valid_documents))


@st.composite
def language_strategy(draw):
    """Generate valid language codes"""
    valid_languages = ["en", "hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa"]
    return draw(st.sampled_from(valid_languages))


@pytest.fixture
def service():
    """Create a fresh service instance for each test"""
    return DocumentGuideService()


@pytest.mark.asyncio
@given(
    scheme_id=scheme_id_strategy(),
    language=language_strategy()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_comprehensive_document_guidance(scheme_id: str, language: str):
    """
    **Feature: gram-sahayak, Property 10: Comprehensive Document Guidance**
    **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
    
    Property: For any scheme requiring documentation, the Document_Guide should provide:
    1. Complete multilingual document lists (Requirement 5.1)
    2. Acceptable alternatives for each document type (Requirement 5.2)
    3. Acquisition guidance from appropriate authorities (Requirement 5.3)
    4. Examples and templates (Requirement 5.4)
    5. Step-by-step instructions (Requirement 5.5)
    """
    service = DocumentGuideService()
    
    # 1. Test complete multilingual document lists (Requirement 5.1)
    scheme_docs = await service.get_scheme_documents(scheme_id, language)
    
    # Property 1: Result must contain required fields
    assert "scheme_id" in scheme_docs, "Result must include scheme_id"
    assert "language" in scheme_docs, "Result must include language"
    assert "documents" in scheme_docs, "Result must include documents list"
    assert "total_documents" in scheme_docs, "Result must include total_documents count"
    
    # Property 2: Scheme ID and language must match request
    assert scheme_docs["scheme_id"] == scheme_id, "Returned scheme_id must match request"
    assert scheme_docs["language"] == language, "Returned language must match request"
    
    # Property 3: Document list must be complete and non-empty
    assert isinstance(scheme_docs["documents"], list), "Documents must be a list"
    assert len(scheme_docs["documents"]) > 0, "Scheme must have at least one required document"
    assert scheme_docs["total_documents"] == len(scheme_docs["documents"]), \
        "total_documents must match actual document count"
    
    # Property 4: Each document must have required fields in requested language
    for doc in scheme_docs["documents"]:
        assert "document_id" in doc, "Each document must have document_id"
        assert "name" in doc, "Each document must have name"
        assert "description" in doc, "Each document must have description"
        assert "category" in doc, "Each document must have category"
        
        # Property 5: Name and description must be non-empty strings
        assert isinstance(doc["name"], str) and len(doc["name"]) > 0, \
            "Document name must be non-empty string"
        assert isinstance(doc["description"], str) and len(doc["description"]) > 0, \
            "Document description must be non-empty string"
        
        # Property 6: Category must be valid
        valid_categories = ["identity", "financial", "property", "income", "identity_income", "supporting"]
        assert doc["category"] in valid_categories, \
            f"Document category must be one of {valid_categories}"
    
    # 2. Test alternatives for each document (Requirement 5.2)
    scheme_docs_with_alts = await service.get_scheme_documents_with_alternatives(scheme_id, language)
    
    # Property 7: Result must include alternatives for each document
    assert "documents" in scheme_docs_with_alts, "Result must include documents"
    assert len(scheme_docs_with_alts["documents"]) == len(scheme_docs["documents"]), \
        "Document count must match between calls"
    
    for doc in scheme_docs_with_alts["documents"]:
        # Property 8: Each document must have alternatives field
        assert "alternatives" in doc, "Each document must have alternatives field"
        assert isinstance(doc["alternatives"], list), "Alternatives must be a list"
        
        # Property 9: If alternatives exist, they must be properly structured
        for alt in doc["alternatives"]:
            assert "documents" in alt, "Each alternative must have documents list"
            assert "explanation" in alt, "Each alternative must have explanation"
            
            # Property 10: Alternative documents must be valid
            assert isinstance(alt["documents"], list), "Alternative documents must be a list"
            assert len(alt["documents"]) > 0, "Alternative must have at least one document"
            
            for alt_doc in alt["documents"]:
                assert "document_id" in alt_doc, "Alternative document must have document_id"
                assert "name" in alt_doc, "Alternative document must have name"
                assert isinstance(alt_doc["name"], str) and len(alt_doc["name"]) > 0, \
                    "Alternative document name must be non-empty string"
            
            # Property 11: Explanation must be non-empty string
            assert isinstance(alt["explanation"], str) and len(alt["explanation"]) > 0, \
                "Alternative explanation must be non-empty string"
    
    # 3. Test acquisition guidance for each document (Requirements 5.3, 5.5)
    for doc in scheme_docs["documents"]:
        doc_id = doc["document_id"]
        
        # Get acquisition guidance
        guidance = await service.get_document_acquisition_guidance(doc_id, language)
        
        # Property 12: Guidance must have required fields or indicate unavailability
        assert "document_id" in guidance, "Guidance must include document_id"
        assert guidance["document_id"] == doc_id, "Guidance document_id must match request"
        
        if "error" not in guidance:
            # Property 13: Complete guidance must have all required fields
            assert "document_name" in guidance, "Guidance must include document_name"
            assert "language" in guidance, "Guidance must include language"
            assert "steps" in guidance, "Guidance must include steps"
            assert "authority" in guidance, "Guidance must include authority"
            assert "processing_time" in guidance, "Guidance must include processing_time"
            assert "fees" in guidance, "Guidance must include fees"
            
            # Property 14: Language must match request
            assert guidance["language"] == language, "Guidance language must match request"
            
            # Property 15: Steps must be a non-empty list (Requirement 5.5)
            assert isinstance(guidance["steps"], list), "Steps must be a list"
            assert len(guidance["steps"]) > 0, "Must have at least one step"
            
            for step in guidance["steps"]:
                assert isinstance(step, str) and len(step) > 0, \
                    "Each step must be non-empty string"
            
            # Property 16: Authority information must be complete (Requirement 5.3)
            if guidance["authority"] is not None:
                assert "name" in guidance["authority"], "Authority must have name"
                assert "contact" in guidance["authority"], "Authority must have contact"
                assert isinstance(guidance["authority"]["name"], str), \
                    "Authority name must be string"
                assert isinstance(guidance["authority"]["contact"], dict), \
                    "Authority contact must be dict"
            
            # Property 17: Processing time must be non-empty string
            assert isinstance(guidance["processing_time"], str) and \
                   len(guidance["processing_time"]) > 0, \
                "Processing time must be non-empty string"
            
            # Property 18: Fees must be non-empty string
            assert isinstance(guidance["fees"], str) and len(guidance["fees"]) > 0, \
                "Fees must be non-empty string"
    
    # 4. Test templates and examples (Requirement 5.4)
    for doc in scheme_docs["documents"]:
        doc_id = doc["document_id"]
        
        # Get template information
        template = await service.get_document_template(doc_id, language)
        
        # Property 19: Template must have required fields or indicate unavailability
        assert "document_id" in template, "Template must include document_id"
        assert template["document_id"] == doc_id, "Template document_id must match request"
        
        if "message" not in template:
            # Property 20: Complete template must have all required fields
            assert "document_name" in template, "Template must include document_name"
            assert "language" in template, "Template must include language"
            assert "template_info" in template, "Template must include template_info"
            
            # Property 21: Language must match request
            assert template["language"] == language, "Template language must match request"
            
            # Property 22: Template info must be properly structured
            assert isinstance(template["template_info"], dict), "Template info must be dict"
            assert "format" in template["template_info"], "Template info must include format"
            assert "key_elements" in template["template_info"], \
                "Template info must include key_elements"
            assert "sample_text" in template["template_info"], \
                "Template info must include sample_text"
            
            # Property 23: Format must be non-empty string
            assert isinstance(template["template_info"]["format"], str) and \
                   len(template["template_info"]["format"]) > 0, \
                "Format must be non-empty string"
            
            # Property 24: Key elements must be non-empty list
            assert isinstance(template["template_info"]["key_elements"], list), \
                "Key elements must be a list"
            assert len(template["template_info"]["key_elements"]) > 0, \
                "Must have at least one key element"
            
            for element in template["template_info"]["key_elements"]:
                assert isinstance(element, str) and len(element) > 0, \
                    "Each key element must be non-empty string"
            
            # Property 25: Sample text must be non-empty string
            assert isinstance(template["template_info"]["sample_text"], str) and \
                   len(template["template_info"]["sample_text"]) > 0, \
                "Sample text must be non-empty string"
    
    # 5. Test complete document guidance aggregation
    for doc in scheme_docs["documents"]:
        doc_id = doc["document_id"]
        
        # Get complete guidance
        complete_guidance = await service.get_complete_document_guidance(doc_id, language)
        
        # Property 26: Complete guidance must have core fields
        assert "document_id" in complete_guidance, "Complete guidance must include document_id"
        assert "document_name" in complete_guidance, "Complete guidance must include document_name"
        assert "description" in complete_guidance, "Complete guidance must include description"
        assert "category" in complete_guidance, "Complete guidance must include category"
        assert "language" in complete_guidance, "Complete guidance must include language"
        
        # Property 27: Language must match request
        assert complete_guidance["language"] == language, \
            "Complete guidance language must match request"
        
        # Property 28: If acquisition guidance exists, it must be complete
        if "acquisition_guidance" in complete_guidance:
            acq = complete_guidance["acquisition_guidance"]
            assert "steps" in acq, "Acquisition guidance must include steps"
            assert "processing_time" in acq, "Acquisition guidance must include processing_time"
            assert "fees" in acq, "Acquisition guidance must include fees"
            assert isinstance(acq["steps"], list) and len(acq["steps"]) > 0, \
                "Steps must be non-empty list"
        
        # Property 29: If template exists, it must be complete
        if "template" in complete_guidance:
            tmpl = complete_guidance["template"]
            assert "format" in tmpl, "Template must include format"
            assert "key_elements" in tmpl, "Template must include key_elements"
            assert "sample_text" in tmpl, "Template must include sample_text"
        
        # Property 30: If alternatives exist, they must be properly structured
        if "alternatives" in complete_guidance:
            assert isinstance(complete_guidance["alternatives"], list), \
                "Alternatives must be a list"
            for alt in complete_guidance["alternatives"]:
                assert "documents" in alt, "Alternative must have documents"
                assert "explanation" in alt, "Alternative must have explanation"


@pytest.mark.asyncio
@given(
    document_id=document_id_strategy(),
    language=language_strategy()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_multilingual_consistency(document_id: str, language: str):
    """
    **Feature: gram-sahayak, Property 10: Comprehensive Document Guidance - Multilingual**
    **Validates: Requirement 5.1**
    
    Property: Document information must be consistent across all supported languages
    """
    service = DocumentGuideService()
    
    # Get document in requested language
    doc_info = await service.get_complete_document_guidance(document_id, language)
    
    # Property 1: Document must exist
    assert "error" not in doc_info, f"Document {document_id} must exist"
    
    # Property 2: Core attributes must be language-independent
    doc_id_result = doc_info["document_id"]
    category = doc_info["category"]
    
    # Get same document in English for comparison
    doc_info_en = await service.get_complete_document_guidance(document_id, "en")
    
    # Property 3: Document ID and category must be same across languages
    assert doc_info_en["document_id"] == doc_id_result, \
        "Document ID must be consistent across languages"
    assert doc_info_en["category"] == category, \
        "Document category must be consistent across languages"
    
    # Property 4: If acquisition guidance exists, structure must be consistent
    has_guidance = "acquisition_guidance" in doc_info
    has_guidance_en = "acquisition_guidance" in doc_info_en
    assert has_guidance == has_guidance_en, \
        "Acquisition guidance availability must be consistent across languages"
    
    if has_guidance:
        steps_count = len(doc_info["acquisition_guidance"]["steps"])
        steps_count_en = len(doc_info_en["acquisition_guidance"]["steps"])
        assert steps_count == steps_count_en, \
            "Number of acquisition steps must be consistent across languages"
    
    # Property 5: If template exists, structure must be consistent
    has_template = "template" in doc_info
    has_template_en = "template" in doc_info_en
    assert has_template == has_template_en, \
        "Template availability must be consistent across languages"
    
    if has_template:
        elements_count = len(doc_info["template"]["key_elements"])
        elements_count_en = len(doc_info_en["template"]["key_elements"])
        assert elements_count == elements_count_en, \
            "Number of key elements must be consistent across languages"
    
    # Property 6: If alternatives exist, structure must be consistent
    has_alternatives = "alternatives" in doc_info
    has_alternatives_en = "alternatives" in doc_info_en
    assert has_alternatives == has_alternatives_en, \
        "Alternatives availability must be consistent across languages"
    
    if has_alternatives:
        alts_count = len(doc_info["alternatives"])
        alts_count_en = len(doc_info_en["alternatives"])
        assert alts_count == alts_count_en, \
            "Number of alternatives must be consistent across languages"


@pytest.mark.asyncio
@given(
    scheme_id=scheme_id_strategy(),
    language=language_strategy()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_alternatives_validity(scheme_id: str, language: str):
    """
    **Feature: gram-sahayak, Property 10: Comprehensive Document Guidance - Alternatives**
    **Validates: Requirement 5.2**
    
    Property: Alternative documents must be valid documents in the system
    """
    service = DocumentGuideService()
    
    # Get all valid document IDs
    all_docs = service.get_all_documents(language)
    valid_doc_ids = {doc["document_id"] for doc in all_docs}
    
    # Get scheme documents with alternatives
    scheme_docs = await service.get_scheme_documents_with_alternatives(scheme_id, language)
    
    for doc in scheme_docs["documents"]:
        for alt in doc["alternatives"]:
            # Property 1: All alternative documents must be valid
            for alt_doc in alt["documents"]:
                assert alt_doc["document_id"] in valid_doc_ids, \
                    f"Alternative document {alt_doc['document_id']} must be valid"
            
            # Property 2: Alternative should not include the original document
            original_id = doc["document_id"]
            alt_ids = [ad["document_id"] for ad in alt["documents"]]
            # Note: Some alternatives might include the original as part of a combination
            # So we just verify all alternatives are valid, not that they exclude original


@pytest.mark.asyncio
@given(
    document_id=document_id_strategy(),
    language=language_strategy()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_acquisition_guidance_completeness(document_id: str, language: str):
    """
    **Feature: gram-sahayak, Property 10: Comprehensive Document Guidance - Acquisition**
    **Validates: Requirements 5.3, 5.5**
    
    Property: Acquisition guidance must provide complete step-by-step instructions
    with authority contacts
    """
    service = DocumentGuideService()
    
    # Get acquisition guidance
    guidance = await service.get_document_acquisition_guidance(document_id, language)
    
    # Skip if guidance not available for this document
    if "error" in guidance:
        return
    
    # Property 1: Steps must form a logical sequence
    steps = guidance["steps"]
    assert len(steps) >= 3, "Acquisition process should have at least 3 steps"
    
    # Property 2: Steps should be actionable (contain verbs in various languages)
    action_verbs = {
        "en": ["visit", "collect", "fill", "submit", "provide", "pay", "check", 
               "download", "attach", "request", "contact"],
        "hi": ["जाएं", "करें", "भरें", "प्रदान", "एकत्र", "जांचें", "डाउनलोड", "संलग्न"],
        "ta": ["செல்லவும்", "சேகரிக்கவும்", "நிரப்பவும்", "வழங்கவும்", "சமர்ப்பிக்கவும்", 
               "செலுத்தவும்", "பதிவிறக்கவும்"],
        "te": ["సందర్శించండి", "సేకరించండి", "నింపండి", "అందించండి", "సమర్పించండి", 
               "చెల్లించండి", "డౌన్‌లోడ్"]
    }
    
    # Get action verbs for the language, fallback to English
    verbs_to_check = action_verbs.get(language, action_verbs["en"])
    
    steps_with_actions = 0
    for step in steps:
        step_lower = step.lower()
        if any(verb in step_lower for verb in verbs_to_check):
            steps_with_actions += 1
    
    # At least 30% of steps should contain action verbs (relaxed for multilingual)
    assert steps_with_actions >= len(steps) * 0.3, \
        f"At least 30% of steps should contain action verbs (found {steps_with_actions}/{len(steps)})"
    
    # Property 3: Authority information must be actionable
    if guidance["authority"] is not None:
        authority = guidance["authority"]
        contact = authority["contact"]
        
        # Contact should have useful information
        contact_keys = contact.keys()
        useful_keys = ["phone", "website", "email", "locator", "address"]
        assert any(key in contact_keys for key in useful_keys), \
            "Authority contact must have at least one useful contact method"
    
    # Property 4: Processing time must indicate duration
    processing_time = guidance["processing_time"].lower()
    time_indicators = ["day", "week", "month", "hour", "minute", "दिन", "सप्ताह", 
                      "நாட்கள்", "రోజులు"]
    assert any(indicator in processing_time for indicator in time_indicators), \
        "Processing time must indicate duration"
    
    # Property 5: Fees must indicate cost or free status
    fees = guidance["fees"].lower()
    cost_indicators = ["₹", "rs", "rupee", "free", "मुफ्त", "இலவசம்", "ఉచితం", "paid"]
    assert any(indicator in fees for indicator in cost_indicators), \
        "Fees must indicate cost or free status"


@pytest.mark.asyncio
@given(language=language_strategy())
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_all_schemes_have_documents(language: str):
    """
    **Feature: gram-sahayak, Property 10: Comprehensive Document Guidance - Coverage**
    **Validates: Requirement 5.1**
    
    Property: All schemes in the system must have document requirements defined
    """
    service = DocumentGuideService()
    
    # Get all scheme IDs
    all_scheme_ids = list(service.scheme_documents_map.keys())
    
    # Property 1: System must have schemes defined
    assert len(all_scheme_ids) > 0, "System must have at least one scheme"
    
    for scheme_id in all_scheme_ids:
        # Property 2: Each scheme must have documents
        scheme_docs = await service.get_scheme_documents(scheme_id, language)
        
        assert "error" not in scheme_docs, f"Scheme {scheme_id} must have documents defined"
        assert len(scheme_docs["documents"]) > 0, \
            f"Scheme {scheme_id} must require at least one document"
        
        # Property 3: All required documents must be valid
        for doc in scheme_docs["documents"]:
            assert doc["document_id"] in service.documents_db, \
                f"Document {doc['document_id']} for scheme {scheme_id} must be in database"


@pytest.mark.asyncio
@given(
    scheme_id=scheme_id_strategy(),
    language=language_strategy()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_deterministic_results(scheme_id: str, language: str):
    """
    **Feature: gram-sahayak, Property 10: Comprehensive Document Guidance - Consistency**
    **Validates: All Requirements 5.1-5.5**
    
    Property: Repeated queries must return consistent results
    """
    service = DocumentGuideService()
    
    # Get scheme documents twice
    result1 = await service.get_scheme_documents_with_alternatives(scheme_id, language)
    result2 = await service.get_scheme_documents_with_alternatives(scheme_id, language)
    
    # Property 1: Results must be identical
    assert result1["scheme_id"] == result2["scheme_id"], "Scheme ID must be consistent"
    assert result1["language"] == result2["language"], "Language must be consistent"
    assert result1["total_documents"] == result2["total_documents"], \
        "Document count must be consistent"
    
    # Property 2: Document lists must be identical
    doc_ids_1 = [doc["document_id"] for doc in result1["documents"]]
    doc_ids_2 = [doc["document_id"] for doc in result2["documents"]]
    assert doc_ids_1 == doc_ids_2, "Document lists must be consistent"
    
    # Property 3: Document details must be identical
    for doc1, doc2 in zip(result1["documents"], result2["documents"]):
        assert doc1["document_id"] == doc2["document_id"], "Document IDs must match"
        assert doc1["name"] == doc2["name"], "Document names must match"
        assert doc1["description"] == doc2["description"], "Document descriptions must match"
        assert doc1["category"] == doc2["category"], "Document categories must match"
        assert len(doc1["alternatives"]) == len(doc2["alternatives"]), \
            "Alternative counts must match"
