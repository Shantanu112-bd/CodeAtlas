import os
import re
import shutil
import subprocess
import logging
from uuid import UUID
from fastapi import BackgroundTasks, HTTPException, status
from ..models import Repository, RepositoryStatus
from ..repositories.repository_repo import RepositoryRepository
from ..config import settings
from .ast_service import ASTService

logger = logging.getLogger("codeatlas.ingestion")

class IngestionService:
    def __init__(self, repo_db: RepositoryRepository):
        self.repo_db = repo_db

    def parse_github_url(self, github_url: str) -> tuple[str, str]:
        # Parse owner and repo name from URL
        # Matches: https://github.com/owner/repo or git@github.com:owner/repo.git
        if github_url.startswith("git@"):
            match = re.search(r"github\.com:([a-zA-Z0-9\-._]+)/([a-zA-Z0-9\-._]+)\.git$", github_url)
        else:
            match = re.search(r"github\.com/([a-zA-Z0-9\-._]+)/([a-zA-Z0-9\-._]+)/?$", github_url)
            
        if not match:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract owner and repository name from URL."
            )
        
        owner, name = match.groups()
        if name.endswith(".git"):
            name = name[:-4]
        return owner, name

    def create_repository_record(self, github_url: str) -> Repository:
        existing = self.repo_db.get_by_url(github_url)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Repository with this URL is already registered."
            )
            
        owner, name = self.parse_github_url(github_url)
        local_path = os.path.abspath(os.path.join(settings.REPO_STORAGE_PATH, owner, name))
        
        repo = Repository(
            github_url=github_url,
            name=name,
            owner=owner,
            default_branch="main",
            local_path=local_path,
            status=RepositoryStatus.PENDING
        )
        return self.repo_db.create(repo)

    def clone_repository_sync(self, repo_id: UUID):
        repo = self.repo_db.get_by_id(repo_id)
        if not repo:
            logger.error(f"Repository {repo_id} not found to clone.")
            return

        self.repo_db.update_status(repo_id, RepositoryStatus.CLONING)
        logger.info(f"Starting clone for repository: {repo.github_url} to {repo.local_path}")

        if os.path.exists(repo.local_path):
            shutil.rmtree(repo.local_path)
        os.makedirs(os.path.dirname(repo.local_path), exist_ok=True)

        try:
            cmd = ["git", "clone", "--depth", "1", repo.github_url, repo.local_path]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Successfully cloned: {repo.github_url}")

            branch_cmd = ["git", "-C", repo.local_path, "symbolic-ref", "--short", "refs/remotes/origin/HEAD"]
            branch_result = subprocess.run(branch_cmd, capture_output=True, text=True)
            if branch_result.returncode == 0:
                branch_name = branch_result.stdout.strip().split("/")[-1]
                repo.default_branch = branch_name
            
            repo.status = RepositoryStatus.INDEXED
            self.repo_db.update(repo)

            # Trigger AST Analysis immediately
            logger.info(f"Triggering AST analysis for {repo.github_url}")
            ast_service = ASTService(self.repo_db.db)
            ast_service.analyze_repository(repo.id)
            
            # Trigger Embedding Generation
            logger.info(f"Triggering embedding generation for {repo.github_url}")
            from .embedding_service import EmbeddingService
            embedding_service = EmbeddingService(self.repo_db.db)
            embedding_service.embed_repository(repo.id)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {repo.github_url}. Error: {e.stderr}")
            repo.status = RepositoryStatus.FAILED
            self.repo_db.update(repo)
            if os.path.exists(repo.local_path):
                shutil.rmtree(repo.local_path, ignore_errors=True)
        except Exception as e:
            logger.error(f"Unexpected error cloning repository: {e}")
            repo.status = RepositoryStatus.FAILED
            self.repo_db.update(repo)
            if os.path.exists(repo.local_path):
                shutil.rmtree(repo.local_path, ignore_errors=True)

    def trigger_ingestion(self, github_url: str, background_tasks: BackgroundTasks) -> Repository:
        repo = self.create_repository_record(github_url)
        background_tasks.add_task(self.clone_repository_sync, repo.id)
        return repo

    def delete_repository(self, repo_id: UUID) -> bool:
        repo = self.repo_db.get_by_id(repo_id)
        if not repo:
            return False
            
        if os.path.exists(repo.local_path):
            shutil.rmtree(repo.local_path, ignore_errors=True)
            
        return self.repo_db.delete(repo_id)
