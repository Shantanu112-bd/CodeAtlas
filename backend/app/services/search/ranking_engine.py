import logging
from typing import List, Dict, Any

logger = logging.getLogger("codeatlas.search.ranking")

class RankingEngine:
    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k

    def rank_results(self, vector_results: List[Dict], graph_results: List[Dict], metadata_results: List[Dict], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Merge results from different strategies using Reciprocal Rank Fusion (RRF),
        and apply domain-specific boosts.
        """
        rrf_scores = {}
        items_map = {}

        # Helper to apply RRF
        def apply_rrf(results, weight=1.0):
            for rank, item in enumerate(results):
                id_ = item["id"]
                if id_ not in items_map:
                    # Deep copy so we don't modify originals directly
                    items_map[id_] = item.copy()
                    
                score_increment = weight / (self.rrf_k + rank + 1)
                rrf_scores[id_] = rrf_scores.get(id_, 0.0) + score_increment

        # Weighting for strategies
        # Metadata Exact Matches are highly valuable
        apply_rrf(metadata_results, weight=1.5)
        # Vector is the core engine
        apply_rrf(vector_results, weight=1.0)
        # Graph yields contextual neighbors
        apply_rrf(graph_results, weight=0.8)

        # Build final list
        final_results = []
        for id_, score in rrf_scores.items():
            item = items_map[id_]
            
            # Apply Graph Boosting / Dead Code Penalties (Simulated here since we need edges)
            # In a full implementation, we'd query the DB for the count of inward/outward edges.
            # To keep it performant, we assume `context_expansion.py` will fetch this later,
            # or we just rely on RRF. For now, we will just use the RRF score.
            
            item["score"] = round(score, 4)
            final_results.append(item)

        # Sort by final RRF score
        final_results = sorted(final_results, key=lambda x: x["score"], reverse=True)
        return final_results[:limit]
