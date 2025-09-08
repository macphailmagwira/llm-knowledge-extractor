from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from llm_knowledge_extractor.features.text_analyzer.daos.text_analyzer_dao import AnalysisDAO
from llm_knowledge_extractor.features.text_analyzer.schemas.text_analyzer_schema import (
    TextAnalysisCreate, 
    TextAnalysisResponse,
    SearchResponse
)
import json
from llm_knowledge_extractor.core.config import settings
from llm_knowledge_extractor.llm_clients.azure.azure_llm_client import AzureLLMClient
from llm_knowledge_extractor.features.text_analyzer.prompts.text_analysis_prompt import text_analysis_prompt, system_prompt
from llm_knowledge_extractor.features.text_analyzer.utils.noun_extractor import NounExtractor
from llm_knowledge_extractor.common.utils.get_logger import get_logger
logger = get_logger() 

class AnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dao = AnalysisDAO(db)
        self.azure_llm_client = AzureLLMClient(model="gpt4o")
        self.noun_extractor = NounExtractor()

    def _calculate_confidence_score(self, text: str, llm_result: dict, keywords: List[str]) -> float:
        """
        Calculate a simple confidence score based on basic checks.
        
        Args:
            text: Original text
            llm_result: LLM analysis result
            keywords: Extracted keywords
            
        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        score = 0.0
        
        try:
            # Text length (25% of score)
            if len(text) > 100:
                score += 0.25
            elif len(text) > 50:
                score += 0.15
            else:
                score += 0.1
            
            # Has summary (25% of score)
            if llm_result.get("summary") and len(str(llm_result["summary"]).strip()) > 10:
                score += 0.25
            
            # Has topics (25% of score)
            topics = llm_result.get("topics", [])
            if topics and len(topics) > 0:
                score += 0.25
            
            # Has keywords (25% of score)
            if keywords and len(keywords) > 0:
                score += 0.25
            
            # Ensure score is between 0.0 and 1.0
            score = max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {str(e)}")
            score = 0.5  
            
        return round(score, 2)    

    async def analyze_text(self, text: str) -> TextAnalysisResponse:
        """
        Analyze text using LLM, then store the results.
        
        Args:
            text: The text to analyze
            
        Returns:
            TextAnalysisResponse with the analysis results
            
        Raises:
            ValueError: If text is empty
            Exception: If LLM analysis fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        try:
            # Get LLM analysis
            text_analysis_prompt_formatted = text_analysis_prompt.format(text=text)
            response = await self.azure_llm_client.call_llm(prompt=text_analysis_prompt_formatted, system_prompt=system_prompt, response_format="json")
            llm_result = json.loads(response)
            logger.debug(f"LLM result: {llm_result}")
            keywords = self.noun_extractor.extract_keywords(text)
            logger.debug(f"Keywords: {keywords}")
            confidence_score = self._calculate_confidence_score(text, llm_result, keywords)
            logger.debug(f"Confidence score: {confidence_score}")
            
            # Create analysis record
            analysis_data = TextAnalysisCreate(
                original_text=text,
                summary=llm_result.get("summary", "No summary available"),
                title=llm_result.get("title"),
                topics=llm_result.get("topics", []),
                sentiment=llm_result.get("sentiment", "neutral"),
                keywords=keywords,
                confidence_score=confidence_score)
            
            # Store in database
            db_analysis = await self.dao.create_analysis(analysis_data)
            
            return TextAnalysisResponse.from_orm(db_analysis)
            
        except Exception as e:
            logger.error(f"Failed to analyze text: {str(e)}")
            raise Exception(f"Analysis failed: {str(e)}")

    async def get_analysis(self, analysis_id: int) -> Optional[TextAnalysisResponse]:
        """Get an analysis by ID."""
        analysis = await self.dao.get_analysis_by_id(analysis_id)
       
        if analysis:
            logger.debug(f"Analysis found: {analysis}")
            return TextAnalysisResponse.from_orm(analysis)
        return None

    async def search_analyses(
        self, 
        topic: Optional[str] = None, 
        keyword: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> SearchResponse:
        """
        Search analyses by topic or keyword.
        
        Args:
            topic: Topic to search for
            keyword: Keyword to search for
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            SearchResponse with matching analyses
        """
        if not topic and not keyword:
           analyses, total = await self.dao.get_all_analyses(limit=limit, offset=offset)
        else:
            logger.debug(f"Searching for analyses with topic: {topic} and keyword: {keyword}")
            analyses, total = await self.dao.search_analyses(
                topic=topic, 
                keyword=keyword, 
                limit=limit, 
                offset=offset
            )
            logger.debug(f"Found {total} analyses")
        
        analysis_responses = [
            TextAnalysisResponse.from_orm(analysis) 
            for analysis in analyses
        ]
        
        return SearchResponse(analyses=analysis_responses, total=total)