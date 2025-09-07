# PetPlantr Authentication Configuration
# JWT-based authentication with API key fallback

import os
import jwt
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from pydantic import BaseModel

# Try to import passlib, fallback to simple hashing if not available
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except ImportError:
    # Fallback for environments without passlib
    import hashlib

    class SimpleCryptContext:
        def hash(self, password: str) -> str:
            return hashlib.sha256(password.encode()).hexdigest()

        def verify(self, plain: str, hashed: str) -> bool:
            return self.hash(plain) == hashed

    pwd_context = SimpleCryptContext()

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security schemes
security = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: list[str] = []

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    scopes: list[str] = []

# Mock user database (replace with real database in production)
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Administrator",
        "email": "admin@petplantr.com",
        "hashed_password": pwd_context.hash("admin123"),
        "disabled": False,
        "scopes": ["read", "write", "admin"]
    },
    "api_user": {
        "username": "api_user",
        "full_name": "API User",
        "email": "api@petplantr.com",
        "hashed_password": pwd_context.hash("api123"),
        "disabled": False,
        "scopes": ["read", "write"]
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def get_user(db: dict, username: str) -> Optional[User]:
    """Get user from database"""
    if username in db:
        user_dict = db[username]
        return User(**user_dict)
    return None

def authenticate_user(fake_db: dict, username: str, password: str) -> Optional[User]:
    """Authenticate a user"""
    user = get_user(fake_db, username)
    if not user:
        return None
    if not verify_password(password, fake_db[username]["hashed_password"]):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[TokenData]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=token_scopes)
        return token_data
    except jwt.PyJWTError:
        return None

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    api_key: Optional[str] = Security(api_key_header)
) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Try JWT token first
    if credentials:
        token_data = verify_token(credentials.credentials)
        if token_data and token_data.username:
            user = get_user(fake_users_db, token_data.username)
            if user:
                return user

    # Try API key
    if api_key:
        # Simple API key validation (replace with database lookup)
        if api_key == os.getenv("API_KEY", "petplantr-api-key-12345"):
            return User(
                username="api_key_user",
                scopes=["read", "write"],
                disabled=False
            )

    raise credentials_exception

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Scope-based dependencies
async def require_scope(scope: str):
    """Require specific scope for endpoint"""
    async def scope_checker(current_user: User = Depends(get_current_active_user)):
        if scope not in current_user.scopes:
            raise HTTPException(
                status_code=403,
                detail=f"Not enough permissions. Required scope: {scope}"
            )
        return current_user
    return scope_checker

# Admin-only dependency
require_admin = require_scope("admin")

# Export for use in main application
__all__ = [
    "authenticate_user",
    "create_access_token",
    "get_current_user",
    "get_current_active_user",
    "require_scope",
    "require_admin",
    "User",
    "TokenData"
]
