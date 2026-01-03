from typing import Annotated
from fastapi.concurrency import asynccontextmanager
from fastapi import FastAPI, status, Response, HTTPException, Depends, Query
from sqlmodel import Session, select
from .database import create_db_and_tables, SessionDep
from .models import *
from .routers import post, user, auth, vote

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    create_db_and_tables()
    yield

app = FastAPI(lifespan = lifespan)

app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(vote.router)

@app.get("/")
def root():
    return {"message" : "Welcome to the home page!"}

