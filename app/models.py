from datetime import datetime, timezone
from pydantic import EmailStr
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, String, Boolean, DateTime, text
from typing import Optional

# class Post(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True)
#     title: str
#     content: str

#     published: bool = Field(
#         sa_column=Column(
#             Boolean,
#             nullable=False,
#             server_default=text("TRUE"),
#         )
#     )

#     created_at: datetime = Field(
#         default_factory=datetime.utcnow,  # Python-side
#         sa_column=Column(
#             DateTime,
#             nullable=False,
#             server_default=text("now()"),   # DB-side
#         ),
#     ) 

# Base SQLModel to be used while defining other SQLModels
class PostBase(SQLModel):
    title: str
    content: str
    published: Optional[bool] = Field(
        default=True,
        sa_column=Column(
            Boolean,
            nullable=False,
            server_default=text("TRUE"),
        )
    )

# Note that only the Post class has table=True
class Post(PostBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    # Using server-side default for created_at to ensure consistency across distributed systems and avoid timezone issues.
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),  # Python-side UTC
        sa_column=Column(
            DateTime(timezone=True),                         # DB-side UTC
            nullable=False,
            server_default=text("timezone('utc', now())"),   # PostgreSQL UTC now()
        ),
    ) 

# SQLModel defining the output schema for GET API
class PostPublic(PostBase):
    id: int

# SQLModel defining the input schema for CREATE API
class PostCreate(PostBase):
    pass

# SQLModel defining the input schema for UPDATE API
class PostUpdate(PostBase):
    pass

########################################### USER MODEL ###########################################
class BaseUser(SQLModel):
    username: str = Field(sa_column=Column(String, nullable=False, unique=True))
    email: EmailStr = Field(sa_column=Column(String, nullable=False, unique=True))
    full_name: str = Field(sa_column=Column(String, nullable=False))

class User(BaseUser, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    password: str = Field(nullable=False)
    hashed_password: str = Field(nullable=False)
    # Using server-side default for date_created to ensure consistency across distributed systems and avoid timezone issues.
    date_created: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),  # Python-side UTC
        sa_column=Column(
            DateTime(timezone=True),                         # DB-side UTC
            nullable=False,
            server_default=text("timezone('utc', now())"),   # PostgreSQL UTC now()
        ),
    ) 
    is_active: Optional[bool] = Field(
        default=True,
        sa_column=Column(
            Boolean,
            nullable=False,
            server_default=text("TRUE"),
        )
    )

class CreateUser(BaseUser):
    password: str = Field(nullable=False)

class ReadUser(BaseUser):
    id: int
    date_created: datetime

class UpdateUser(SQLModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

########################################### USER AUTHENTICATON MODEL ###########################################
class LoginUser(SQLModel):
    email: EmailStr
    password: str

class Token(SQLModel):
    access_token: str
    token_type: str

class TokenData(SQLModel):
    username: Optional[str] = None
    user_id: Optional[int] = None