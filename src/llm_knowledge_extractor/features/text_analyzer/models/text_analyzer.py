
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float
from sqlalchemy.sql import func
from llm_knowledge_extractor.common.db.base import Base


class TextAnalysis(Base):
    __tablename__ = "text_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    title = Column(String(255), nullable=True)
    topics = Column(JSON, nullable=False)  
    sentiment = Column(String(50), nullable=False)
    keywords = Column(JSON, nullable=False) 
    confidence_score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())