from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, literal
from uuid import UUID
from ..database import get_db
from ..models import CodeGraphEdge, CodeFunction, CodeClass

router = APIRouter(prefix="/repositories", tags=["Graph Knowledge"])

@router.get("/{id}/functions/{function_id}/callers")
def get_function_callers(id: UUID, function_id: UUID, depth: int = 5, db: Session = Depends(get_db)):
    # Recursive query going UP the call chain (who calls this?)
    edge_cte = select(CodeGraphEdge.source_id.label('node_id'), literal(1).label('depth')).where(
        and_(CodeGraphEdge.target_id == function_id, CodeGraphEdge.edge_type == 'calls')
    ).cte(name='caller_chain', recursive=True)

    edge_alias = edge_cte.alias()
    edge_cte = edge_cte.union(
        select(CodeGraphEdge.source_id, edge_alias.c.depth + 1).where(
            and_(
                CodeGraphEdge.target_id == edge_alias.c.node_id,
                CodeGraphEdge.edge_type == 'calls',
                edge_alias.c.depth < depth
            )
        )
    )

    query = select(CodeFunction).where(CodeFunction.id.in_(select(edge_cte.c.node_id)))
    callers = db.execute(query).scalars().all()
    
    return [
        {"id": c.id, "name": c.name, "start_line": c.start_line, "end_line": c.end_line}
        for c in callers
    ]

@router.get("/{id}/functions/{function_id}/callees")
def get_function_callees(id: UUID, function_id: UUID, depth: int = 5, db: Session = Depends(get_db)):
    # Recursive query going DOWN the call chain (what does this call?)
    edge_cte = select(CodeGraphEdge.target_id.label('node_id'), literal(1).label('depth')).where(
        and_(CodeGraphEdge.source_id == function_id, CodeGraphEdge.edge_type == 'calls')
    ).cte(name='callee_chain', recursive=True)

    edge_alias = edge_cte.alias()
    edge_cte = edge_cte.union(
        select(CodeGraphEdge.target_id, edge_alias.c.depth + 1).where(
            and_(
                CodeGraphEdge.source_id == edge_alias.c.node_id,
                CodeGraphEdge.edge_type == 'calls',
                edge_alias.c.depth < depth
            )
        )
    )

    query = select(CodeFunction).where(CodeFunction.id.in_(select(edge_cte.c.node_id)))
    callees = db.execute(query).scalars().all()
    
    return [
        {"id": c.id, "name": c.name, "start_line": c.start_line, "end_line": c.end_line}
        for c in callees
    ]

@router.get("/{id}/classes/{class_id}/inheritance")
def get_class_inheritance(id: UUID, class_id: UUID, db: Session = Depends(get_db)):
    # Ancestors (who does this class inherit from?)
    ancestors_cte = select(CodeGraphEdge.target_id.label('node_id'), literal(1).label('depth')).where(
        and_(CodeGraphEdge.source_id == class_id, CodeGraphEdge.edge_type == 'inherits')
    ).cte(name='ancestor_chain', recursive=True)

    ancestors_alias = ancestors_cte.alias()
    ancestors_cte = ancestors_cte.union(
        select(CodeGraphEdge.target_id, ancestors_alias.c.depth + 1).where(
            and_(
                CodeGraphEdge.source_id == ancestors_alias.c.node_id,
                CodeGraphEdge.edge_type == 'inherits',
                ancestors_alias.c.depth < 10
            )
        )
    )

    # Descendants (who inherits from this class?)
    descendants_cte = select(CodeGraphEdge.source_id.label('node_id'), literal(1).label('depth')).where(
        and_(CodeGraphEdge.target_id == class_id, CodeGraphEdge.edge_type == 'inherits')
    ).cte(name='descendant_chain', recursive=True)

    descendants_alias = descendants_cte.alias()
    descendants_cte = descendants_cte.union(
        select(CodeGraphEdge.source_id, descendants_alias.c.depth + 1).where(
            and_(
                CodeGraphEdge.target_id == descendants_alias.c.node_id,
                CodeGraphEdge.edge_type == 'inherits',
                descendants_alias.c.depth < 10
            )
        )
    )

    ancestors = db.execute(select(CodeClass).where(CodeClass.id.in_(select(ancestors_cte.c.node_id)))).scalars().all()
    descendants = db.execute(select(CodeClass).where(CodeClass.id.in_(select(descendants_cte.c.node_id)))).scalars().all()

    return {
        "ancestors": [{"id": c.id, "name": c.name} for c in ancestors],
        "descendants": [{"id": c.id, "name": c.name} for c in descendants]
    }

@router.get("/{id}/graph/impact/{node_id}")
def get_graph_impact(id: UUID, node_id: UUID, db: Session = Depends(get_db)):
    """
    Reverse Dependency Analysis: What breaks if this node changes?
    (Fetches everything that points TO this node)
    """
    edges = db.execute(
        select(CodeGraphEdge).where(
            and_(
                CodeGraphEdge.repository_id == id,
                CodeGraphEdge.target_id == node_id
            )
        )
    ).scalars().all()
    return [{"source_id": e.source_id, "source_type": e.source_type, "edge_type": e.edge_type} for e in edges]

@router.get("/{id}/graph/dependencies/{node_id}")
def get_graph_dependencies(id: UUID, node_id: UUID, db: Session = Depends(get_db)):
    """
    Forward Dependency Analysis: What does this node depend on?
    (Fetches everything this node points TO)
    """
    edges = db.execute(
        select(CodeGraphEdge).where(
            and_(
                CodeGraphEdge.repository_id == id,
                CodeGraphEdge.source_id == node_id
            )
        )
    ).scalars().all()
    return [{"target_id": e.target_id, "target_type": e.target_type, "edge_type": e.edge_type} for e in edges]

@router.get("/{id}/graph/architecture")
def get_architecture_view(id: UUID, db: Session = Depends(get_db)):
    """
    Generates a high-level layered architecture view.
    Groups classes by Service, Controller, Repository.
    """
    classes = db.execute(
        select(CodeClass).join(CodeClass.code_file).where(
            CodeClass.code_file.has(repository_id=id)
        )
    ).scalars().all()
    
    architecture = {
        "controllers": [],
        "services": [],
        "repositories": [],
        "models": [],
        "other": []
    }
    
    for c in classes:
        name_lower = c.name.lower()
        if "controller" in name_lower or "router" in name_lower:
            architecture["controllers"].append({"id": c.id, "name": c.name})
        elif "service" in name_lower or "manager" in name_lower:
            architecture["services"].append({"id": c.id, "name": c.name})
        elif "repository" in name_lower or "dao" in name_lower:
            architecture["repositories"].append({"id": c.id, "name": c.name})
        elif "model" in name_lower or "schema" in name_lower:
            architecture["models"].append({"id": c.id, "name": c.name})
        else:
            architecture["other"].append({"id": c.id, "name": c.name})
            
    return architecture
