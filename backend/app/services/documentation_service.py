import uuid
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from openai import OpenAI

from ..config import settings
from ..models import (
    Repository, CodeFile, CodeClass, CodeFunction, CodeGraphEdge,
    GeneratedDocument, DocumentType, DocumentStatus
)
from .entity_summarization_service import EntitySummarizationService
from ..utils.document_formatter import markdown_to_html, html_to_pdf

logger = logging.getLogger("codeatlas.documentation")

class DocumentationService:
    def __init__(self, db: Session):
        self.db = db
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def _generate_content_with_llm(self, prompt: str, context: str) -> str:
        if not self.openai_client:
            logger.warning("OpenAI client not configured. Returning dummy content.")
            return f"# Generated Content\n\n**Prompt:** {prompt}\n\n**Context (Truncated):** {context[:200]}..."

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are the Principal Documentation Architect for CodeAtlas. Generate accurate, graph-aware engineering documentation using the provided context. Format output entirely in standard Markdown. Use Mermaid.js where appropriate for diagrams. Do not include introductory text like 'Here is the documentation', just return the Markdown."},
                    {"role": "user", "content": f"{prompt}\n\n### CONTEXT:\n{context}"}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Failed to generate content with LLM: {e}")
            return f"# Generation Failed\n\nAn error occurred: {str(e)}"

    def _get_repo_context(self, repository_id: uuid.UUID) -> str:
        summarization_service = EntitySummarizationService(self.db)
        summaries = summarization_service.generate_summaries(repository_id)
        # Flatten summaries into a single context string
        # To avoid token limits, we might truncate in a real production system, but for MVP we send it.
        context = ""
        for s in summaries:
            context += f"\n--- {s['node_type'].upper()}: {s['name']} ---\n{s['content']}\n"
        return context

    def _create_and_store_document(
        self, repository_id: uuid.UUID, doc_type: DocumentType, target_node_id: Optional[uuid.UUID], content_markdown: str
    ) -> GeneratedDocument:
        html_content = markdown_to_html(content_markdown)
        
        doc = GeneratedDocument(
            repository_id=repository_id,
            document_type=doc_type,
            target_node_id=target_node_id,
            content_markdown=content_markdown,
            content_html=html_content,
            status=DocumentStatus.COMPLETED
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def generate_architecture_doc(self, repository_id: uuid.UUID) -> GeneratedDocument:
        repo = self.db.query(Repository).filter(Repository.id == repository_id).first()
        if not repo:
            raise ValueError(f"Repository {repository_id} not found.")

        context = self._get_repo_context(repository_id)
        prompt = f"""
        Generate comprehensive Architecture Documentation for the repository '{repo.name}'.
        Include:
        - System Overview
        - Layers (e.g., Services, Controllers, Repositories)
        - Key Dependencies
        - A Mermaid.js Architecture Diagram
        """
        markdown_content = self._generate_content_with_llm(prompt, context)
        return self._create_and_store_document(repository_id, DocumentType.ARCHITECTURE, None, markdown_content)

    def generate_service_doc(self, repository_id: uuid.UUID, service_name: str, target_node_id: uuid.UUID) -> GeneratedDocument:
        context = self._get_repo_context(repository_id)
        prompt = f"""
        Generate Service Documentation for '{service_name}'.
        Using the graph context provided, clearly outline:
        - Service Responsibilities
        - Dependencies (Outgoing calls/imports)
        - Consumers (Incoming calls/imports)
        - Potential Risk Areas
        """
        markdown_content = self._generate_content_with_llm(prompt, context)
        return self._create_and_store_document(repository_id, DocumentType.SERVICE, target_node_id, markdown_content)

    def generate_api_doc(self, repository_id: uuid.UUID) -> GeneratedDocument:
        context = self._get_repo_context(repository_id)
        prompt = """
        Generate API Documentation based on the repository graph and code summaries.
        Identify controller/router classes or functions.
        Extract and document:
        - Endpoints
        - Request Models
        - Response Models
        - Dependencies
        """
        markdown_content = self._generate_content_with_llm(prompt, context)
        return self._create_and_store_document(repository_id, DocumentType.API, None, markdown_content)

    def generate_onboarding_guide(self, repository_id: uuid.UUID) -> GeneratedDocument:
        context = self._get_repo_context(repository_id)
        prompt = """
        Generate a Developer Onboarding Guide for this repository.
        Include:
        - Repository Structure Summary
        - Key Services and Components
        - Primary Entry Points
        - Recommended Development Workflow
        """
        markdown_content = self._generate_content_with_llm(prompt, context)
        return self._create_and_store_document(repository_id, DocumentType.ONBOARDING, None, markdown_content)

    def generate_impact_doc(self, repository_id: uuid.UUID, component_name: str, target_node_id: uuid.UUID) -> GeneratedDocument:
        context = self._get_repo_context(repository_id)
        prompt = f"""
        Generate an Impact Analysis Document for '{component_name}'.
        Using the graph context, detail:
        - What breaks if this component changes?
        - Full Dependency Chains (upstream and downstream)
        - Critical dependent components
        """
        markdown_content = self._generate_content_with_llm(prompt, context)
        return self._create_and_store_document(repository_id, DocumentType.IMPACT, target_node_id, markdown_content)
