import os
import time
import uuid
import sys
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import Base
from app.models import Repository, CodeFile, CodeClass, CodeFunction, RepositoryStatus
from app.services.embedding_service import EmbeddingService
from app.services.search.search_orchestrator import SearchOrchestrator
from app.config import settings

async def async_main():
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    print("1. Creating dummy repository...")
    repo_id = uuid.uuid4()
    repo = Repository(
        id=repo_id,
        name="test_validation_repo",
        owner="tester",
        github_url="https://github.com/tester/test_validation_repo",
        default_branch="main",
        local_path="/tmp/test_validation_repo",
        status=RepositoryStatus.INDEXED
    )
    db.add(repo)
    
    file_id = uuid.uuid4()
    code_file = CodeFile(
        id=file_id,
        repository_id=repo_id,
        file_path="src/main.py"
    )
    db.add(code_file)
    
    # Create the actual file on disk so summarization can read it
    os.makedirs("/tmp/test_validation_repo/src", exist_ok=True)
    with open("/tmp/test_validation_repo/src/main.py", "w") as f:
        f.write("class AuthManager:\n    def login(self):\n        pass\n")
    
    class_id = uuid.uuid4()
    code_class = CodeClass(
        id=class_id,
        code_file_id=file_id,
        name="AuthManager",
        start_line=1,
        end_line=3
    )
    db.add(code_class)
    
    func_id = uuid.uuid4()
    code_func = CodeFunction(
        id=func_id,
        code_file_id=file_id,
        name="login",
        start_line=2,
        end_line=3
    )
    db.add(code_func)
    
    db.commit()
    
    print("2. Running embedding service...")
    start_time = time.time()
    embedding_service = EmbeddingService(db)
    
    collection_name = embedding_service.collection_name
    provider_name = embedding_service.provider.__class__.__name__
    dimension = embedding_service.provider.get_dimension()
    
    embedding_service.embed_repository(repo_id)
    embed_time = time.time() - start_time
    
    print(f"3. Verifying Qdrant insertion in {collection_name}...")
    collection_info = embedding_service.qdrant_client.get_collection(collection_name)
    vector_count = collection_info.points_count
    
    print("4. Executing Hybrid Search...")
    search_service = SearchOrchestrator(db)
    search_response = await search_service.hybrid_search(
        query="authentication login",
        repository_id=repo_id
    )
    results = search_response.get("results", [])
    intent = search_response.get("intent", "unknown")
    
    print("\n" + "="*50)
    print("VALIDATION REPORT")
    print("="*50)
    print(f"Provider: {provider_name}")
    print(f"Collection: {collection_name}")
    print(f"Vector Dimension: {dimension}")
    print(f"Embedding Latency: {embed_time:.2f} seconds")
    print(f"Vectors in Collection: {vector_count}")
    print(f"Search Intent: {intent}")
    print(f"Search Results Returned: {len(results)}")
    for res in results:
        print(f" - [{res.get('node_type', 'unknown')}] {res.get('name', res.get('id', 'unknown'))} (Score: {res.get('score', 0):.4f})")
    print("="*50)
    
    # Cleanup
    db.delete(code_func)
    db.delete(code_class)
    db.delete(code_file)
    db.delete(repo)
    db.commit()
    db.close()

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
