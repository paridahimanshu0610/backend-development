from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from jwt.exceptions import InvalidTokenError
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from pydantic import BaseModel
from .models import User, TokenData, Token
from .database import SessionDep
from .config import settings
from sqlmodel import select

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# In OAuth2PasswordBearer, `tokenUrl="login"` tells SwaggerUI where to get a token. It does nothing at runtime. It can even be a fake URL
# token='login' is just for front-end documentation purpose.
# `OAuth2PasswordBearer` reads the Authorization header in the HTTPRequest
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def prepare_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# HTTP Request
#     ↓
# Authorization Header: Bearer <JWT>
#     ↓
# OAuth2PasswordBearer
#     ↓
# Extracts <JWT>
#     ↓
# Injected into get_current_user(token)
#     ↓
# verify_access_token(token)
#     ↓
# jwt.decode(...)
#     ↓
# user_id extracted

def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        username = payload.get("username")
        if user_id is None:
            raise credentials_exception
        
        token_data = TokenData(user_id=user_id, username = username)

    except InvalidTokenError:
        raise credentials_exception 
    
    return token_data

# When we send an HTTP request, FastAPI does the following before the endpoint runs:

# 1. Sees Depends(oauth2_scheme)
# 2. Looks for the Authorization header
# 3. Verifies the format is Bearer <token>
# 4. Extracts the token string
# 5. Injects it into the function. Internally, this happens: token = oauth2_scheme(request)

def get_current_user(session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)],) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Could not validate credentials", 
        headers={"WWW-Authenticate": "Bearer"}, 
        )
    
    token_data = verify_access_token(token, credentials_exception)
    user = session.exec(select(User).where(User.id == token_data.user_id)).first()

    if not user:
        raise credentials_exception
    
    return user