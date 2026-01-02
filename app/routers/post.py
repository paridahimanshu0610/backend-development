from typing import Annotated, Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.params import Depends
from ..models import Post, PostPublic, PostBase, PostCreate, PostUpdate, User
from ..oauth2 import get_current_user
from ..database import SessionDep
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/posts", tags=["Post"])

@router.post("/", response_model=PostPublic, status_code = status.HTTP_201_CREATED)
def create_post(session: SessionDep, current_user: Annotated[User, Depends(get_current_user)], post: PostCreate, ):
    try:
        print("input post", type(post), post)
        db_post = Post(
                **post.model_dump(),
                owner_id=current_user.id,
            )
        # db_post = Post.model_validate(post)
        session.add(db_post)
        session.commit()
        session.refresh(db_post)
        return db_post
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = str(e))


@router.get("/", response_model=list[PostPublic])
def read_posts(
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 3,
    search: Optional[str] = "",
    show_all: Optional[bool] = True
):

    # select_stmt = select(Post)
    select_stmt = (select(Post).options(selectinload(Post.owner))) # With `selectinload`, there will be 2 separate queries. One for `post` and another for `user`. 
    select_stmt = select_stmt if show_all else select_stmt.where(Post.owner_id == current_user.id)
    posts = session.exec(select_stmt.where(Post.content.ilike(f"%{search}%")).offset(offset).limit(limit)).all()
    
    if not posts:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "No post was found."
        )
    
    return posts


@router.get("/{post_id}", response_model=PostPublic)
def read_post(post_id: int, session: SessionDep):
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail= f"Post with id: {post_id} was not found."
        )
    return post


@router.patch("/{post_id}", response_model=PostPublic)
def update_post(post_id: int, post: PostUpdate, session: SessionDep):
    post_db = session.get(Post, post_id)
    if not post_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail= f"Post with id: {post_id} was not found."
        )
    post_data = post.model_dump(exclude_unset=True)
    post_db.sqlmodel_update(post_data)
    session.add(post_db)
    session.commit()
    session.refresh(post_db)
    return post_db


@router.delete("/{post_id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, session: SessionDep, current_user: Annotated[User, Depends(get_current_user)],):
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail= f"Post with id: {post_id} was not found."
        )

    if post.owner_id!=current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail= "You are not allowed to delete this post."
        )
     
    session.delete(post)
    session.commit()