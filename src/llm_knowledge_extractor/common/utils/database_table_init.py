from llm_knowledge_extractor.common.db.session import engine, metadata
from llm_knowledge_extractor.core.config import settings
import logging
import traceback
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)



def create_tables():
    """Create database tables and log the process"""
    try:
        logger.info("Starting table creation process...")
        
        # Get existing tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"Existing tables in database: {existing_tables}")
        
        # Get tables from metadata
        metadata_tables = list(metadata.tables.keys())
        logger.info(f"Tables defined in metadata: {metadata_tables}")
        
        # Create tables
        logger.info("Creating tables (this will skip existing ones)...")
        metadata.create_all(bind=engine)
        
        # Verify tables were created
        updated_tables = inspector.get_table_names()
        new_tables = set(updated_tables) - set(existing_tables)
        
        if new_tables:
            logger.info(f"New tables created: {list(new_tables)}")
        else:
            logger.info("No new tables needed - all tables already exist")
            
        logger.info(f"Final database tables: {updated_tables}")
        logger.info("Table creation process completed successfully")
        
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        logger.error(traceback.format_exc())
        raise