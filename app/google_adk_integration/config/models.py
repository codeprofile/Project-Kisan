# app/google_adk_integration/config/models.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    session_id: str
    agent_used: Optional[str] = None
    tools_called: Optional[List[str]] = None
    confidence: Optional[float] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())