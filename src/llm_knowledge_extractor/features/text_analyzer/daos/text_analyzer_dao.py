from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.sql import func
from llm_knowledge_extractor.features.text_analyzer.models.text_analyzer import TextAnalysis
from llm_knowledge_extractor.features.text_analyzer.schemas.text_analyzer_schema import TextAnalysisCreate
import json
import sqlalchemy



class AnalysisDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_analysis(self, analysis_data: TextAnalysisCreate) -> TextAnalysis:
        """Create a new text analysis record."""
        db_analysis = TextAnalysis(
            original_text=analysis_data.original_text,
            summary=analysis_data.summary,
            title=analysis_data.title,
            topics=analysis_data.topics,
            sentiment=analysis_data.sentiment,
            confidence_score=analysis_data.confidence_score,
            keywords=analysis_data.keywords
        )
        
        self.db.add(db_analysis)
        await self.db.commit()
        await self.db.refresh(db_analysis)
        return db_analysis

    async def get_analysis_by_id(self, analysis_id: int) -> Optional[TextAnalysis]:
        """Get an analysis by ID."""
        result = await self.db.execute(
            select(TextAnalysis).where(TextAnalysis.id == analysis_id)
        )
        return result.scalar_one_or_none()

    async def search_analyses(
        self, 
        topic: Optional[str] = None, 
        keyword: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[TextAnalysis], int]:
        """
        Search analyses by topic or keyword.
        
        Returns:
            Tuple of (analyses, total_count)
        """
        query = select(TextAnalysis)
        count_query = select(func.count(TextAnalysis.id))
        
        conditions = []
        
        if topic:
            # Search in topics JSON array
            conditions.append(
                func.cast(TextAnalysis.topics, sqlalchemy.Text).like(f'%{topic}%')
            )
            
        if keyword:
            # Search in keywords JSON array
            conditions.append(
                or_(
                    func.cast(TextAnalysis.keywords, sqlalchemy.Text).like(f'%{keyword.lower()}%'))
            )
        
        if conditions:
            filter_condition = and_(*conditions) if len(conditions) > 1 else conditions[0]
            query = query.where(filter_condition)
            count_query = count_query.where(filter_condition)
        
        # total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        #paginated results
        query = query.order_by(TextAnalysis.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        analyses = result.scalars().all()
        
        return list(analyses), total

    async def get_all_analyses(self, limit: int = 50, offset: int = 0) -> tuple[List[TextAnalysis], int]:
        """Get all analyses with pagination."""
        # Get total count
        count_result = await self.db.execute(select(func.count(TextAnalysis.id)))
        total = count_result.scalar()
        
        # Get paginated results
        result = await self.db.execute(
            select(TextAnalysis)
            .order_by(TextAnalysis.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        analyses = result.scalars().all()
        
        return list(analyses), total