from sqlalchemy.orm import Session
from ..models import Repository, RepositoryStatus
from uuid import UUID

class RepositoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, repo_id: UUID) -> Repository | None:
        return self.db.query(Repository).filter(Repository.id == repo_id).first()

    def get_by_url(self, github_url: str) -> Repository | None:
        return self.db.query(Repository).filter(Repository.github_url == github_url).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[Repository]:
        return self.db.query(Repository).offset(skip).limit(limit).all()

    def create(self, repo: Repository) -> Repository:
        self.db.add(repo)
        self.db.commit()
        self.db.refresh(repo)
        return repo

    def update_status(self, repo_id: UUID, status: RepositoryStatus) -> Repository | None:
        repo = self.get_by_id(repo_id)
        if repo:
            repo.status = status
            self.db.commit()
            self.db.refresh(repo)
        return repo

    def update(self, repo: Repository) -> Repository:
        self.db.commit()
        self.db.refresh(repo)
        return repo

    def delete(self, repo_id: UUID) -> bool:
        repo = self.get_by_id(repo_id)
        if repo:
            self.db.delete(repo)
            self.db.commit()
            return True
        return False
