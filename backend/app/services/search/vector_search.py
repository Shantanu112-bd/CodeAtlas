import logging
from typing import List, Dict, Any
from uuid import UUID

from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from ...config import settings

logger = logging.getLogger("codeatlas.search.vector")

class VectorSearchService:
    def __init__(self):
        self.collection_name = "codeatlas_nodes"
        
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
        self.qdrant_client = None
        if settings.QDRANT_URL:
            self.qdrant_client = AsyncQdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
            )

    async def _get_embedding(self, text: str) -> List[float]:
        if not self.openai_client:
            logger.error("OpenAI client not configured for embedding generation.")
            return []
            
        try:
            response = await self.openai_client.embeddings.create(
                input=[text],
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            return []

    async def search(self, repository_id: UUID, query: str, top_k: int = 10, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Perform a semantic vector search restricted by repository_id.
        """
        if not self.qdrant_client:
            logger.error("Qdrant client not configured.")
            return []
            
        vector = await self._get_embedding(query)
        if not vector:
            return []
            
        # Filter by repository_id to restrict search scope
        repo_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="repository_id",
                    match=models.MatchValue(value=str(repository_id))
                )
            ]
        )
        
        try:
            results = await self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                query_filter=repo_filter,
                limit=top_k,
                score_threshold=threshold
            )
            
            # Map Qdrant points back to a dictionary format
            formatted_results = []
            for hit in results:
                formatted_results.append({
                    "id": hit.payload.get("id"),
                    "node_type": hit.payload.get("node_type"),
                    "name": hit.payload.get("name"),
                    "file_path": hit.payload.get("file_path"),
                    "content": hit.payload.get("content"),
                    "score": hit.score,
                    "search_type": "vector"
                })
                
            return formatted_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
