from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from uuid import UUID
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.search.search_orchestrator import SearchOrchestrator

router = APIRouter(prefix="/search", tags=["Search"])

class SearchRequest(BaseModel):
    repository_id: UUID
    query: str

class SearchResponse(BaseModel):
    intent: str
    confidence: float
    results: List[Dict[str, Any]]
    graph_context: List[Dict[str, Any]]

@router.post("", response_model=SearchResponse)
async def perform_search(request: SearchRequest, db: Session = Depends(get_db)):
    """
    Executes a Hybrid Semantic Search combining Vector, Graph, and Metadata techniques.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty."
        )
        
    orchestrator = SearchOrchestrator(db)
    
    try:
        response = await orchestrator.hybrid_search(
            repository_id=request.repository_id,
            query=request.query
        )
        return response
    except Exception as e:
        import logging
        logging.getLogger("codeatlas.search.router").error(f"Search endpoint failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during search: {str(e)}"
        )
