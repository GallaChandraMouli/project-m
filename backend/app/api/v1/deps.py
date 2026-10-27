from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_access_token, hash_api_key
from app.models.user import User
from app.models.api_key import ApiKey

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_authenticated_consumer(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Authenticates consumer via either standard API Key (`nx-live-...`) or session JWT."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Use 'Bearer <key>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_str = parts[1]
    
    # Check if API Key
    if token_str.startswith("nx-live-"):
        key_hash = hash_api_key(token_str)
        api_key_obj = db.query(ApiKey).filter(ApiKey.key_hash == key_hash, ApiKey.is_active == True).first()
        if not api_key_obj:
            raise HTTPException(status_code=401, detail="Invalid or revoked API key")
        
        user = db.query(User).filter(User.id == api_key_obj.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User associated with API key not found")
        return user
    
    # Else check if JWT token
    payload = decode_access_token(token_str)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid API key or token")
    
    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
