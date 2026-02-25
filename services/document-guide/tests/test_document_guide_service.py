import pytest
from document_guide_service import DocumentGuideService


@pytest.fixture
def service():
    return DocumentGuideService()


@pytest.mark.asyncio
async def test_get_scheme_documents_pm_kisan_english(service):
    """Test getting PM-KISAN documents in English"""
    result = await service.get_scheme_documents("PM-KISAN", "en")
    
    assert result["scheme_id"] == "PM-KISAN"
    assert result["language"] == "en"
    assert result["total_documents"] == 3
    assert len(result["documents"]) == 3
    
    # Check for required documents
    doc_ids = [doc["document_id"] for doc in result["documents"]]
    assert "AADHAAR" in doc_ids
    assert "LAND_RECORDS" in doc_ids
    assert "BANK_PASSBOOK" in doc_ids


@pytest.mark.asyncio
async def test_get_scheme_documents_pm_kisan_hindi(service):
    """Test getting PM-KISAN documents in Hindi"""
    result = await service.get_scheme_documents("PM-KISAN", "hi")
    
    assert result["scheme_id"] == "PM-KISAN"
    assert result["language"] == "hi"
    assert result["total_documents"] == 3
    
    # Check that Hindi names are returned
    aadhaar_doc = next(doc for doc in result["documents"] if doc["document_id"] == "AADHAAR")
    assert aadhaar_doc["name"] == "आधार कार्ड"


@pytest.mark.asyncio
async def test_get_scheme_documents_invalid_scheme(service):
    """Test getting documents for non-existent scheme"""
    result = await service.get_scheme_documents("INVALID-SCHEME", "en")
    
    assert "error" in result
    assert result["documents"] == []


@pytest.mark.asyncio
async def test_get_document_alternatives_aadhaar(service):
    """Test getting alternatives for Aadhaar"""
    result = await service.get_document_alternatives("AADHAAR", "en")
    
    assert result["document_id"] == "AADHAAR"
    assert result["language"] == "en"
    assert len(result["alternatives"]) > 0
    
    # Check first alternative
    first_alt = result["alternatives"][0]
    assert "documents" in first_alt
    assert "explanation" in first_alt
    assert len(first_alt["documents"]) == 2  # VOTER_ID and RATION_CARD


@pytest.mark.asyncio
async def test_get_document_alternatives_hindi(service):
    """Test getting alternatives in Hindi"""
    result = await service.get_document_alternatives("AADHAAR", "hi")
    
    assert result["language"] == "hi"
    assert "यदि आधार उपलब्ध नहीं है" in result["alternatives"][0]["explanation"]


@pytest.mark.asyncio
async def test_get_document_alternatives_no_alternatives(service):
    """Test getting alternatives for document with no alternatives"""
    result = await service.get_document_alternatives("PASSPORT_PHOTO", "en")
    
    assert result["document_id"] == "PASSPORT_PHOTO"
    assert result["alternatives"] == []


@pytest.mark.asyncio
async def test_get_scheme_documents_with_alternatives(service):
    """Test getting complete scheme documents with alternatives"""
    result = await service.get_scheme_documents_with_alternatives("PM-KISAN", "en")
    
    assert result["scheme_id"] == "PM-KISAN"
    assert result["total_documents"] == 3
    
    # Check that each document has alternatives field
    for doc in result["documents"]:
        assert "alternatives" in doc
        if doc["document_id"] == "AADHAAR":
            assert len(doc["alternatives"]) > 0


@pytest.mark.asyncio
async def test_get_scheme_documents_mgnrega(service):
    """Test getting MGNREGA documents"""
    result = await service.get_scheme_documents("MGNREGA", "en")
    
    assert result["scheme_id"] == "MGNREGA"
    assert result["total_documents"] == 3
    
    doc_ids = [doc["document_id"] for doc in result["documents"]]
    assert "AADHAAR" in doc_ids
    assert "BANK_PASSBOOK" in doc_ids
    assert "PASSPORT_PHOTO" in doc_ids


@pytest.mark.asyncio
async def test_get_scheme_documents_scholarship(service):
    """Test getting scholarship documents"""
    result = await service.get_scheme_documents("SC-ST-SCHOLARSHIP", "en")
    
    assert result["scheme_id"] == "SC-ST-SCHOLARSHIP"
    assert result["total_documents"] == 5
    
    doc_ids = [doc["document_id"] for doc in result["documents"]]
    assert "AADHAAR" in doc_ids
    assert "CASTE_CERTIFICATE" in doc_ids
    assert "BANK_PASSBOOK" in doc_ids
    assert "INCOME_CERTIFICATE" in doc_ids
    assert "PASSPORT_PHOTO" in doc_ids


def test_get_supported_languages(service):
    """Test getting supported languages"""
    languages = service.get_supported_languages()
    
    assert "en" in languages
    assert "hi" in languages
    assert "ta" in languages
    assert "te" in languages
    assert len(languages) == 10


def test_get_all_documents_english(service):
    """Test getting all documents in English"""
    documents = service.get_all_documents("en")
    
    assert len(documents) > 0
    assert all("document_id" in doc for doc in documents)
    assert all("name" in doc for doc in documents)
    assert all("description" in doc for doc in documents)
    assert all("category" in doc for doc in documents)


def test_get_all_documents_tamil(service):
    """Test getting all documents in Tamil"""
    documents = service.get_all_documents("ta")
    
    aadhaar_doc = next(doc for doc in documents if doc["document_id"] == "AADHAAR")
    assert aadhaar_doc["name"] == "ஆதார் அட்டை"


@pytest.mark.asyncio
async def test_multilingual_support_all_languages(service):
    """Test that all supported languages work for document retrieval"""
    languages = ["en", "hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa"]
    
    for lang in languages:
        result = await service.get_scheme_documents("PM-KISAN", lang)
        assert result["language"] == lang
        assert result["total_documents"] == 3
        assert all("name" in doc for doc in result["documents"])


@pytest.mark.asyncio
async def test_document_categories(service):
    """Test that documents have correct categories"""
    all_docs = service.get_all_documents("en")
    
    # Check specific document categories
    aadhaar = next(doc for doc in all_docs if doc["document_id"] == "AADHAAR")
    assert aadhaar["category"] == "identity"
    
    bank = next(doc for doc in all_docs if doc["document_id"] == "BANK_PASSBOOK")
    assert bank["category"] == "financial"
    
    land = next(doc for doc in all_docs if doc["document_id"] == "LAND_RECORDS")
    assert land["category"] == "property"
