import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select, text

from app.orm_main import app
from app.config import settings
from app.database import get_session

from app.orm_main import app
from app.config import settings
from app.oauth2 import prepare_access_token
from app import models

def create_test_database():
    admin_db_url = (
        f"{settings.database}://"
        f"{settings.database_username}:{settings.database_password}@"
        f"{settings.database_hostname}:{settings.database_port}/postgres"
    )

    admin_engine = create_engine(admin_db_url, isolation_level="AUTOCOMMIT")

    with admin_engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT 1 FROM pg_database WHERE datname = :dbname"
            ),
            {"dbname": f"{settings.database_name}_test"},
        )

        exists = result.scalar()

        if not exists:
            conn.execute(
                text(f'CREATE DATABASE "{settings.database_name}_test"')
            )

    admin_engine.dispose()

create_test_database()

# Test database URL
TEST_DATABASE_URL = (
    f"{settings.database}://"
    f"{settings.database_username}:{settings.database_password}@"
    f"{settings.database_hostname}:{settings.database_port}/"
    f"{settings.database_name}_test"
)

# Create SQLModel engine
engine = create_engine(TEST_DATABASE_URL, echo=False)


@pytest.fixture(scope="function")
def session():
    """
    Creates a fresh database session for each test.
    """
    # Drop and recreate tables
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture(scope="function")
def client(session: Session):
    """
    FastAPI test client with overridden DB session.
    """

    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user2(client):
    user_data = {
        "username": "aditya",
        "email": "aditya@gmail.com",
        "full_name": "Aditya Chopra",
        "password": "password123"
        }
    res = client.post("/user/", json=user_data)

    assert res.status_code == 201

    new_user = res.json()
    new_user['password'] = user_data['password']
    return new_user


@pytest.fixture(scope="function")
def test_user(client):
    user_data = {
        "username": "vikram",
        "email": "vikram@gmail.com",
        "full_name": "Vikram Chopra",
        "password": "password123"
        }
    res = client.post("/user/", json=user_data)

    assert res.status_code == 201

    new_user = res.json()
    new_user['password'] = user_data['password']
    return new_user


@pytest.fixture(scope="function")
def token(test_user):
    return prepare_access_token({"username": test_user["username"], "user_id": test_user['id']})


@pytest.fixture(scope="function")
def authorized_client(client, token):
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}"
    }

    return client


@pytest.fixture(scope="function")
def test_posts(test_user, test_user2, session):
    posts_data = [
        {
            "title": "1st title",
            "content": "1st content",
            "owner_id": test_user["id"],
        },
        {
            "title": "2nd title",
            "content": "2nd content",
            "owner_id": test_user["id"],
        },
        {
            "title": "3rd title",
            "content": "3rd content",
            "owner_id": test_user["id"],
        },
        {
            "title": "4th title",
            "content": "4th content",
            "owner_id": test_user2["id"],
        },
    ]

    posts = [models.Post(**post) for post in posts_data]

    session.add_all(posts)
    session.commit()

    stmt = select(models.Post).order_by(models.Post.id)
    posts = session.exec(stmt).all()

    yield posts

    # Optional but recommended safety
    session.rollback()
