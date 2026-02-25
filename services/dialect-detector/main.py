from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from dialect_detector_service import DialectDetectorService

app = FastAPI(title="Dialect Detector Service")
detector = DialectDetectorService()


class AudioFeatures(BaseModel):
    sample_rate: int
    channels: int
    bit_depth: int
    duration: float


class DialectResult(BaseModel):
    primary_dialect: str
    primary_language: str
    confidence: float
    alternative_dialects: List[dict]
    detection_time: float
    code_switching_detected: bool
    needs_clarification: bool
    clarification_prompt: Optional[str] = None


class FeedbackData(BaseModel):
    correct_dialect: Optional[str] = None
    user_satisfaction: int
    comments: Optional[str] = None


@app.post("/detect", response_model=DialectResult)
async def detect_dialect(audio_features: AudioFeatures):
    try:
        result = await detector.detect_dialect(audio_features.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback")
async def update_confidence(session_id: str, feedback: FeedbackData):
    try:
        await detector.update_confidence(session_id, feedback.dict())
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dialects")
async def get_supported_dialects():
    try:
        dialects = await detector.get_supported_dialects()
        return {"dialects": dialects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
