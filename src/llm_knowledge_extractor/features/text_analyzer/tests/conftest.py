import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime

from llm_knowledge_extractor.main import app
from llm_knowledge_extractor.features.text_analyzer.schemas.text_analyzer_schema import TextAnalysisResponse
