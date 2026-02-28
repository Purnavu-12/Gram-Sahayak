from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from dialect_detector_service import DialectDetectorService
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
            "service": "dialect-detector",
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

app = FastAPI(title="Dialect Detector Service")

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

detector = DialectDetectorService()


def sanitize_string(value: str) -> str:
    """Remove HTML tags and limit length for input sanitization."""
    if not value:
        return value
    clean = re.sub(r'<[^>]+>', '', value)
    return clean[:10000]


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
        result = await detector.detect_dialect(audio_features.model_dump())
        return result
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/feedback")
async def update_confidence(session_id: str, feedback: FeedbackData):
    try:
        await detector.update_confidence(session_id, feedback.model_dump())
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/dialects")
async def get_supported_dialects():
    try:
        dialects = await detector.get_supported_dialects()
        return {"dialects": dialects}
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
