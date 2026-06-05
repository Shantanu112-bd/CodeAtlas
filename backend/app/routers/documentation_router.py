import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import GeneratedDocument, DocumentType, DocumentStatus
from ..services.documentation_service import DocumentationService

router = APIRouter(prefix="/api/v1/documentation", tags=["documentation"])

class DocumentGenerationRequest(BaseModel):
    repository_id: uuid.UUID
    document_type: DocumentType
    target_node_id: Optional[uuid.UUID] = None
    target_name: Optional[str] = None # For Service or Impact docs

class DocumentResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    document_type: DocumentType
    status: DocumentStatus
    created_at: str
    
    class Config:
        orm_mode = True

@router.post("/generate", response_model=DocumentResponse)
def generate_document(req: DocumentGenerationRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    doc_service = DocumentationService(db)
    
    # In a real system, we might run this in the background, but for simplicity
    # and testing, we run it synchronously here. To avoid timeouts on long LLM calls,
    # background tasks are preferred. For this MVP, we execute immediately.
    try:
        if req.document_type == DocumentType.ARCHITECTURE:
            doc = doc_service.generate_architecture_doc(req.repository_id)
        elif req.document_type == DocumentType.SERVICE:
            if not req.target_name or not req.target_node_id:
                raise HTTPException(status_code=400, detail="target_name and target_node_id required for SERVICE docs")
            doc = doc_service.generate_service_doc(req.repository_id, req.target_name, req.target_node_id)
        elif req.document_type == DocumentType.API:
            doc = doc_service.generate_api_doc(req.repository_id)
        elif req.document_type == DocumentType.ONBOARDING:
            doc = doc_service.generate_onboarding_guide(req.repository_id)
        elif req.document_type == DocumentType.IMPACT:
            if not req.target_name or not req.target_node_id:
                raise HTTPException(status_code=400, detail="target_name and target_node_id required for IMPACT docs")
            doc = doc_service.generate_impact_doc(req.repository_id, req.target_name, req.target_node_id)
        else:
            raise HTTPException(status_code=400, detail="Unsupported document type")
            
        return {
            "id": doc.id,
            "repository_id": doc.repository_id,
            "document_type": doc.document_type,
            "status": doc.status,
            "created_at": doc.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/repository/{repository_id}", response_model=List[DocumentResponse])
def list_documents(repository_id: uuid.UUID, db: Session = Depends(get_db)):
    docs = db.query(GeneratedDocument).filter(GeneratedDocument.repository_id == repository_id).order_by(GeneratedDocument.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "repository_id": d.repository_id,
            "document_type": d.document_type,
            "status": d.status,
            "created_at": d.created_at.isoformat()
        } for d in docs
    ]

@router.get("/{document_id}/markdown")
def get_document_markdown(document_id: uuid.UUID, db: Session = Depends(get_db)):
    doc = db.query(GeneratedDocument).filter(GeneratedDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return Response(content=doc.content_markdown, media_type="text/markdown")

@router.get("/{document_id}/html")
def get_document_html(document_id: uuid.UUID, db: Session = Depends(get_db)):
    doc = db.query(GeneratedDocument).filter(GeneratedDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return Response(content=doc.content_html, media_type="text/html")

@router.get("/{document_id}/pdf")
def get_document_pdf(document_id: uuid.UUID, db: Session = Depends(get_db)):
    doc = db.query(GeneratedDocument).filter(GeneratedDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    from ..utils.document_formatter import html_to_pdf
    try:
        pdf_bytes = html_to_pdf(doc.content_html)
        return Response(content=pdf_bytes, media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename=document_{document_id}.pdf"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
