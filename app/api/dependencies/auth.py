"""
Authentication dependencies
Provides different authentication methods for API endpoints
"""
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Union
from app.models.user import User
from app.db.conn import get_db
from app.api.routes.auth import get_current_user
from app.core.config import get_app_settings

settings = get_app_settings()

# Optional bearer token scheme
security = HTTPBearer(auto_error=False)


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Verify API key for cronjob/integration access.
    API key should be provided in X-API-Key header.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Get configured API key
    if not settings.cronjob_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key authentication is not configured on server"
        )
    
    # Compare API keys
    configured_key = (
        settings.cronjob_api_key.get_secret_value() 
        if hasattr(settings.cronjob_api_key, 'get_secret_value') 
        else str(settings.cronjob_api_key)
    )
    
    if x_api_key != configured_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return x_api_key


async def get_current_user_or_api_key(
    x_api_key: Optional[str] = Header(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Union[User, str]:
    """
    Allow authentication via either JWT token or API key.
    Returns User object for JWT auth, or API key string for key auth.
    
    This is useful for endpoints that can be accessed by both:
    - Regular authenticated users (JWT)
    - Automated systems/cronjobs (API Key)
    """
    # Try API key first
    if x_api_key:
        try:
            return await verify_api_key(x_api_key)
        except HTTPException:
            pass
    
    # Try JWT token
    if credentials:
        try:
            return await get_current_user(credentials.credentials, db)
        except HTTPException:
            pass
    
    # Neither worked
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide either Bearer token or X-API-Key header.",
        headers={"WWW-Authenticate": "Bearer, ApiKey"},
    )


async def require_api_key(api_key: str = Depends(verify_api_key)) -> str:
    """
    Require API key authentication only.
    Use this for endpoints that should only be accessed by cronjobs/integrations.
    """
    return api_key


async def require_user_auth(user: User = Depends(get_current_user)) -> User:
    """
    Require JWT user authentication only.
    Use this for endpoints that should only be accessed by logged-in users.
    """
    return user
