from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from scheme_matcher_service import SchemeMatcherService
import os
import json

app = FastAPI(
    title="Scheme Matcher Service",
    description="Government scheme discovery and eligibility matching with optional Bedrock Knowledge Base integration",
    version="2.0.0",
)
matcher = SchemeMatcherService()

# Bedrock integration state
bedrock_enabled = os.getenv("BEDROCK_ENABLED", "false").lower() == "true"
bedrock_kb_id = os.getenv("BEDROCK_KB_ID", "")


class UserProfile(BaseModel):
    user_id: str
    personal_info: Dict[str, Any]
    demographics: Dict[str, Any]
    economic: Dict[str, Any]
    preferences: Dict[str, Any]
    application_history: List[Dict[str, Any]]


class SchemeMatch(BaseModel):
    scheme_id: str
    name: str
    match_score: float
    eligibility_status: str
    estimated_benefit: float
    application_difficulty: str
    reason: str
    source: Optional[str] = None


class UserPreferences(BaseModel):
    prioritize_benefit: bool
    prioritize_ease: bool
    exclude_categories: Optional[List[str]] = None


class KBSearchRequest(BaseModel):
    query: str
    language: str = "en"
    max_results: int = 3
    filters: Optional[Dict[str, Any]] = None


@app.post("/schemes/find", response_model=List[SchemeMatch])
async def find_eligible_schemes(profile: UserProfile):
    try:
        schemes = await matcher.find_eligible_schemes(profile.model_dump())
        # Add source field for backward compatibility
        for scheme in schemes:
            if "source" not in scheme:
                scheme["source"] = "neo4j"
        return schemes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/schemes/{scheme_id}/eligibility")
async def evaluate_eligibility(scheme_id: str, profile: UserProfile):
    try:
        result = await matcher.evaluate_eligibility(scheme_id, profile.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/schemes/rank")
async def get_priority_ranking(schemes: List[SchemeMatch], preferences: UserPreferences):
    try:
        ranked = await matcher.get_priority_ranking(
            [s.model_dump() for s in schemes],
            preferences.model_dump()
        )
        return ranked
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/schemes/{scheme_id}/alternatives")
async def suggest_alternative_schemes(scheme_id: str, profile: UserProfile):
    """
    Suggest alternative schemes when user is ineligible for requested scheme
    Validates: Requirement 3.5
    """
    try:
        alternatives = await matcher.suggest_alternative_schemes(
            profile.model_dump(),
            scheme_id
        )
        return alternatives
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/schemes/update")
async def update_scheme_database(updates: List[Dict[str, Any]]):
    """
    Update scheme database with new information
    Validates: Requirement 3.4
    """
    try:
        await matcher.update_scheme_database(updates)
        return {"status": "success", "updated_count": len(updates)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/schemes/status")
async def get_scheme_update_status():
    """
    Get information about recent scheme updates
    Validates: Requirement 3.4
    """
    try:
        status = matcher.get_scheme_update_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "scheme-matcher",
        "bedrock": {
            "enabled": bedrock_enabled,
            "knowledge_base_configured": bool(bedrock_kb_id),
        },
    }


@app.get("/bedrock/status")
async def bedrock_status():
    """Get Bedrock integration status for Scheme Matcher"""
    return {
        "enabled": bedrock_enabled,
        "knowledge_base_id": bedrock_kb_id or None,
        "search_mode": "hybrid" if bedrock_enabled else "neo4j_only",
    }


@app.post("/bedrock/toggle")
async def toggle_bedrock(enabled: bool = True):
    """Enable or disable Bedrock integration"""
    global bedrock_enabled
    bedrock_enabled = enabled
    return {"bedrock_enabled": bedrock_enabled}
