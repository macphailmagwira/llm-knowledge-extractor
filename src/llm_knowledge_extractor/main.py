import logging
import sys
import traceback
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from llm_knowledge_extractor.core.config import settings
from llm_knowledge_extractor.common.utils.database_table_init import create_tables
from llm_knowledge_extractor.common.db.session import db, engine
from llm_knowledge_extractor.common.utils.get_logger import get_logger
logger = get_logger() 


try:    
    logger.info("Loading API router...")
    from llm_knowledge_extractor.api.v1.router import router    
    logger.info("Loading database session...")
    from llm_knowledge_extractor.common.db.session import db, engine
    
    # Import metadata and models for table creation
    logger.info("Loading database models...")
    from llm_knowledge_extractor.common.db.base import metadata
    from llm_knowledge_extractor.features.text_analyzer.models.text_analyzer import TextAnalysis    
    logger.info("All imports successful")
except Exception as e:
    logger.error(f"ERROR DURING IMPORT: {str(e)}")
    logger.error(traceback.format_exc())
    sys.exit(1)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan with database initialization
    """
    try:
        # Startup
        logger.info("=== APPLICATION STARTUP ===")
        
        #Connect to database
        try:
            logger.info("Connecting to database...")
            await db.connect()
            logger.info("Database connection established successfully")
        except Exception as db_error:
            logger.error(f"DATABASE CONNECTION ERROR: {str(db_error)}")
            logger.error(traceback.format_exc())
            raise
        
        # Create database tables
        try:
            logger.info("Creating database tables...")
            create_tables()
            logger.info("Database tables setup completed")
        except Exception as table_error:
            logger.error(f"TABLE CREATION ERROR: {str(table_error)}")
            logger.error(traceback.format_exc())
            raise
            
        logger.info("=== APPLICATION STARTUP COMPLETE ===")
        yield
        
    finally:
        # Shutdown
        logger.info("=== APPLICATION SHUTDOWN ===")
        try:
            if db is not None:
                await db.disconnect()
                logger.info("Database connection closed")
        except Exception as db_close_error:
            logger.error(f"Error closing database: {str(db_close_error)}")
        logger.info("=== APPLICATION SHUTDOWN COMPLETE ===")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    try:
        app_instance = FastAPI(
            title=settings.APP_TITLE, 
            lifespan=lifespan
        )
        
        # Add CORS middleware
        app_instance.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=["*"],
            expose_headers=["*"],
            max_age=600,
        )
        
        # Register exception handler
        @app_instance.middleware("http")
        async def catch_exceptions_middleware(request: Request, call_next):
            try:
                return await call_next(request)
            except Exception as e:
                logger.error(f"Exception in request {request.url.path}: {str(e)}")
                logger.error(traceback.format_exc())
                return JSONResponse(
                    status_code=422,
                    content={"detail": str(e)}
                )
        
        # Include API router
        app_instance.include_router(router, prefix="/api/v1")
        logger.info(f"API router initialized with prefix: /api/v1")
        
        return app_instance
    except Exception as app_error:
        logger.error(f"APPLICATION CREATION ERROR: {str(app_error)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

app = create_app()

if __name__ == "__main__":
    """
    Server configurations with enhanced error handling
    """
    try:
        host = settings.ALLOWED_HOST
        port = settings.ALLOWED_PORT
        debug_mode = settings.DEBUG
        
        logger.info(f"Starting server on {host}:{port} (debug={debug_mode})")
        
        uvicorn.run(
            app="main:app",  
            host=host,
            port=port,
            log_level="debug" if debug_mode else "info",  
            reload=True,
            log_config=None,
            use_colors=True,
        )
    except Exception as server_error:
        logger.error(f"SERVER STARTUP ERROR: {str(server_error)}")
        logger.error(traceback.format_exc())
        sys.exit(1)