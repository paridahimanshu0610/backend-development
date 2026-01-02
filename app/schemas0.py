from datetime import datetime
from typing import Annotated, Optional

from fastapi import Depends
from pydantic import EmailStr, Field
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Session, SQLModel, create_engine, select

# Read: https://sqlmodel.tiangolo.com/tutorial/fastapi/multiple-models/#use-multiple-models-to-create-a-hero
# and https://sqlmodel.tiangolo.com/tutorial/fastapi/response-model/

# This is the base model that contains the common fields for both CreateTweet and ReadTweet models.
class BaseTweet(SQLModel):
    title: str = Field(index=True, nullable=False)
    content: str = Field(nullable=False)
    # By adding Optional, we are making this field optional in the request body.
    published: Optional[bool] = Field(default=True, nullable=False)

# This behaves as both a Pydantic model and an SQLAlchemy model, and is used for interacting with the database.
class Tweet(BaseTweet, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True, nullable=False)
    date_created: datetime = Field(default_factory=datetime.now, index=True, nullable=False)

# This behaves as a Pydantic model, and is used for data validation and serialization.
class CreateTweet(BaseTweet):
    pass

# This also behaves as a Pydantic model, and is used for data validation and serialization.
class ReadTweet(BaseTweet):
    # By commenting out id here, we are excluding it from the response model.
    # id: int
    date_created: datetime

########################################### USER MODEL ###########################################
class BaseUser(SQLModel):
    username: str = Field(index=True, nullable=False, unique=True)
    email: EmailStr = Field(index=True, nullable=False, unique=True)
    full_name: str = Field(nullable=False)
    is_active: Optional[bool] = Field(default=True, nullable=False)

class User(BaseUser, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    password: str = Field(nullable=False)
    hashed_password: str = Field(nullable=False)
    # date_created: datetime = Field(default_factory=datetime.now, index=True, nullable=False)
    # Using server-side default for date_created to ensure consistency across distributed systems and avoid timezone issues.
    date_created: datetime = Field(sa_column=Column(DateTime, server_default=func.now(), nullable=False, index=True))

class CreateUser(BaseUser):
    password: str = Field(nullable=False)

class ReadUser(BaseUser):
    id: int
    date_created: datetime