import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, patch, MagicMock
import json

from llm_knowledge_extractor.features.text_analyzer.api.v1.text_analyzer_api import router

app = FastAPI()
app.include_router(router)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_analysis_db_object():
    """Mock database object returned by DAO"""
    mock_obj = MagicMock()
    mock_obj.id = 1
    mock_obj.original_text = "Test text"
    mock_obj.summary = "Test summary"
    mock_obj.title = "Test title"
    mock_obj.topics = ["test"]
    mock_obj.sentiment = "positive"
    mock_obj.keywords = ["test", "keyword"]
    mock_obj.confidence_score = 0.75
    mock_obj.created_at = "2025-01-01T00:00:00Z"
    mock_obj.updated_at = "2025-01-01T00:00:00Z"
    return mock_obj

class TestAnalyzeEndpoint:
    
    @patch('llm_knowledge_extractor.features.text_analyzer.services.analysis_service.AzureLLMClient')
    @patch('llm_knowledge_extractor.features.text_analyzer.services.analysis_service.AnalysisDAO')
    @patch('llm_knowledge_extractor.features.text_analyzer.api.v1.text_analyzer_api.get_async_db')
    def test_analyze_success(self, mock_get_db, mock_dao_class, mock_llm_class, client, mock_analysis_db_object):
        # Mock database
        mock_get_db.return_value = AsyncMock()
        
        # Mock DAO
        mock_dao = AsyncMock()
        mock_dao.create_analysis.return_value = mock_analysis_db_object
        mock_dao_class.return_value = mock_dao
        
        # Mock LLM response
        mock_llm = AsyncMock()
        llm_response = json.dumps({
            "summary": "Test summary",
            "title": "Test title", 
            "topics": ["test"],
            "sentiment": "positive"
        })
        mock_llm.call_llm.return_value = llm_response
        mock_llm_class.return_value = mock_llm
        
        test_text = "The system processes a database using an algorithm. Data flows through the server network efficiently."
        
        from llm_knowledge_extractor.features.text_analyzer.utils.noun_extractor import NounExtractor
        noun_extractor = NounExtractor()
        actual_keywords = noun_extractor.extract_keywords(test_text, top_k=3)
        
        with patch('llm_knowledge_extractor.features.text_analyzer.schemas.text_analyzer_schema.TextAnalysisResponse.from_orm') as mock_from_orm:
            from llm_knowledge_extractor.features.text_analyzer.schemas.text_analyzer_schema import TextAnalysisResponse
            
            expected_response = TextAnalysisResponse(
                id=1,
                original_text=test_text,
                summary="Test summary",
                title="Test title",
                topics=["test"],
                sentiment="positive",
                keywords=actual_keywords,
                confidence_score=0.75,
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-01T00:00:00Z"
            )
            mock_from_orm.return_value = expected_response
            
          
            response = client.post("/analyze", json={"text": test_text})
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["id"] == 1
            assert response_data["summary"] == "Test summary"
            assert response_data["title"] == "Test title"
            assert response_data["topics"] == ["test"]
            assert response_data["sentiment"] == "positive"
            
            keywords = response_data["keywords"]
            assert isinstance(keywords, list)
            assert len(keywords) > 0
            assert len(keywords) <= 3  # default top_k=3
            
            assert keywords == actual_keywords, f"Expected keywords {actual_keywords}, got {keywords}"
            assert response_data["confidence_score"] == 0.75

            
            expected_keyword_candidates = ["system", "database", "algorithm", "data", "server", "network"]
            assert any(keyword in expected_keyword_candidates for keyword in keywords), \
                f"No expected keywords found. Got: {keywords}, Expected candidates: {expected_keyword_candidates}"
            
            mock_llm.call_llm.assert_called_once()
            mock_dao.create_analysis.assert_called_once()
            
            call_args = mock_dao.create_analysis.call_args[0][0]  #TextAnalysisCreate object
            assert hasattr(call_args, 'keywords')
            assert call_args.keywords == actual_keywords
    
    @patch('llm_knowledge_extractor.features.text_analyzer.api.v1.text_analyzer_api.get_async_db')
    def test_analyze_empty_text(self, mock_get_db, client):
        # Arrange
        mock_get_db.return_value = AsyncMock()
        
        # Act - Send valid JSON but with empty text (will be caught by Pydantic validation)
        response = client.post("/analyze", json={"text": "   "})  # whitespace-only text
        
        # Assert - Pydantic validation should return 422 for invalid input
        assert response.status_code == 422
        response_data = response.json()
        assert "detail" in response_data
        assert any("Text cannot be empty" in str(error) for error in response_data["detail"])

class TestGetAnalysisEndpoint:
    
    @patch('llm_knowledge_extractor.features.text_analyzer.services.analysis_service.AnalysisDAO')
    @patch('llm_knowledge_extractor.features.text_analyzer.api.v1.text_analyzer_api.get_async_db')
    def test_get_analysis_success(self, mock_get_db, mock_dao_class, client, mock_analysis_db_object):
        # Arrange
        mock_get_db.return_value = AsyncMock()
        
        # Mock DAO
        mock_dao = AsyncMock()
        mock_dao.get_analysis_by_id.return_value = mock_analysis_db_object
        mock_dao_class.return_value = mock_dao
        
        # Mock TextAnalysisResponse.from_orm
        with patch('llm_knowledge_extractor.features.text_analyzer.schemas.text_analyzer_schema.TextAnalysisResponse.from_orm') as mock_from_orm:
            expected_response = {
                "id": 1,
                "original_text": "Test text",
                "summary": "Test summary",
                "title": "Test title",
                "topics": ["test"],
                "sentiment": "positive",
                "keywords": ["test", "keyword"],
                "confidence_score": 0.75,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z"
            }
            mock_from_orm.return_value = expected_response
            
            # Act
            response = client.get("/analysis/1")
            
            # Assert
            assert response.status_code == 200
            assert response.json()["id"] == 1
            
            # Verify service logic was called
            mock_dao.get_analysis_by_id.assert_called_once_with(1)
    
    @patch('llm_knowledge_extractor.features.text_analyzer.services.analysis_service.AnalysisDAO')
    @patch('llm_knowledge_extractor.features.text_analyzer.api.v1.text_analyzer_api.get_async_db')
    def test_get_analysis_not_found(self, mock_get_db, mock_dao_class, client):
        # Arrange
        mock_get_db.return_value = AsyncMock()
        
        # Mock DAO returning None
        mock_dao = AsyncMock()
        mock_dao.get_analysis_by_id.return_value = None
        mock_dao_class.return_value = mock_dao
        
        # Act
        response = client.get("/analysis/999")
        
        # Assert
        assert response.status_code == 404
        assert "Analysis not found" in response.json()["detail"]
        
        # Verify service logic was called
        mock_dao.get_analysis_by_id.assert_called_once_with(999)