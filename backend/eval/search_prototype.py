import logging
from typing import List, Dict, Any

class SearchPrototype:
    def __init__(self, db_session, qdrant_client, openai_client):
        self.db = db_session
        self.qdrant = qdrant_client
        self.openai = openai_client

    def _get_embedding(self, query: str) -> List[float]:
        if not self.openai:
            return [0.0] * 1536
        response = self.openai.embeddings.create(
            input=[query],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    def vector_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Standard Vector Search using Qdrant cosine similarity.
        """
        if not self.qdrant:
            return []
            
        vector = self._get_embedding(query)
        results = self.qdrant.search(
            collection_name="codeatlas_nodes",
            query_vector=vector,
            limit=top_k
        )
        
        return [
            {
                "id": hit.payload.get("id"),
                "node_type": hit.payload.get("node_type"),
                "name": hit.payload.get("name"),
                "file_path": hit.payload.get("file_path"),
                "score": hit.score,
                "strategy": "vector"
            }
            for hit in results
        ]

    def graph_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Mock Graph Search using naive text matching to find an entry node,
        then returning immediate graph neighbors.
        """
        # In a real implementation, this would use a BM25 or tf-idf search
        # on the Postgres tables to find a seed node, then perform a recursive
        # CTE to fetch graph edges up to a certain depth.
        # This is stubbed for evaluation harnesses.
        return []

    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Hybrid Search combining Vector and Graph search using Reciprocal Rank Fusion (RRF).
        """
        vector_results = self.vector_search(query, top_k=top_k * 2)
        graph_results = self.graph_search(query, top_k=top_k * 2)
        
        # RRF Implementation
        k = 60
        rrf_scores = {}
        
        # Helper to merge items
        items_map = {}
        
        for rank, item in enumerate(vector_results):
            id_ = item["id"]
            items_map[id_] = item
            rrf_scores[id_] = rrf_scores.get(id_, 0) + 1.0 / (k + rank + 1)
            
        for rank, item in enumerate(graph_results):
            id_ = item["id"]
            if id_ not in items_map:
                items_map[id_] = item
            rrf_scores[id_] = rrf_scores.get(id_, 0) + 1.0 / (k + rank + 1)
            
        sorted_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        top_results = []
        for id_, score in sorted_rrf[:top_k]:
            merged_item = items_map[id_].copy()
            merged_item["score"] = score
            merged_item["strategy"] = "hybrid"
            top_results.append(merged_item)
            
        return top_results
