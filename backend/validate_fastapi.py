import os
import time
import uuid
import sys
import asyncio
import json
import shutil
import subprocess
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import Base
from app.models import Repository, CodeFile, CodeClass, CodeFunction, CodeGraphEdge, RepositoryStatus
from app.services.ingestion_service import IngestionService
from app.repositories.repository_repo import RepositoryRepository
from app.services.ast_service import ASTService
from app.services.embedding_service import EmbeddingService
from app.services.search.search_orchestrator import SearchOrchestrator
from app.config import settings

def get_postgres_db_size(conn):
    try:
        return conn.execute(text("SELECT pg_database_size('codeatlas')")).scalar()
    except Exception as e:
        print(f"Error getting PG DB size: {e}")
        return 0

def get_qdrant_storage_size():
    try:
        res = subprocess.run(["docker", "exec", "goofy_albattani", "du", "-s", "/qdrant/storage"], capture_output=True, text=True, check=True)
        size_kb = int(res.stdout.split()[0])
        return size_kb * 1024 # return bytes
    except Exception as e:
        print(f"Error getting Qdrant storage size: {e}")
        return 0

async def async_main():
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    conn = engine.connect()
    
    repo_db = RepositoryRepository(db)
    ingest_service = IngestionService(repo_db)
    
    github_url = "https://github.com/fastapi/fastapi"
    
    print("1. Preparing Repository...")
    existing = repo_db.get_by_url(github_url)
    if existing:
        print("   Deleting existing repository record...")
        ingest_service.delete_repository(existing.id)
        db.commit()
        
    repo = ingest_service.create_repository_record(github_url)
    db.commit()
    
    # Measure initial storage
    init_pg_size = get_postgres_db_size(conn)
    init_qd_size = get_qdrant_storage_size()
    
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
    
    print("4. Generating Graph-Aware Embeddings & Indexing Qdrant...")
    start_embed = time.time()
    embedding_service = EmbeddingService(db)
    embedding_service.embed_repository(repo.id)
    embed_time = time.time() - start_embed
    print(f"   Embeddings generated and indexed in {embed_time:.2f}s")
    
    # Measure post storage
    post_pg_size = get_postgres_db_size(conn)
    post_qd_size = get_qdrant_storage_size()
    
    pg_growth = post_pg_size - init_pg_size
    qd_growth = post_qd_size - init_qd_size
    
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
        "init_pg_size": init_pg_size,
        "post_pg_size": post_pg_size,
        "pg_growth": pg_growth,
        "init_qd_size": init_qd_size,
        "post_qd_size": post_qd_size,
        "qd_growth": qd_growth,
    }
    
    print(f"   Metrics: Files={files_count}, Classes={classes_count}, Functions={functions_count}")
    print(f"   Edges={edges_count}, Vectors={vectors_count}")
    print(f"   Postgres Growth: {pg_growth / 1024:.2f} KB, Qdrant Growth: {qd_growth / 1024:.2f} KB")
    
    print("6. Executing Specific Test Queries...")
    queries = {
        "architecture": [
            "Explain FastAPI architecture",
            "Show routing system",
            "Show dependency injection system"
        ],
        "dependency": [
            "What depends on APIRouter?",
            "What imports Depends?"
        ],
        "impact": [
            "What breaks if APIRouter changes?",
            "What depends on FastAPI class?"
        ]
    }
    
    search_results = {}
    search_service = SearchOrchestrator(db)
    
    for category, category_queries in queries.items():
        search_results[category] = []
        for q in category_queries:
            print(f"   Query ({category}): '{q}'")
            start_q = time.time()
            res = await search_service.hybrid_search(repository_id=repo.id, query=q)
            q_time = time.time() - start_q
            
            top_results = []
            for r in res.get("results", [])[:5]:
                top_results.append({
                    "type": r.get("node_type"),
                    "name": r.get("name"),
                    "score": r.get("score"),
                    "file_path": r.get("file_path")
                })
                
            search_results[category].append({
                "query": q,
                "time": q_time,
                "intent": res.get("intent"),
                "results": top_results
            })
            print(f"     -> Returned {len(res.get('results', []))} results in {q_time:.2f}s")
            
    conn.close()
    db.close()
    
    report_data = {
        "metrics": metrics,
        "searches": search_results
    }
    
    with open("/tmp/fastapi_validation_data.json", "w") as f:
        json.dump(report_data, f, indent=2)
        
    print("\nValidation completed successfully! Data saved to /tmp/fastapi_validation_data.json")

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
