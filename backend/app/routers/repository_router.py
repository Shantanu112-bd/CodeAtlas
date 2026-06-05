from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from ..database import get_db
from ..schemas import RepositoryCreate, RepositoryOut
from ..repositories.repository_repo import RepositoryRepository
from ..services.ingestion_service import IngestionService


router = APIRouter(prefix="/repositories", tags=["Repositories"])

def get_ingestion_service(db: Session = Depends(get_db)) -> IngestionService:
    repo_db = RepositoryRepository(db)
    return IngestionService(repo_db)

@router.post("", response_model=RepositoryOut, status_code=status.HTTP_201_CREATED)
def add_repository(
    payload: RepositoryCreate,
    background_tasks: BackgroundTasks,
    service: IngestionService = Depends(get_ingestion_service)
):
    return service.trigger_ingestion(payload.github_url, background_tasks)

@router.get("", response_model=list[RepositoryOut])
def list_repositories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    repo_db = RepositoryRepository(db)
    return repo_db.get_all(skip=skip, limit=limit)

@router.get("/{id}", response_model=RepositoryOut)
def get_repository(
    id: UUID,
    db: Session = Depends(get_db)
):
    repo_db = RepositoryRepository(db)
    repo = repo_db.get_by_id(id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found."
        )
    return repo
@router.get("/{id}/stats")
def get_repository_stats(
    id: UUID,
    db: Session = Depends(get_db)
):
    from ..models import CodeFile, CodeClass, CodeFunction, CodeGraphEdge
    
    files_count = db.query(CodeFile).filter(CodeFile.repository_id == id).count()
    classes_count = db.query(CodeClass).join(CodeFile).filter(CodeFile.repository_id == id).count()
    functions_count = db.query(CodeFunction).join(CodeFile).filter(CodeFile.repository_id == id).count()
    deps_count = db.query(CodeGraphEdge).filter(CodeGraphEdge.repository_id == id).count()
    
    # Heuristics for architecture
    services = db.query(CodeClass).join(CodeFile).filter(CodeFile.repository_id == id, CodeClass.name.ilike('%Service%')).count()
    controllers = db.query(CodeClass).join(CodeFile).filter(CodeFile.repository_id == id, CodeClass.name.ilike('%Controller%')).count()
    repos = db.query(CodeClass).join(CodeFile).filter(CodeFile.repository_id == id, CodeClass.name.ilike('%Repository%')).count()
    
    health_score = 85 # Placeholder for MVP
    
    return {
        "repository_id": id,
        "files": files_count,
        "classes": classes_count,
        "functions": functions_count,
        "dependencies": deps_count,
        "services": services,
        "controllers": controllers,
        "repositories": repos,
        "health_score": health_score
    }

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repository(
    id: UUID,
    service: IngestionService = Depends(get_ingestion_service)
):
    success = service.delete_repository(id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found."
        )
