from pydantic import BaseModel
from typing import Optional

class VoiceRequest(BaseModel):
    """Voice request model"""
    audio_format: str = "wav"
    language: str = "en-US"

class TranscriptionResult(BaseModel):
    """Speech-to-text result model"""
    text: str
    confidence: Optional[float] = None

class VoiceResponse(BaseModel):
    """Voice response model"""
    audio_format: str = "wav"
    text_content: str
    duration_ms: Optional[int] = None
