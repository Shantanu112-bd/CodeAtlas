import uuid
import pytest
from unittest.mock import MagicMock, patch

from app.models import Repository, CodeFile, CodeClass, CodeFunction, CodeGraphEdge
from app.services.embedding_service import EmbeddingService

@pytest.fixture
def mock_db():
    db = MagicMock()
    
    repo_id = uuid.uuid4()
    repo = Repository(id=repo_id, name="test-repo", owner="test-owner", default_branch="main", local_path="/tmp/test-repo")
    
    file_id = uuid.uuid4()
    code_file = CodeFile(id=file_id, repository_id=repo_id, file_path="test.py")
    
    code_class = CodeClass(id=uuid.uuid4(), code_file_id=file_id, name="TestClass", start_line=1, end_line=3)
    code_func = CodeFunction(id=uuid.uuid4(), code_file_id=file_id, name="test_func", start_line=5, end_line=7)
    
    edge = CodeGraphEdge(
        id=uuid.uuid4(),
        repository_id=repo_id,
        source_type="function",
        source_id=code_func.id,
        target_type="class",
        target_id=code_class.id,
        edge_type="instantiates"
    )

    def mock_query_filter_first(*args, **kwargs):
        return repo

    def mock_query_filter_all(*args, **kwargs):
        return []

    # Configure mock
    db.query().filter().first.side_effect = lambda: repo
    
    # We will just patch the summarization service directly instead of deep-mocking db queries
    return db, repo_id

@patch("app.services.embedding_service.OpenAI")
@patch("app.services.embedding_service.QdrantClient")
@patch("app.services.embedding_service.EntitySummarizationService")
def test_embed_repository_graph_aware(mock_summarizer_class, mock_qdrant, mock_openai, mock_db):
    db, repo_id = mock_db
    
    # Mock Summarizer
    mock_summarizer = mock_summarizer_class.return_value
    mock_summarizer.generate_summaries.return_value = [
        {"id": "1", "node_type": "repository", "content": "Repo context"},
        {"id": "2", "node_type": "class", "content": "Class context with instantiation edge"},
    ]

    service = EmbeddingService(db)
    service.openai_client = mock_openai()
    service.qdrant_client = mock_qdrant()

    # Mock OpenAI
    mock_response = MagicMock()
    mock_emb1 = MagicMock()
    mock_emb1.embedding = [0.1, 0.2]
    mock_emb2 = MagicMock()
    mock_emb2.embedding = [0.3, 0.4]
    mock_response.data = [mock_emb1, mock_emb2]
    service.openai_client.embeddings.create.return_value = mock_response

    # Execute
    result = service.embed_repository(repo_id)

    # Verify
    assert result is True
    
    # Check OpenAI called with 2 rich contexts
    create_call = service.openai_client.embeddings.create.call_args
    assert len(create_call.kwargs['input']) == 2
    assert create_call.kwargs['input'][0] == "Repo context"
    assert create_call.kwargs['input'][1] == "Class context with instantiation edge"

    # Check Qdrant
    upsert_call = service.qdrant_client.upsert.call_args
    assert len(upsert_call.kwargs['points']) == 2
    assert upsert_call.kwargs['points'][0].payload['node_type'] == "repository"
    assert upsert_call.kwargs['points'][1].payload['node_type'] == "class"
