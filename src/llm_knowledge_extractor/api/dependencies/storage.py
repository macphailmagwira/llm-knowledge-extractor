from fastapi import Depends, HTTPException, status
from azure.storage.blob import BlobServiceClient
import logging

from llm_knowledge_extractor.core.config import settings

logger = logging.getLogger(__name__)

async def get_blob_service():
    """
    Returns an Azure Blob Service client.
    Used as a FastAPI dependency.
    """
    try:
        connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        return blob_service_client
    except Exception as e:
        logger.error(f"Failed to connect to Azure Blob Storage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to file storage service"
        )