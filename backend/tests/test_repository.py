import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import Repository, RepositoryStatus
import unittest.mock as mock

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

def test_add_repository_invalid_url():
    response = client.post("/v1/repositories", json={"github_url": "invalid_url"})
    assert response.status_code == 422
    assert "Invalid GitHub repository URL format" in response.text

@mock.patch("subprocess.run")
def test_add_repository_success(mock_sub_run):
    mock_sub_run.return_value = mock.MagicMock(returncode=0, stdout="origin/main")

    payload = {"github_url": "https://github.com/owner/repo"}
    response = client.post("/v1/repositories", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["github_url"] == "https://github.com/owner/repo"
    assert data["name"] == "repo"
    assert data["owner"] == "owner"
    assert data["status"] == "pending"

def test_list_repositories():
    db = TestingSessionLocal()
    repo = Repository(
        github_url="https://github.com/owner/repo",
        name="repo",
        owner="owner",
        default_branch="main",
        local_path="./repos/owner/repo",
        status=RepositoryStatus.INDEXED
    )
    db.add(repo)
    db.commit()

    response = client.get("/v1/repositories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "repo"

def test_get_repository_not_found():
    response = client.get("/v1/repositories/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

def test_delete_repository_not_found():
    response = client.delete("/v1/repositories/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
