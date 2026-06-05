from pydantic import BaseModel, EmailStr, field_validator
import re
from uuid import UUID
from datetime import datetime
from .models import RepositoryStatus

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    github_id: str

class UserOut(UserBase):
    id: UUID
    github_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

class GitHubCallbackCode(BaseModel):
    code: str
    state: str | None = None

class RepositoryBase(BaseModel):
    github_url: str

    @field_validator("github_url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        # Matches https://github.com/owner/repo or git@github.com:owner/repo.git
        pattern = r"^(https?://github\.com/[a-zA-Z0-9\-._]+/[a-zA-Z0-9\-._]+(/?)|git@github\.com:[a-zA-Z0-9\-._]+/[a-zA-Z0-9\-._]+\.git)$"
        if not re.match(pattern, v):
            raise ValueError("Invalid GitHub repository URL format.")
        return v

class RepositoryCreate(RepositoryBase):
    pass

class RepositoryOut(RepositoryBase):
    id: UUID
    github_url: str
    name: str
    owner: str
    default_branch: str
    local_path: str
    status: RepositoryStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
