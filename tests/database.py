import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

from app.orm_main import app
from app.config import settings
from app.database import get_session

from app.orm_main import app
from app.config import settings

# Test database URL
TEST_DATABASE_URL = (
    f"{settings.database}://"
    f"{settings.database_username}:{settings.database_password}@"
    f"{settings.database_hostname}:{settings.database_port}/"
    f"{settings.database_name}_test"
)

# Create SQLModel engine
engine = create_engine(TEST_DATABASE_URL, echo=False)


@pytest.fixture(scope="function")(scope="function")
def session():
    """
    Creates a fresh database session for each test.
    """
    # Drop and recreate tables
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture(scope="function")(scope="function")
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