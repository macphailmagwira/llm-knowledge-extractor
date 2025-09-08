from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime
import time
from pathlib import Path

from llm_knowledge_extractor.core.config import settings
from llm_knowledge_extractor.features.text_analyzer.schemas.text_analyzer_schema import (
    TextAnalysisRequest,
    TextAnalysisResponse,
    SearchResponse,
    BatchTextRequest,
    BatchSubmitResponse,
    BatchResult 
)

from sqlalchemy.ext.asyncio import AsyncSession
from llm_knowledge_extractor.common.db.session import get_async_db
from llm_knowledge_extractor.features.text_analyzer.services.analysis_service import AnalysisService
from llm_knowledge_extractor.common.utils.get_logger import get_logger
logger = get_logger() 


router = APIRouter()


batch_results: Dict[str, Dict[str, Any]] = {} # in memory storage



@router.post("/analyze", response_model=TextAnalysisResponse)
async def analyze_text(
    request: TextAnalysisRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Analyze text and extract summary, topics, sentiment, and keywords.
    
    This endpoint:
    1. Takes unstructured text input
    2. Uses Azure OpenAI to generate summary, extract title, topics, and sentiment
    3. Extracts the 3 most frequent nouns as keywords using NLTK
    4. Stores the analysis in the database
    5. Returns the complete analysis
    """
    try:
        service = AnalysisService(db)
        result = await service.analyze_text(request.text)
        logger.info("Successfully analyzed text")
        logger.debug(f"Analysis result: {result}")

        return result
    except ValueError as e:
        logger.error(f"Failed to analyze text: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to analyze text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=SearchResponse)
async def search_analyses(
    topic: Optional[str] = Query(None, description="Search by topic"),
    keyword: Optional[str] = Query(None, description="Search by keyword (searches in keywords, title, and summary)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Search stored analyses by topic or keyword.
    
    - **topic**: Search for analyses containing this topic
    - **keyword**: Search for analyses containing this keyword in keywords, title, or summary
    - If neither topic nor keyword is provided, returns all analyses
    - Results are paginated and ordered by creation date (newest first)
    """
    try:
        service = AnalysisService(db)
        result = await service.search_analyses(
            topic=topic,
            keyword=keyword,
            limit=limit,
            offset=offset
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{analysis_id}", response_model=TextAnalysisResponse)
async def get_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific analysis by ID."""
    try:
        service = AnalysisService(db)
        result = await service.get_analysis(analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@router.post("/batch/analyze", response_model=BatchSubmitResponse)
async def batch_analyze_texts(
    request: BatchTextRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Submit texts for batch analysis. Returns immediately with batch_id.
    """
    batch_id = str(uuid.uuid4())
    
    batch_results[batch_id] = {
        "status": "processing",
        "successful": [],
        "failed": [],
        "total": len(request.texts),
        "created_at": datetime.utcnow()
    }
    
    background_tasks.add_task(process_batch, batch_id, request.texts, db)
    
    return BatchSubmitResponse(
        batch_id=batch_id,
        message="Batch processing started",
        total_texts=len(request.texts)
    )


@router.get("/batch/{batch_id}", response_model=BatchResult)
async def get_batch_results(batch_id: str):
    """
    Get results of a batch analysis.
    """
    if batch_id not in batch_results:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    result = batch_results[batch_id]
    
    return BatchResult(
        batch_id=batch_id,
        status=result["status"],
        successful=result["successful"],
        failed=result["failed"],
        total=result["total"],
        success_count=len(result["successful"]),
        failure_count=len(result["failed"])
    )

# Background processing
async def process_batch(batch_id: str, texts: List[str], db: AsyncSession):
    """Process batch in background"""
    service = AnalysisService(db)
    
    for text in texts:
        try:
            if not text.strip():
                batch_results[batch_id]["failed"].append("Empty text")
                continue
                
            result = await service.analyze_text(text)
            batch_results[batch_id]["successful"].append(result)
            
        except Exception as e:
            batch_results[batch_id]["failed"].append(f"Text '{text[:50]}...': {str(e)}")
    
    batch_results[batch_id]["status"] = "completed"