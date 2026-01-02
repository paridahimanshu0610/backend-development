from sqlmodel import SQLModel, create_engine, Session
from .models import *
from typing import Annotated
from fastapi import Depends
from .config import settings

database_url = f"{settings.database}://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}" # "dialect+driver://username:password@host:port/database"

engine = create_engine(database_url, echo=True)

def create_db_and_tables():
    print("Creating database and tables...")
    SQLModel.metadata.create_all(engine)
    print("Database and tables created.")

def get_session():
    with Session(engine) as session:
        yield session

# `SessionDep` is not a Session instance. It’s a type annotation + dependency marker. FastAPI only resolves it inside dependency-injected functions
# In simple words, Session: SessionDep will not work with "any" regular function in Python. `SessionDep` can work as a dependency, only when FastAPI handles the function in which it is passed.
# As path operation functions are handled by FastAPI, `SessionDep` will only work as a dependency when it is passed inside a path operation function.
SessionDep = Annotated[Session, Depends(get_session)]