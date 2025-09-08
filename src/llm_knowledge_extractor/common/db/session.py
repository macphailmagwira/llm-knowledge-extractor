import logging
from typing import Generator

import sqlalchemy
from databases import Database
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy_utils import create_database, database_exists
from typing import AsyncGenerator
from llm_knowledge_extractor.core.config import settings
from llm_knowledge_extractor.common.db.base import metadata

logger = logging.getLogger(__name__)

# Set SSL configuration based on environment
use_ssl = settings.ENVIRONMENT == "production"
logger.info(f"Using SSL: {use_ssl}")

# Configure connect args for async engine
async_connect_args = {
    "server_settings": {"jit": "off"}  # Improve ENUM handling
}

# Only add SSL settings in production
if use_ssl:
    async_connect_args.update({
        "ssl": True,
        "ssl_context": True,
    })

# Use asyncpg for async operations
async_engine = create_async_engine(
    settings.DB_URL.replace('postgresql+psycopg2', 'postgresql+asyncpg'),
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_timeout=60,
    pool_recycle=1800,
    pool_pre_ping=True,
    connect_args=async_connect_args
)

# Keep the synchronous engine for compatibility
db = Database(settings.DB_URL)

# Configure connect args for sync engine
sync_connect_args = {
    "connect_timeout": 10,
}

# Only add SSL settings in production
if use_ssl:
    sync_connect_args["sslmode"] = "require"
else:
    sync_connect_args["sslmode"] = "prefer"  # Fallback to non-SSL if not available

# Enhanced engine configuration
engine = sqlalchemy.create_engine(
    settings.DB_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_timeout=60,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo_pool=True if settings.DEBUG else False,
    connect_args=sync_connect_args
)

# Create async session factory
AsyncLocalSession = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession
)

# Create database if it doesn't exist
if not database_exists(engine.url):
    create_database(engine.url)

LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Add async session getter - FIXED to re-raise exceptions
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    A dependency for working with PostgreSQL asynchronously
    """
    async_session = AsyncLocalSession()
    try:
        yield async_session
    except Exception as e:
        logger.error(f"Async database session error: {e}", exc_info=True)
        # IMPORTANT: Re-raise the exception so FastAPI can handle it properly
        raise
    finally:
        await async_session.close()

# FIXED to re-raise exceptions
def get_db() -> Generator[Session, None, None]:
    """
    A dependency for working with PostgreSQL
    """
    db_session = LocalSession()
    try:
        yield db_session
    except Exception as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        # IMPORTANT: Re-raise the exception so FastAPI can handle it properly
        raise
    finally:
        db_session.close()