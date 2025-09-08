import logging
import sys
import inspect
from llm_knowledge_extractor.core.config import settings

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def get_logger() -> logging.Logger:
    frame = inspect.currentframe().f_back
    module = frame.f_globals.get('__name__', 'unknown')
    logger = logging.getLogger(module)
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    return logger