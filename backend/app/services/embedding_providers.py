from abc import ABC, abstractmethod
from typing import List
import httpx
import logging
from openai import OpenAI
from ..config import settings

logger = logging.getLogger("codeatlas.embedding_providers")

class EmbeddingProvider(ABC):
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        pass

class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAIEmbeddingProvider")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "text-embedding-3-small"
        self.dimension = 1536
        
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise
            
    def get_dimension(self) -> int:
        return self.dimension

class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip('/')
        self.model = "nomic-embed-text"
        self.dimension = 768
        
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/api/embed",
                    json={
                        "model": self.model,
                        "input": texts
                    },
                    timeout=300.0
                )
                if response.status_code == 200:
                    data = response.json()
                    if "embeddings" in data:
                        return data["embeddings"]
                
                # Fallback to single requests if /api/embed is not available or fails
                logger.warning("Ollama /api/embed failed or returned unexpected data, falling back to /api/embeddings")
                for text in texts:
                    res = client.post(
                        f"{self.base_url}/api/embeddings",
                        json={
                            "model": self.model,
                            "prompt": text
                        },
                        timeout=300.0
                    )
                    res.raise_for_status()
                    embeddings.append(res.json()["embedding"])
            return embeddings
        except Exception as e:
            logger.error(f"Ollama embedding failed: {e}")
            raise
            
    def get_dimension(self) -> int:
        return self.dimension
