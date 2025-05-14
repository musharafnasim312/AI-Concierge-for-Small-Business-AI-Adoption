from pydantic import BaseModel
from typing import Optional, List, Dict

class ChatMessage(BaseModel):
    """Chat message request model"""
    message: str
    stream: bool = False

class Source(BaseModel):
    """Source citation model"""
    source: str
    content: str
    page: Optional[str] = None

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    sources: Optional[List[Source]] = None
    feedback_score: Optional[float] = None

class FeedbackResponse(BaseModel):
    """Feedback response model"""
    status: str
    new_score: float
