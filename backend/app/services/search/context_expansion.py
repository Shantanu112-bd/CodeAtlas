import logging
import asyncio
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ...models import CodeGraphEdge

logger = logging.getLogger("codeatlas.search.expansion")

class ContextExpansionService:
    def __init__(self, db: Session):
        self.db = db

    def _sync_expand(self, repository_id: UUID, result_ids: List[str]) -> List[Dict[str, Any]]:
        if not result_ids:
            return []
            
        edges = self.db.query(CodeGraphEdge).filter(
            CodeGraphEdge.repository_id == repository_id,
            or_(
                CodeGraphEdge.source_id.in_(result_ids),
                CodeGraphEdge.target_id.in_(result_ids)
            )
        ).all()
        
        context = []
        for e in edges:
            context.append({
                "source_id": str(e.source_id),
                "source_type": e.source_type,
                "target_id": str(e.target_id),
                "target_type": e.target_type,
                "edge_type": e.edge_type
            })
            
        return context

    async def expand_context(self, repository_id: UUID, top_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fetch graph connections for the top N results.
        """
        # Take up to top 3 results for expansion
        result_ids = [r["id"] for r in top_results[:3] if "id" in r]
        
        try:
            return await asyncio.to_thread(self._sync_expand, repository_id, result_ids)
        except Exception as e:
            logger.error(f"Context expansion failed: {e}")
            return []
