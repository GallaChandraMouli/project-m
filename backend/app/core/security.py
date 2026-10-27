import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import jwt
import bcrypt

from app.core.config import settings

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def generate_api_key(name: str = "Default") -> Tuple[str, str, str]:
    """Generates an API key. Returns (raw_key, hashed_key, prefix)."""
    raw_token = secrets.token_hex(24)
    raw_key = f"nx-live-{raw_token}"
    prefix = raw_key[:12]
    key_hash = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
    return raw_key, key_hash, prefix

def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode('utf-8')).hexdigest()

def generate_node_token() -> str:
    """Generates a secure registration token for a provider worker daemon."""
    return f"nx-node-{secrets.token_hex(20)}"
