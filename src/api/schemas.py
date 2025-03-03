from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ContentMetadata(BaseModel):
    source: Optional[str] = None
    timestamp: datetime = None

class AnalysisRequest(BaseModel):
    content: Optional[str] = None
    url: Optional[str] = None
    models: List[str] = []

class PoliticalSentiment(BaseModel):
    score: float = Field(..., ge=1, le=100, description="Political leaning score (1=Left, 100=Right)")
    label: str = Field(..., description="LEFT, RIGHT, or CENTER")
    confidence: float = Field(..., ge=0, le=1)

class EmotionalContext(BaseModel):
    primary_emotion: str
    confidence: float
    secondary_emotions: List[Dict[str, float]]

class ToneAnalysis(BaseModel):
    tone: str
    confidence: float

class ContextualAnalysis(BaseModel):
    emotions: EmotionalContext
    tone: ToneAnalysis

class FullAnalysisResponse(BaseModel):
    political_sentiment: PoliticalSentiment
    context: ContextualAnalysis
    metadata: Dict[str, Any]

class AnalysisResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    results: Optional[FullAnalysisResponse] = None
    error: Optional[str] = None

class SourceAnalysis(BaseModel):
    domain: str
    score: float

class ModelComparison(BaseModel):
    models: List[str]
    results: Dict[str, Dict[str, Any]] 