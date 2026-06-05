import os
import time
import uuid
import sys
import asyncio
import json
import shutil
import subprocess
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import Base
from app.models import Repository, CodeFile, CodeClass, CodeFunction, CodeGraphEdge, RepositoryStatus
from app.services.ingestion_service import IngestionService
from app.repositories.repository_repo import RepositoryRepository
from app.services.ast_service import ASTService
from app.services.embedding_service import EmbeddingService
from app.services.search.search_orchestrator import SearchOrchestrator
from app.config import settings

async def async_main():
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    repo_db = RepositoryRepository(db)
    ingest_service = IngestionService(repo_db)
    
    github_url = "https://github.com/Shantanu112-bd/CodeAtlas"
    
    print("1. Preparing Repository...")
    existing = repo_db.get_by_url(github_url)
    if existing:
        print("   Deleting existing repository record...")
        ingest_service.delete_repository(existing.id)
        db.commit()
        
    repo = ingest_service.create_repository_record(github_url)
    db.commit()
    
    print("2. Cloning Repository...")
    start_clone = time.time()
    
    if os.path.exists(repo.local_path):
        shutil.rmtree(repo.local_path)
    os.makedirs(os.path.dirname(repo.local_path), exist_ok=True)
    subprocess.run(["git", "clone", "--depth", "1", repo.github_url, repo.local_path], check=True, capture_output=True)
    
    repo.status = RepositoryStatus.INDEXED
    db.commit()
    clone_time = time.time() - start_clone
    print(f"   Clone completed in {clone_time:.2f}s")
    
    print("3. Running AST Analysis & Knowledge Graph Generation...")
    start_ast = time.time()
    ast_service = ASTService(db)
    ast_service.analyze_repository(repo.id)
    ast_time = time.time() - start_ast
    print(f"   AST Analysis completed in {ast_time:.2f}s")
    
    print("4. Generating Graph-Aware Embeddings...")
    start_embed = time.time()
    embedding_service = EmbeddingService(db)
    embedding_service.embed_repository(repo.id)
    embed_time = time.time() - start_embed
    print(f"   Embeddings generated in {embed_time:.2f}s")
    
    print("5. Collecting Metrics...")
    files_count = db.query(CodeFile).filter_by(repository_id=repo.id).count()
    classes_count = db.query(CodeClass).join(CodeFile).filter(CodeFile.repository_id == repo.id).count()
    functions_count = db.query(CodeFunction).join(CodeFile).filter(CodeFile.repository_id == repo.id).count()
    edges_count = db.query(CodeGraphEdge).filter_by(repository_id=repo.id).count()
    
    collection_info = embedding_service.qdrant_client.get_collection(embedding_service.collection_name)
    vectors_count = collection_info.points_count
    
    metrics = {
        "files": files_count,
        "classes": classes_count,
        "functions": functions_count,
        "edges": edges_count,
        "vectors": vectors_count,
        "clone_time": clone_time,
        "ast_time": ast_time,
        "embed_time": embed_time,
        "collection_size": collection_info.points_count
    }
    
    print(f"   Metrics: Files={files_count}, Classes={classes_count}, Functions={functions_count}")
    print(f"   Edges={edges_count}, Vectors={vectors_count}")
    
    print("6. Executing Test Queries...")
    queries = [
        "How does repository ingestion work?",
        "Show authentication implementation.",
        "What depends on EmbeddingService?",
        "Explain hybrid search architecture.",
        "What breaks if ASTService changes?"
    ]
    
    search_results = []
    search_service = SearchOrchestrator(db)
    
    for q in queries:
        print(f"   Query: '{q}'")
        start_q = time.time()
        res = await search_service.hybrid_search(repository_id=repo.id, query=q)
        q_time = time.time() - start_q
        
        top_results = []
        for r in res.get("results", [])[:3]:
            top_results.append({
                "type": r.get("node_type"),
                "name": r.get("name"),
                "score": r.get("score")
            })
            
        search_results.append({
            "query": q,
            "time": q_time,
            "intent": res.get("intent"),
            "results": top_results
        })
        print(f"     -> Returned {len(res.get('results', []))} results in {q_time:.2f}s")
        
    db.close()
    
    report_data = {
        "metrics": metrics,
        "searches": search_results
    }
    
    with open("/tmp/large_repo_validation_data.json", "w") as f:
        json.dump(report_data, f, indent=2)
        
    print("\nValidation completed successfully! Data saved to /tmp/large_repo_validation_data.json")

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
