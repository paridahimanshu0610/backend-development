from typing import Annotated, Optional, List
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.params import Depends
from ..models import Post, Vote, PostPublic, PostWithVote, PostBase, PostCreate, PostUpdate, User
from ..oauth2 import get_current_user
from ..database import SessionDep
from sqlmodel import Session, select
from sqlalchemy import func
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


@router.get("/", response_model=List[PostWithVote]) #
def read_posts(
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 3,
    search: Optional[str] = "",
    show_all: Optional[bool] = True
):

    # Implemenation 1: Without votes
    # select_stmt = (select(Post).options(selectinload(Post.owner))) # With `selectinload`, there will be 2 separate queries. One for `post` and another for `user`. 
    # select_stmt = select_stmt if show_all else select_stmt.where(Post.owner_id == current_user.id)
    # posts = session.exec(select_stmt.where(Post.content.ilike(f"%{search}%")).offset(offset).limit(limit)).all()

    # Implementation 2: With votes
    # Base select with vote count
    select_stmt = (
        select(Post, func.count(Vote.post_id).label("votes"))
        .join(Vote, Vote.post_id == Post.id, isouter=True)
        .group_by(Post.id)
    )

    # Optional owner filter
    if not show_all:
        select_stmt = select_stmt.where(Post.owner_id == current_user.id)

    # Optional content search
    if search:
        select_stmt = select_stmt.where(Post.content.ilike(f"%{search}%"))

    # Pagination
    select_stmt = select_stmt.offset(offset).limit(limit)
    print("SQL query:", select_stmt)
    # Execute query
    posts = session.exec(select_stmt).all()

    # Wrap each row into PostWithVote
    posts = [
        PostWithVote(post=PostPublic.model_validate(post), votes=votes)  # ensure PostPublic used
        for post, votes in posts
    ]    
    print("All queried posts:", posts)

    if not posts:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "No post was found."
        )
    
    return posts


@router.get("/{post_id}", response_model=PostWithVote)
def read_post(post_id: int, session: SessionDep, current_user: Annotated[User, Depends(get_current_user)],):
    # Implemenation 1: Without votes
    # post = session.get(Post, post_id)

    # Implementation 2: With votes
    select_stmt = (
        select(Post, func.count(Vote.post_id).label("votes"))
        .join(Vote, Vote.post_id == Post.id, isouter=True)
        .where(Post.id == post_id)
        .group_by(Post.id)
    )

    post = session.exec(select_stmt).first()  # row is a tuple: (Post, vote_count)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post_obj, vote_count = post

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail= f"Post with id: {post_id} was not found."
        )

    post_obj, vote_count = post

    # Convert Post -> PostPublic
    post_public = PostPublic.model_validate(post_obj)

    # Wrap into PostWithVote
    post = PostWithVote(post=post_public, votes=vote_count)

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