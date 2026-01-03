from fastapi import APIRouter, HTTPException,status, Depends, FastAPI, Response
from ..models import User, Post, Vote, VoteApiSchema
from ..database import SessionDep
from ..oauth2 import get_current_user
from .. import utils
from typing import Annotated
from sqlmodel import select, delete


router = APIRouter(prefix = "/vote", tags=["Login"])

# A vote record exists only for likes. A dislike doesn't have any record.
@router.post("/", status_code=status.HTTP_201_CREATED)
def vote(
    vote: VoteApiSchema,
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
):
    post_db = session.exec(select(Post).where(Post.id==vote.post_id)).first()

    if not post_db:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Post was not found."
        )

    vote_stmt = select(Vote).where(
        Vote.user_id == current_user.id,
        Vote.post_id == vote.post_id,
    )
    current_vote = session.exec(vote_stmt).first()

    if vote.vote_dir == 1:
        if current_vote:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User '{current_user.full_name}' has already liked this post.",
            )

        db_vote = Vote(
            post_id=vote.post_id,
            user_id=current_user.id,
        )

        session.add(db_vote)
        session.commit()
        return {"detail": "Successfully liked the post"}

    # vote_dir != 1 → unlike
    if not current_vote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Like does not exist.",
        )

    session.exec(
        delete(Vote).where(
            Vote.user_id == current_user.id,
            Vote.post_id == vote.post_id,
        )
    )
    session.commit()

    return {"detail": "Successfully unliked the post"}