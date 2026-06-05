import logging
import asyncio
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ...models import CodeClass, CodeFunction, CodeFile, CodeGraphEdge

logger = logging.getLogger("codeatlas.search.graph")

class GraphSearchService:
    def __init__(self, db: Session):
        self.db = db

    def _sync_search(self, repository_id: UUID, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Sync blocking search logic to find entry nodes by name, then fetch immediate neighbors.
        """
        # Split query into keywords
        keywords = [k.strip() for k in query.lower().split() if len(k) > 2]
        if not keywords:
            return []

        results = []
        found_ids = set()

        # Helper to score keywords
        def score_match(name: str) -> float:
            name_lower = name.lower()
            score = 0.0
            for k in keywords:
                if k in name_lower:
                    score += 0.5
                    if k == name_lower:
                        score += 0.5 # exact match boost
            return score

        # 1. Find Entry Nodes (Files)
        files = self.db.query(CodeFile).filter(CodeFile.repository_id == repository_id).all()
        for f in files:
            score = score_match(f.file_path)
            if score > 0:
                found_ids.add(str(f.id))
                results.append({
                    "id": str(f.id),
                    "node_type": "file",
                    "name": f.file_path,
                    "file_path": f.file_path,
                    "score": score,
                    "search_type": "graph"
                })

        # 2. Find Entry Nodes (Classes & Functions)
        classes = self.db.query(CodeClass).join(CodeFile).filter(CodeFile.repository_id == repository_id).all()
        for c in classes:
            score = score_match(c.name)
            if score > 0:
                found_ids.add(str(c.id))
                results.append({
                    "id": str(c.id),
                    "node_type": "class",
                    "name": c.name,
                    "file_path": c.code_file.file_path,
                    "score": score,
                    "search_type": "graph"
                })

        functions = self.db.query(CodeFunction).join(CodeFile).filter(CodeFile.repository_id == repository_id).all()
        for fn in functions:
            score = score_match(fn.name)
            if score > 0:
                found_ids.add(str(fn.id))
                results.append({
                    "id": str(fn.id),
                    "node_type": "function",
                    "name": fn.name,
                    "file_path": fn.code_file.file_path,
                    "score": score,
                    "search_type": "graph"
                })

        # Sort by score and take top seed nodes
        results = sorted(results, key=lambda x: x["score"], reverse=True)[:5]
        seed_ids = [r["id"] for r in results]

        # 3. Graph Expansion (1 hop)
        if seed_ids:
            edges = self.db.query(CodeGraphEdge).filter(
                CodeGraphEdge.repository_id == repository_id,
                or_(
                    CodeGraphEdge.source_id.in_(seed_ids),
                    CodeGraphEdge.target_id.in_(seed_ids)
                )
            ).all()

            # Just bump the score of nodes that are connected to seed nodes
            # We add target/source nodes to results with lower score
            expansion_score = 0.3
            for e in edges:
                if str(e.target_id) not in found_ids:
                    found_ids.add(str(e.target_id))
                    results.append({
                        "id": str(e.target_id),
                        "node_type": e.target_type,
                        "name": f"{e.target_type}_{e.target_id}", # Placeholder name
                        "file_path": "unknown",
                        "score": expansion_score,
                        "search_type": "graph"
                    })
                if str(e.source_id) not in found_ids:
                    found_ids.add(str(e.source_id))
                    results.append({
                        "id": str(e.source_id),
                        "node_type": e.source_type,
                        "name": f"{e.source_type}_{e.source_id}", # Placeholder name
                        "file_path": "unknown",
                        "score": expansion_score,
                        "search_type": "graph"
                    })

        # Limit final output
        return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]

    async def search(self, repository_id: UUID, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Async wrapper for Graph Search.
        """
        try:
            return await asyncio.to_thread(self._sync_search, repository_id, query, limit)
        except Exception as e:
            logger.error(f"Graph search failed: {e}")
            return []
