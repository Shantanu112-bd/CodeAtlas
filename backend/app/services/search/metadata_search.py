import logging
import asyncio
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...models import CodeClass, CodeFunction, CodeFile

logger = logging.getLogger("codeatlas.search.metadata")

class MetadataSearchService:
    def __init__(self, db: Session):
        self.db = db

    def _sync_search(self, repository_id: UUID, query: str, limit: int) -> List[Dict[str, Any]]:
        results = []
        # Extract potential exact match tokens (like a class name)
        tokens = [t.strip() for t in query.split() if len(t.strip()) > 2]
        if not tokens:
            return []

        # Find exact or ILIKE matches in Classes
        for token in tokens:
            pattern = f"%{token}%"
            
            # Search Files
            matched_files = self.db.query(CodeFile).filter(
                CodeFile.repository_id == repository_id,
                CodeFile.file_path.ilike(pattern)
            ).limit(limit).all()
            for f in matched_files:
                score = 0.9 if token.lower() in f.file_path.lower().split('/')[-1] else 0.5
                results.append({
                    "id": str(f.id),
                    "node_type": "file",
                    "name": f.file_path,
                    "file_path": f.file_path,
                    "score": score,
                    "search_type": "metadata"
                })

            # Search Classes
            matched_classes = self.db.query(CodeClass).join(CodeFile).filter(
                CodeFile.repository_id == repository_id,
                CodeClass.name.ilike(pattern)
            ).limit(limit).all()
            for c in matched_classes:
                score = 1.0 if c.name.lower() == token.lower() else 0.7
                results.append({
                    "id": str(c.id),
                    "node_type": "class",
                    "name": c.name,
                    "file_path": c.code_file.file_path,
                    "score": score,
                    "search_type": "metadata"
                })

            # Search Functions
            matched_funcs = self.db.query(CodeFunction).join(CodeFile).filter(
                CodeFile.repository_id == repository_id,
                CodeFunction.name.ilike(pattern)
            ).limit(limit).all()
            for fn in matched_funcs:
                score = 1.0 if fn.name.lower() == token.lower() else 0.6
                results.append({
                    "id": str(fn.id),
                    "node_type": "function",
                    "name": fn.name,
                    "file_path": fn.code_file.file_path,
                    "score": score,
                    "search_type": "metadata"
                })

        # Deduplicate and sort
        unique_results = {}
        for r in results:
            if r["id"] not in unique_results or unique_results[r["id"]]["score"] < r["score"]:
                unique_results[r["id"]] = r
                
        return sorted(list(unique_results.values()), key=lambda x: x["score"], reverse=True)[:limit]

    async def search(self, repository_id: UUID, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            return await asyncio.to_thread(self._sync_search, repository_id, query, limit)
        except Exception as e:
            logger.error(f"Metadata search failed: {e}")
            return []
