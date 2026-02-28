from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from document_guide_service import DocumentGuideService
import os
import logging
import json
import re
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": "document-guide",
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

app = FastAPI(
    title="Document Guide Service",
    description="Document acquisition guidance and requirements for Gram Sahayak",
    version="1.0.0",
)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

guide = DocumentGuideService()


def sanitize_string(value: str) -> str:
    """Remove HTML tags and limit length for input sanitization."""
    if not value:
        return value
    clean = re.sub(r'<[^>]+>', '', value)
    return clean[:10000]


class DocumentRequest(BaseModel):
    scheme_id: str
    language: Optional[str] = "en"


class AlternativeRequest(BaseModel):
    document_id: str
    language: Optional[str] = "en"


@app.post("/documents/scheme")
async def get_scheme_documents(request: DocumentRequest):
    """
    Get complete list of required documents for a scheme in user's language
    Validates: Requirement 5.1
    """
    try:
        result = await guide.get_scheme_documents(request.scheme_id, request.language)
        return result
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/documents/alternatives")
async def get_document_alternatives(request: AlternativeRequest):
    """
    Get acceptable alternative documents for a specific document
    Validates: Requirement 5.2
    """
    try:
        result = await guide.get_document_alternatives(request.document_id, request.language)
        return result
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/documents/scheme/complete")
async def get_scheme_documents_with_alternatives(request: DocumentRequest):
    """
    Get complete document requirements with alternatives for a scheme
    Validates: Requirements 5.1, 5.2
    """
    try:
        result = await guide.get_scheme_documents_with_alternatives(
            request.scheme_id,
            request.language
        )
        return result
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/documents/languages")
async def get_supported_languages():
    """Get list of supported languages"""
    try:
        languages = guide.get_supported_languages()
        return {"languages": languages}
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/documents/all")
async def get_all_documents(language: str = "en"):
    """Get all documents in the database"""
    try:
        documents = guide.get_all_documents(language)
        return {"documents": documents, "language": language}
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "document-guide"}


class GuidanceRequest(BaseModel):
    document_id: str
    language: Optional[str] = "en"


class AuthorityRequest(BaseModel):
    authority_id: str
    language: Optional[str] = "en"


@app.post("/documents/acquisition-guidance")
async def get_document_acquisition_guidance(request: GuidanceRequest):
    """
    Get step-by-step guidance for obtaining a specific document
    Validates: Requirements 5.3, 5.5
    """
    try:
        result = await guide.get_document_acquisition_guidance(
            request.document_id,
            request.language
        )
        return result
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/documents/template")
async def get_document_template(request: GuidanceRequest):
    """
    Get template and example information for a specific document
    Validates: Requirement 5.4
    """
    try:
        result = await guide.get_document_template(
            request.document_id,
            request.language
        )
        return result
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/documents/complete-guidance")
async def get_complete_document_guidance(request: GuidanceRequest):
    """
    Get complete guidance including acquisition steps, authority contacts, and templates
    Validates: Requirements 5.3, 5.4, 5.5
    """
    try:
        result = await guide.get_complete_document_guidance(
            request.document_id,
            request.language
        )
        return result
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/authorities/contact")
async def get_authority_contact_info(request: AuthorityRequest):
    """
    Get contact information for a specific authority
    Validates: Requirement 5.3
    """
    try:
        result = await guide.get_authority_contact_info(
            request.authority_id,
            request.language
        )
        return result
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/authorities/all")
async def get_all_authorities(language: str = "en"):
    """Get list of all authorities with contact information"""
    try:
        authorities = guide.get_all_authorities(language)
        return {"authorities": authorities, "language": language}
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
