import enum
import uuid
from sqlalchemy import Column, String, Integer, DateTime, func, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base

class RepositoryStatus(str, enum.Enum):
    PENDING = "pending"
    CLONING = "cloning"
    INDEXED = "indexed"
    FAILED = "failed"

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_url = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    default_branch = Column(String, nullable=False, default="main")
    local_path = Column(String, nullable=False)
    status = Column(Enum(RepositoryStatus), nullable=False, default=RepositoryStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    code_files = relationship("CodeFile", back_populates="repository", cascade="all, delete-orphan")

class CodeFile(Base):
    __tablename__ = "code_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    repository = relationship("Repository", back_populates="code_files")
    classes = relationship("CodeClass", back_populates="code_file", cascade="all, delete-orphan")
    functions = relationship("CodeFunction", back_populates="code_file", cascade="all, delete-orphan")
    imports = relationship("CodeImport", back_populates="code_file", cascade="all, delete-orphan")

class CodeClass(Base):
    __tablename__ = "code_classes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code_file_id = Column(UUID(as_uuid=True), ForeignKey("code_files.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    start_line = Column(Integer)
    end_line = Column(Integer)
    docstring = Column(String)
    parent_class_names = Column(JSON, default=list)

    code_file = relationship("CodeFile", back_populates="classes")

class CodeFunction(Base):
    __tablename__ = "code_functions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code_file_id = Column(UUID(as_uuid=True), ForeignKey("code_files.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    start_line = Column(Integer)
    end_line = Column(Integer)
    docstring = Column(String)
    calls = Column(JSON, default=list)
    
    code_file = relationship("CodeFile", back_populates="functions")

class CodeImport(Base):
    __tablename__ = "code_imports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_file_id = Column(UUID(as_uuid=True), ForeignKey("code_files.id", ondelete="CASCADE"), nullable=False)
    imported_module = Column(String, nullable=False, index=True)
    import_type = Column(String, nullable=False) # e.g., 'import', 'from'
    line_number = Column(Integer)

    code_file = relationship("CodeFile", back_populates="imports")

class CodeGraphEdge(Base):
    __tablename__ = "code_graph_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    
    # Polymorphic Source Node
    source_type = Column(String, nullable=False) # 'file', 'class', 'function'
    source_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Polymorphic Target Node
    target_type = Column(String, nullable=False) # 'file', 'class', 'function'
    target_id = Column(UUID(as_uuid=True), nullable=False)
    
    edge_type = Column(String, nullable=False) # 'imports', 'inherits', 'calls', 'instantiates'

    repository = relationship("Repository")

class DocumentType(str, enum.Enum):
    ARCHITECTURE = "architecture"
    SERVICE = "service"
    API = "api"
    ONBOARDING = "onboarding"
    IMPACT = "impact"

class DocumentStatus(str, enum.Enum):
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

class GeneratedDocument(Base):
    __tablename__ = "generated_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    target_node_id = Column(UUID(as_uuid=True), nullable=True)
    content_markdown = Column(String, nullable=True)
    content_html = Column(String, nullable=True)
    status = Column(Enum(DocumentStatus), nullable=False, default=DocumentStatus.GENERATING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    repository = relationship("Repository")

