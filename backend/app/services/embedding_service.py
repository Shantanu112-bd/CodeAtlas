import os
import uuid
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from ..config import settings
from ..models import Repository, CodeFile, CodeClass, CodeFunction
from .entity_summarization_service import EntitySummarizationService

logger = logging.getLogger("codeatlas.embedding")

class EmbeddingService:
    def __init__(self, db: Session):
        self.db = db
        self.collection_name = "codeatlas_nodes"
        
        # Initialize OpenAI
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
        # Initialize Qdrant
        self.qdrant_client = None
        if settings.QDRANT_URL:
            self.qdrant_client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
            )
            self._ensure_collection()

    def _ensure_collection(self):
        if not self.qdrant_client:
            return
            
        try:
            collections = self.qdrant_client.get_collections().collections
            if not any(c.name == self.collection_name for c in collections):
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to ensure Qdrant collection: {e}")

    def embed_repository(self, repository_id: uuid.UUID) -> bool:
        if not self.openai_client or not self.qdrant_client:
            logger.warning("EmbeddingService not fully configured. Skipping.")
            return False

        repo = self.db.query(Repository).filter(Repository.id == repository_id).first()
        if not repo:
            logger.error(f"Repository {repository_id} not found.")
            return False

        logger.info(f"Starting embedding generation for {repo.name}")

        summarization_service = EntitySummarizationService(self.db)
        summaries = summarization_service.generate_summaries(repository_id)

        if not summaries:
            logger.info("No entity summaries generated to embed.")
            return True

        # Batch API requests (OpenAI allows max 2048 per batch, but usually smaller is safer for token limits)
        BATCH_SIZE = 100
        for i in range(0, len(summaries), BATCH_SIZE):
            batch = summaries[i:i+BATCH_SIZE]
            batch_texts = [m["content"] for m in batch]

            try:
                response = self.openai_client.embeddings.create(
                    input=batch_texts,
                    model="text-embedding-3-small"
                )
                
                points = []
                for idx, emb in enumerate(response.data):
                    meta = batch[idx]
                    points.append(
                        PointStruct(
                            id=meta["id"],
                            vector=emb.embedding,
                            payload=meta
                        )
                    )
                
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                
                logger.info(f"Embedded and upserted batch {i//BATCH_SIZE + 1} ({len(points)} entities)")
            except Exception as e:
                logger.error(f"Error during embedding batch {i//BATCH_SIZE + 1}: {e}")
                # We could retry here in a real production system

        logger.info(f"Successfully embedded repository {repository_id} with graph-aware summaries.")
        return True
