from typing import Annotated
from fastapi import APIRouter, HTTPException,status, Depends, FastAPI
from psycopg2 import IntegrityError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from ..models import User, LoginUser, Token
from ..database import SessionDep
from .. import utils, oauth2
from sqlmodel import select


router = APIRouter(tags=["Login"])

@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def authenticate_user(session: SessionDep, user_credentials: OAuth2PasswordRequestForm = Depends(),):

    user_db = session.exec(select(User).where(User.email == user_credentials.username)).first()

    if not user_db:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials", headers={"WWW-Authenticate": "Bearer"},)
    
    if not utils.verify_password(user_credentials.password, user_db.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials", headers={"WWW-Authenticate": "Bearer"},)
    
    access_token = oauth2.prepare_access_token({"username": user_db.username, "user_id": user_db.id})

    return {"access_token" : access_token, "token_type" : "bearer"}  