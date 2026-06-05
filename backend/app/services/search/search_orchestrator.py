import asyncio
import logging
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from .intent_service import IntentDetectionService
from .vector_search import VectorSearchService
from .graph_search import GraphSearchService
from .metadata_search import MetadataSearchService
from .ranking_engine import RankingEngine
from .context_expansion import ContextExpansionService

logger = logging.getLogger("codeatlas.search.orchestrator")

class SearchOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.intent_service = IntentDetectionService()
        self.vector_search = VectorSearchService()
        self.graph_search = GraphSearchService(self.db)
        self.metadata_search = MetadataSearchService(self.db)
        self.ranking_engine = RankingEngine()
        self.context_expansion = ContextExpansionService(self.db)

    async def hybrid_search(self, repository_id: UUID, query: str) -> Dict[str, Any]:
        """
        Executes the full hybrid semantic search pipeline concurrently.
        """
        logger.info(f"Starting hybrid search for query: '{query}' in repo: {repository_id}")
        
        # Phase 1-4: Execute Intent, Vector, Graph, and Metadata searches concurrently
        intent_task = asyncio.create_task(self.intent_service.detect_intent(query))
        vector_task = asyncio.create_task(self.vector_search.search(repository_id, query, top_k=15))
        graph_task = asyncio.create_task(self.graph_search.search(repository_id, query, limit=15))
        metadata_task = asyncio.create_task(self.metadata_search.search(repository_id, query, limit=5))
        
        # Wait for all to complete
        intent, vector_results, graph_results, metadata_results = await asyncio.gather(
            intent_task, vector_task, graph_task, metadata_task, return_exceptions=True
        )
        
        # Handle potential exceptions gracefully
        if isinstance(intent, Exception):
            logger.error(f"Intent detection failed: {intent}")
            intent = "code_discovery"
        if isinstance(vector_results, Exception):
            logger.error(f"Vector search failed: {vector_results}")
            vector_results = []
        if isinstance(graph_results, Exception):
            logger.error(f"Graph search failed: {graph_results}")
            graph_results = []
        if isinstance(metadata_results, Exception):
            logger.error(f"Metadata search failed: {metadata_results}")
            metadata_results = []

        # Phase 5: Ranking
        ranked_results = self.ranking_engine.rank_results(
            vector_results=vector_results,
            graph_results=graph_results,
            metadata_results=metadata_results,
            limit=10
        )
        
        # Phase 6: Context Expansion
        graph_context = await self.context_expansion.expand_context(repository_id, ranked_results)
        
        # Construct response
        # Using a fixed high confidence for MVP, in reality we'd calculate this based on top scores
        confidence = 0.95 if ranked_results and ranked_results[0].get("score", 0) > 0.5 else 0.45
        
        return {
            "intent": intent,
            "confidence": confidence,
            "results": ranked_results,
            "graph_context": graph_context
        }
