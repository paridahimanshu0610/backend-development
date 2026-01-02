from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg2 import IntegrityError
from ..models import User, CreateUser, ReadUser, UpdateUser
from ..database import SessionDep
from .. import utils
from ..oauth2 import get_current_user
from sqlmodel import select

router = APIRouter(prefix="/user", tags=["User"])

@router.post("/", response_model=ReadUser, status_code=status.HTTP_201_CREATED)
def create_user(inp_user: CreateUser, session: SessionDep):
    # Convert input data to dict and add hashed password
    user_data = inp_user.model_dump()
    user_data["hashed_password"] = utils.hash_password(user_data["password"])
    user = User(**user_data)
    try:
        session.add(user)
        session.commit()
        session.refresh(user)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return user

@router.patch("/{user_id}", response_model=ReadUser, status_code=status.HTTP_200_OK)
def update_user(user_id:int, user: UpdateUser, session:SessionDep):
    user_db = session.get(User, user_id)
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail= f"User with id: {user_id} was not found."
        )

    user_data = user.model_dump(exclude_unset=True)
    # Handle password separately
    if "password" in user_data:
        user_db.password = user_data["password"]
        user_db.hashed_password = utils.hash_password(user_data["password"])
    try:
        user_db.sqlmodel_update(user_data)
        session.add(user_db)
        session.commit()
        session.refresh(user_db)
        return user_db
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists.",
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f"Failed to update user: {e}",
        )     


@router.get("/", response_model=list[ReadUser], status_code=status.HTTP_200_OK)
def read_user(
    current_user: Annotated[User, Depends(get_current_user)], # Annotated[User, Depends(get_current_user)] ensures that this API requires an authentication token. 
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    # `current_user` details will be used to check for things like resource permission, and use other user details required during backend processing.
    print("current_user_details: ", current_user)
    users = session.exec(select(User).offset(offset).limit(limit)).all()
    return users

@router.get("/{user_id}", response_model=ReadUser, status_code=status.HTTP_200_OK)
def read_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "User not found")
    return user  

@router.delete("/{user_id}")
def delete_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    session.delete(user)
    session.commit()
    return {"ok": True}