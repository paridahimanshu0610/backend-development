from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, status
from ..models import Post, PostPublic, PostCreate, PostUpdate
from ..database import SessionDep
from sqlmodel import Session, select

router = APIRouter(prefix="/posts", tags=["Post"])

@router.post("/", response_model=PostPublic, status_code = status.HTTP_201_CREATED)
def create_post(post: PostCreate, session: SessionDep):
    try:
        db_post = Post.model_validate(post)
        session.add(db_post)
        session.commit()
        session.refresh(db_post)
        return db_post
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = str(e))


@router.get("/", response_model=list[PostPublic])
def read_posts(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 3,
):
    posts = session.exec(select(Post).offset(offset).limit(limit)).all()

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


@router.delete("/{post_id}")
def delete_post(post_id: int, session: SessionDep):
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail= f"Post with id: {post_id} was not found."
        )
    session.delete(post)
    session.commit()
    return {"ok": True}