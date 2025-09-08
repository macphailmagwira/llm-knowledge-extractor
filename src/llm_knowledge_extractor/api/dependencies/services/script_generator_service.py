from functools import lru_cache
from llm_knowledge_extractor.features.python_script_generator.services.python_script_generator import ScriptGeneratorService
from llm_knowledge_extractor.core.config import settings

@lru_cache()
def get_script_generator_service() -> ScriptGeneratorService:
    """Return a singleton ScriptGeneratorService instance with cached configuration."""
    return ScriptGeneratorService()