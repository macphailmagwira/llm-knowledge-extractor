import logging
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional
import requests
import json
import base64
from llm_knowledge_extractor.features.workflow.schemas.workflow import User


from llm_knowledge_extractor.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)

# Use a custom OAuth2 scheme that doesn't auto-error
class CustomOAuth2(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.headers.get("Authorization")
        logger.debug(f"Authorization header: {authorization[:20] if authorization else 'None'}")
        
        if not authorization:
            return None
            
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer":
            logger.warning(f"Invalid authorization scheme: {scheme}")
            return None
            
        return token

# Initialize with tokenUrl but we don't really use it for validation
oauth2_scheme = CustomOAuth2(tokenUrl="token", auto_error=False)



async def verify_token(token: str) -> dict:
    """
    Verify JWT created by our application frontend.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Check basic JWT format
        parts = token.split('.')
        if len(parts) != 3:
            logger.error(f"Invalid JWT format: expected 3 parts, got {len(parts)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Decode JWT with our secret
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=["HS256"]
        )
        return payload
    except JWTError as e:
        logger.error(f"JWT decoding error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    """
    Dependency to get the current user from a token.
    Works with multiple token types.
    """
    try:
        
        if not token:
            logger.warning("No token provided in Authorization header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Log token prefix for debugging
        if token:
            logger.debug(f"Token prefix: {token[:10]}...")
            
        # Verify token and get payload
        payload = await verify_token(token)
        
        # Log successful decode
        logger.debug(f"Token payload contains keys: {list(payload.keys())}")
        
        # Extract user ID - try 'sub' first, then fall back to other fields
        user_id = payload.get("sub") or payload.get("id") or payload.get("userId")
        if not user_id:
            logger.warning("Token missing user identifier")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user identifier",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create user object from token claims
        user = User(
            id=user_id,
            email=payload.get("email"),
            name=payload.get("name")
        )
        logger.debug(f"Authenticated user: {user.id}")
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in auth: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication system error",
        )