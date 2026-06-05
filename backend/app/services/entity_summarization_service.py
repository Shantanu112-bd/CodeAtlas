import uuid
import logging
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from ..models import Repository, CodeFile, CodeClass, CodeFunction, CodeGraphEdge

logger = logging.getLogger("codeatlas.summarization")

class EntitySummarizationService:
    def __init__(self, db: Session):
        self.db = db

    def _get_edges(self, repository_id: uuid.UUID) -> List[CodeGraphEdge]:
        return self.db.query(CodeGraphEdge).filter(CodeGraphEdge.repository_id == repository_id).all()

    def generate_summaries(self, repository_id: uuid.UUID) -> List[Dict[str, Any]]:
        repo = self.db.query(Repository).filter(Repository.id == repository_id).first()
        if not repo:
            logger.error(f"Repository {repository_id} not found.")
            return []

        files = self.db.query(CodeFile).filter(CodeFile.repository_id == repository_id).all()
        classes = self.db.query(CodeClass).filter(CodeClass.code_file_id.in_([f.id for f in files])).all()
        functions = self.db.query(CodeFunction).filter(CodeFunction.code_file_id.in_([f.id for f in files])).all()
        edges = self._get_edges(repository_id)

        # Build Maps
        file_map = {f.id: f for f in files}
        class_map = {c.id: c for c in classes}
        func_map = {f.id: f for f in functions}

        # Helper to get node name
        def get_node_name(node_type: str, node_id: uuid.UUID) -> str:
            if node_type == 'file' and node_id in file_map:
                return file_map[node_id].file_path
            elif node_type == 'class' and node_id in class_map:
                return class_map[node_id].name
            elif node_type == 'function' and node_id in func_map:
                return func_map[node_id].name
            return "Unknown"

        # Organize Edges
        # inward_edges[target_id] = [source_node]
        inward_edges = {}
        # outward_edges[source_id] = [target_node]
        outward_edges = {}

        for edge in edges:
            in_list = inward_edges.setdefault(edge.target_id, [])
            in_list.append((edge.source_type, edge.source_id, edge.edge_type))
            
            out_list = outward_edges.setdefault(edge.source_id, [])
            out_list.append((edge.target_type, edge.target_id, edge.edge_type))

        summaries = []

        # 1. Repository Summary
        repo_summary = f"Repository: {repo.name}\nOwner: {repo.owner}\nDefault Branch: {repo.default_branch}\n"
        repo_summary += f"Total Files: {len(files)}\nTotal Classes: {len(classes)}\nTotal Functions: {len(functions)}\n"
        summaries.append({
            "id": str(repo.id),
            "node_type": "repository",
            "repository_id": str(repo.id),
            "file_path": "/",
            "name": repo.name,
            "content": repo_summary
        })

        # 2. File Summaries
        for f in files:
            f_classes = [c.name for c in classes if c.code_file_id == f.id]
            f_funcs = [func.name for func in functions if func.code_file_id == f.id]
            
            out_imports = [get_node_name(t, tid) for t, tid, e in outward_edges.get(f.id, []) if e == 'imports']
            in_imports = [get_node_name(t, tid) for t, tid, e in inward_edges.get(f.id, []) if e == 'imports']

            summary = f"File: {f.file_path}\n"
            if f_classes: summary += f"Contains Classes: {', '.join(f_classes)}\n"
            if f_funcs: summary += f"Contains Functions: {', '.join(f_funcs)}\n"
            if out_imports: summary += f"Imports: {', '.join(out_imports)}\n"
            if in_imports: summary += f"Imported By: {', '.join(in_imports)}\n"

            summaries.append({
                "id": str(f.id),
                "node_type": "file",
                "repository_id": str(repo.id),
                "file_path": f.file_path,
                "name": f.file_path,
                "content": summary
            })

        # 3. Class Summaries
        for c in classes:
            parents = [get_node_name(t, tid) for t, tid, e in outward_edges.get(c.id, []) if e == 'inherits']
            children = [get_node_name(t, tid) for t, tid, e in inward_edges.get(c.id, []) if e == 'inherits']
            instantiators = [get_node_name(t, tid) for t, tid, e in inward_edges.get(c.id, []) if e == 'instantiates']
            
            summary = f"Class: {c.name}\nFile: {file_map[c.code_file_id].file_path}\n"
            if c.docstring: summary += f"Docstring: {c.docstring}\n"
            if parents: summary += f"Inherits from: {', '.join(parents)}\n"
            if children: summary += f"Extended by: {', '.join(children)}\n"
            if instantiators: summary += f"Instantiated by: {', '.join(instantiators)}\n"
            
            # Read code content from file
            # In a real pipeline, we'd batch read files. Doing it naively here.
            code_snippet = self._read_lines(repo.local_path, file_map[c.code_file_id].file_path, c.start_line, c.end_line)
            if code_snippet:
                summary += f"\nCode:\n{code_snippet}"

            summaries.append({
                "id": str(c.id),
                "node_type": "class",
                "repository_id": str(repo.id),
                "file_path": file_map[c.code_file_id].file_path,
                "name": c.name,
                "content": summary
            })

        # 4. Function Summaries
        for func in functions:
            callers = [get_node_name(t, tid) for t, tid, e in inward_edges.get(func.id, []) if e == 'calls']
            callees = [get_node_name(t, tid) for t, tid, e in outward_edges.get(func.id, []) if e == 'calls']
            
            summary = f"Function: {func.name}\nFile: {file_map[func.code_file_id].file_path}\n"
            if func.docstring: summary += f"Docstring: {func.docstring}\n"
            if callers: summary += f"Called by: {', '.join(callers)}\n"
            if callees: summary += f"Calls: {', '.join(callees)}\n"
            
            code_snippet = self._read_lines(repo.local_path, file_map[func.code_file_id].file_path, func.start_line, func.end_line)
            if code_snippet:
                summary += f"\nCode:\n{code_snippet}"

            summaries.append({
                "id": str(func.id),
                "node_type": "function",
                "repository_id": str(repo.id),
                "file_path": file_map[func.code_file_id].file_path,
                "name": func.name,
                "content": summary
            })

        logger.info(f"Generated {len(summaries)} entity summaries for repository {repository_id}")
        return summaries

    def _read_lines(self, local_path: str, file_path: str, start_line: int, end_line: int) -> str:
        if start_line is None or end_line is None:
            return ""
        try:
            import os
            full_path = os.path.join(local_path, file_path)
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return "".join(lines[max(0, start_line-1):end_line])
        except Exception:
            return ""
