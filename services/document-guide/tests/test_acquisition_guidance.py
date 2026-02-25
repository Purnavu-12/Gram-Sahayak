"""
Unit tests for document acquisition guidance functionality
Validates: Requirements 5.3, 5.4, 5.5
"""

import pytest
from document_guide_service import DocumentGuideService


@pytest.fixture
def service():
    return DocumentGuideService()


@pytest.mark.asyncio
async def test_get_acquisition_guidance_aadhaar_english(service):
    """Test acquisition guidance for Aadhaar in English"""
    result = await service.get_document_acquisition_guidance("AADHAAR", "en")
    
    assert result["document_id"] == "AADHAAR"
    assert result["language"] == "en"
    assert "steps" in result
    assert len(result["steps"]) > 0
    assert "authority" in result
    assert "processing_time" in result
    assert "fees" in result
    assert "Visit nearest Aadhaar Enrollment Center" in result["steps"][0]


@pytest.mark.asyncio
async def test_get_acquisition_guidance_income_cert_hindi(service):
    """Test acquisition guidance for Income Certificate in Hindi"""
    result = await service.get_document_acquisition_guidance("INCOME_CERTIFICATE", "hi")
    
    assert result["document_id"] == "INCOME_CERTIFICATE"
    assert result["language"] == "hi"
    assert "steps" in result
    assert len(result["steps"]) > 0
    assert "तहसील" in result["steps"][0]


@pytest.mark.asyncio
async def test_get_acquisition_guidance_caste_cert_tamil(service):
    """Test acquisition guidance for Caste Certificate in Tamil"""
    result = await service.get_document_acquisition_guidance("CASTE_CERTIFICATE", "ta")
    
    assert result["document_id"] == "CASTE_CERTIFICATE"
    assert result["language"] == "ta"
    assert "steps" in result
    assert len(result["steps"]) > 0


@pytest.mark.asyncio
async def test_get_acquisition_guidance_land_records_telugu(service):
    """Test acquisition guidance for Land Records in Telugu"""
    result = await service.get_document_acquisition_guidance("LAND_RECORDS", "te")
    
    assert result["document_id"] == "LAND_RECORDS"
    assert result["language"] == "te"
    assert "steps" in result
    assert len(result["steps"]) > 0


@pytest.mark.asyncio
async def test_get_acquisition_guidance_invalid_document(service):
    """Test acquisition guidance for invalid document"""
    result = await service.get_document_acquisition_guidance("INVALID_DOC", "en")
    
    assert "error" in result
    assert result["document_id"] == "INVALID_DOC"


@pytest.mark.asyncio
async def test_get_authority_contact_uidai(service):
    """Test getting UIDAI center contact information"""
    result = await service.get_authority_contact_info("UIDAI_CENTER", "en")
    
    assert result["authority_id"] == "UIDAI_CENTER"
    assert result["language"] == "en"
    assert "contact_info" in result
    assert "phone" in result["contact_info"]
    assert "website" in result["contact_info"]
    assert "1947" in result["contact_info"]["phone"]


@pytest.mark.asyncio
async def test_get_authority_contact_tehsil_hindi(service):
    """Test getting Tehsil office contact information in Hindi"""
    result = await service.get_authority_contact_info("TEHSIL_OFFICE", "hi")
    
    assert result["authority_id"] == "TEHSIL_OFFICE"
    assert result["language"] == "hi"
    assert "contact_info" in result
    assert "तहसील" in result["name"]


@pytest.mark.asyncio
async def test_get_authority_contact_invalid(service):
    """Test getting invalid authority contact information"""
    result = await service.get_authority_contact_info("INVALID_AUTH", "en")
    
    assert "error" in result
    assert result["authority_id"] == "INVALID_AUTH"


@pytest.mark.asyncio
async def test_get_document_template_income_cert(service):
    """Test getting Income Certificate template"""
    result = await service.get_document_template("INCOME_CERTIFICATE", "en")
    
    assert result["document_id"] == "INCOME_CERTIFICATE"
    assert result["language"] == "en"
    assert "template_info" in result
    assert "format" in result["template_info"]
    assert "key_elements" in result["template_info"]
    assert "sample_text" in result["template_info"]
    assert len(result["template_info"]["key_elements"]) > 0


@pytest.mark.asyncio
async def test_get_document_template_caste_cert_hindi(service):
    """Test getting Caste Certificate template in Hindi"""
    result = await service.get_document_template("CASTE_CERTIFICATE", "hi")
    
    assert result["document_id"] == "CASTE_CERTIFICATE"
    assert result["language"] == "hi"
    assert "template_info" in result
    assert "जाति" in result["template_info"]["sample_text"]


@pytest.mark.asyncio
async def test_get_document_template_invalid(service):
    """Test getting template for document without template"""
    result = await service.get_document_template("AADHAAR", "en")
    
    assert "message" in result
    assert result["document_id"] == "AADHAAR"


@pytest.mark.asyncio
async def test_get_complete_guidance_income_cert(service):
    """Test getting complete guidance for Income Certificate"""
    result = await service.get_complete_document_guidance("INCOME_CERTIFICATE", "en")
    
    assert result["document_id"] == "INCOME_CERTIFICATE"
    assert result["language"] == "en"
    assert "document_name" in result
    assert "description" in result
    assert "category" in result
    assert "acquisition_guidance" in result
    assert "template" in result
    assert "alternatives" in result
    
    # Check acquisition guidance structure
    assert "steps" in result["acquisition_guidance"]
    assert "authority" in result["acquisition_guidance"]
    assert "processing_time" in result["acquisition_guidance"]
    assert "fees" in result["acquisition_guidance"]


@pytest.mark.asyncio
async def test_get_complete_guidance_aadhaar(service):
    """Test getting complete guidance for Aadhaar (has guidance but no template)"""
    result = await service.get_complete_document_guidance("AADHAAR", "en")
    
    assert result["document_id"] == "AADHAAR"
    assert "acquisition_guidance" in result
    assert "template" not in result  # Aadhaar doesn't have template
    assert "alternatives" in result


@pytest.mark.asyncio
async def test_get_complete_guidance_invalid_document(service):
    """Test getting complete guidance for invalid document"""
    result = await service.get_complete_document_guidance("INVALID_DOC", "en")
    
    assert "error" in result
    assert result["document_id"] == "INVALID_DOC"


@pytest.mark.asyncio
async def test_get_all_authorities(service):
    """Test getting all authorities"""
    authorities = service.get_all_authorities("en")
    
    assert len(authorities) > 0
    assert any(auth["authority_id"] == "UIDAI_CENTER" for auth in authorities)
    assert any(auth["authority_id"] == "TEHSIL_OFFICE" for auth in authorities)
    
    for auth in authorities:
        assert "authority_id" in auth
        assert "name" in auth
        assert "contact_info" in auth


@pytest.mark.asyncio
async def test_authority_info_in_acquisition_guidance(service):
    """Test that acquisition guidance includes authority information"""
    result = await service.get_document_acquisition_guidance("INCOME_CERTIFICATE", "en")
    
    assert "authority" in result
    assert result["authority"] is not None
    assert "name" in result["authority"]
    assert "contact" in result["authority"]
    assert "phone" in result["authority"]["contact"]


@pytest.mark.asyncio
async def test_processing_time_and_fees_included(service):
    """Test that processing time and fees are included in guidance"""
    result = await service.get_document_acquisition_guidance("CASTE_CERTIFICATE", "en")
    
    assert "processing_time" in result
    assert "fees" in result
    assert "days" in result["processing_time"].lower()
    assert "₹" in result["fees"] or "free" in result["fees"].lower()


@pytest.mark.asyncio
async def test_multilingual_template_support(service):
    """Test that templates support multiple languages"""
    languages = ["en", "hi", "ta", "te"]
    
    for lang in languages:
        result = await service.get_document_template("INCOME_CERTIFICATE", lang)
        assert result["language"] == lang
        assert "template_info" in result
        assert "key_elements" in result["template_info"]
        assert len(result["template_info"]["key_elements"]) > 0
