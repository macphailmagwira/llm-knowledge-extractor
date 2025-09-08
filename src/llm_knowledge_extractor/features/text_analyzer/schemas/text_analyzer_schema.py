from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime


class TextAnalysisRequest(BaseModel):
    text: str
    
    @validator('text')
    def text_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Text cannot be empty')
        return v.strip()


class TextAnalysisResponse(BaseModel):
    id: int
    summary: str
    title: Optional[str]
    topics: List[str]
    sentiment: str
    keywords: List[str]
    confidence_score: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class TextAnalysisCreate(BaseModel):
    original_text: str
    summary: str
    title: Optional[str]
    topics: List[str]
    sentiment: str
    keywords: List[str]
    confidence_score: float


class SearchResponse(BaseModel):
    analyses: List[TextAnalysisResponse]
    total: int


class BatchTextRequest(BaseModel):
    texts: List[str]

class BatchSubmitResponse(BaseModel):
    batch_id: str
    message: str
    total_texts: int

class BatchResult(BaseModel):
    batch_id: str
    status: str  # "processing", "completed"
    successful: List[TextAnalysisResponse]
    failed: List[str]
    total: int
    success_count: int
    failure_count: int