import os
import logging
import uuid
import concurrent.futures
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session

from ..models import Repository, RepositoryStatus, CodeFile, CodeClass, CodeFunction, CodeImport, CodeGraphEdge
from ..utils.ast_parser import CodeParser
from ..utils.treesitter_parser import TreeSitterParser

logger = logging.getLogger("codeatlas.ast")

def _parse_file_worker(args: Tuple[str, str, str]) -> Dict[str, Any]:
    file_path, rel_path, repo_id_str = args
    file_extension = os.path.splitext(file_path)[1]
    
    parsed_data = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if file_extension == '.py':
            parsed_data = CodeParser.parse_python_file(content)
        elif file_extension in ['.js', '.jsx', '.ts', '.tsx']:
            parsed_data = TreeSitterParser.parse_file(content, file_extension)
            
    except Exception as e:
        return {"error": str(e), "rel_path": rel_path}

    if not parsed_data or ("classes" not in parsed_data and "functions" not in parsed_data):
        return {"rel_path": rel_path}

    code_file_id = uuid.uuid4()
    
    return {
        "file": {
            "id": code_file_id,
            "repository_id": uuid.UUID(repo_id_str),
            "file_path": rel_path
        },
        "classes": [{**c, "id": uuid.uuid4(), "code_file_id": code_file_id} for c in parsed_data.get('classes', [])],
        "functions": [{**f, "id": uuid.uuid4(), "code_file_id": code_file_id} for f in parsed_data.get('functions', [])],
        "imports": [{**i, "id": uuid.uuid4(), "code_file_id": code_file_id} for i in parsed_data.get('imports', [])]
    }

class ASTService:
    def __init__(self, db: Session):
        self.db = db

    def analyze_repository(self, repository_id: uuid.UUID) -> bool:
        """Walks the repository directory, parses files in parallel, and saves code structures."""
        repo = self.db.query(Repository).filter(Repository.id == repository_id).first()
        if not repo or repo.status != RepositoryStatus.INDEXED:
            logger.error(f"Cannot analyze repository {repository_id}. Status is not INDEXED.")
            return False

        if not os.path.exists(repo.local_path):
            logger.error(f"Local path does not exist for repository {repository_id}: {repo.local_path}")
            return False

        logger.info(f"Starting AST analysis for repository: {repo.github_url}")

        file_args = []
        valid_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx'}

        for root, dirs, files in os.walk(repo.local_path):
            dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '.venv', 'venv'}]
            for file_name in files:
                if file_name.startswith('.'):
                    continue
                ext = os.path.splitext(file_name)[1]
                if ext in valid_extensions:
                    file_path = os.path.join(root, file_name)
                    rel_path = os.path.relpath(file_path, repo.local_path)
                    file_args.append((file_path, rel_path, str(repo.id)))

        code_files = []
        code_classes = []
        code_functions = []
        code_imports = []

        # Parallel Parsing
        with concurrent.futures.ProcessPoolExecutor() as executor:
            for result in executor.map(_parse_file_worker, file_args):
                if "error" in result:
                    logger.warning(f"Error parsing file {result['rel_path']}: {result['error']}")
                    continue
                if "file" not in result:
                    continue
                
                code_files.append(CodeFile(**result["file"]))
                code_classes.extend([CodeClass(**c) for c in result["classes"]])
                code_functions.extend([CodeFunction(**f) for f in result["functions"]])
                
                # Model mapping
                for imp in result["imports"]:
                    code_imports.append(CodeImport(
                        id=imp["id"],
                        code_file_id=imp["code_file_id"],
                        imported_module=imp["module"],
                        import_type=imp["type"],
                        line_number=imp["line"]
                    ))

        logger.info(f"Parsed {len(code_files)} files. Inserting into database...")

        # Bulk Inserts
        self.db.bulk_save_objects(code_files)
        self.db.bulk_save_objects(code_classes)
        self.db.bulk_save_objects(code_functions)
        self.db.bulk_save_objects(code_imports)
        
        # Dependency Mapping Pass
        module_to_file_id = {}
        for f in code_files:
            # Python mapping app/models.py -> app.models
            py_mod = f.file_path.replace('/', '.').replace('.py', '')
            module_to_file_id[py_mod] = f.id
            # JS/TS mapping src/components/Button.tsx -> src/components/Button
            js_mod = os.path.splitext(f.file_path)[0]
            module_to_file_id[js_mod] = f.id

        graph_edges = []
        file_to_imports = {f.id: [] for f in code_files}

        # 1. Resolve Imports
        for imp in code_imports:
            target_mod = imp.imported_module
            target_file_id = None
            
            if target_mod in module_to_file_id:
                target_file_id = module_to_file_id[target_mod]
            else:
                # Heuristic for JS relative imports e.g., './components/Button'
                if target_mod.startswith('./') or target_mod.startswith('../'):
                    clean_target = target_mod.replace('./', '').replace('../', '')
                    for mod_key, f_id in module_to_file_id.items():
                        if mod_key.endswith(clean_target):
                            target_file_id = f_id
                            break
                            
            if target_file_id:
                file_to_imports[imp.code_file_id].append(target_file_id)
                graph_edges.append(CodeGraphEdge(
                    id=uuid.uuid4(),
                    repository_id=repository_id,
                    source_type='file',
                    source_id=imp.code_file_id,
                    target_type='file',
                    target_id=target_file_id,
                    edge_type='imports'
                ))

        # Build indexes for class/func lookups
        file_classes = {f.id: {} for f in code_files}
        global_classes = {}
        for c in code_classes:
            file_classes[c.code_file_id][c.name] = c.id
            global_classes[c.name] = c.id

        file_funcs = {f.id: {} for f in code_files}
        global_funcs = {}
        for f in code_functions:
            file_funcs[f.code_file_id][f.name] = f.id
            global_funcs[f.name] = f.id

        # 2. Resolve Class Inheritance
        for c in code_classes:
            for parent_name in getattr(c, "parent_class_names", []):
                target_id = None
                if parent_name in file_classes[c.code_file_id]:
                    target_id = file_classes[c.code_file_id][parent_name]
                else:
                    for imp_file_id in file_to_imports.get(c.code_file_id, []):
                        if parent_name in file_classes.get(imp_file_id, {}):
                            target_id = file_classes[imp_file_id][parent_name]
                            break
                    if not target_id and parent_name in global_classes:
                        target_id = global_classes[parent_name]

                if target_id:
                    graph_edges.append(CodeGraphEdge(
                        id=uuid.uuid4(),
                        repository_id=repository_id,
                        source_type='class',
                        source_id=c.id,
                        target_type='class',
                        target_id=target_id,
                        edge_type='inherits'
                    ))

        # 3. Resolve Function Calls
        for f in code_functions:
            for call_name in getattr(f, "calls", []):
                target_id = None
                target_type = None
                
                if call_name in file_funcs[f.code_file_id]:
                    target_id = file_funcs[f.code_file_id][call_name]
                    target_type = 'function'
                elif call_name in file_classes[f.code_file_id]:
                    target_id = file_classes[f.code_file_id][call_name]
                    target_type = 'class'
                else:
                    for imp_file_id in file_to_imports.get(f.code_file_id, []):
                        if call_name in file_funcs.get(imp_file_id, {}):
                            target_id = file_funcs[imp_file_id][call_name]
                            target_type = 'function'
                            break
                        elif call_name in file_classes.get(imp_file_id, {}):
                            target_id = file_classes[imp_file_id][call_name]
                            target_type = 'class'
                            break
                    if not target_id:
                        if call_name in global_funcs:
                            target_id = global_funcs[call_name]
                            target_type = 'function'
                        elif call_name in global_classes:
                            target_id = global_classes[call_name]
                            target_type = 'class'
                
                if target_id:
                    graph_edges.append(CodeGraphEdge(
                        id=uuid.uuid4(),
                        repository_id=repository_id,
                        source_type='function',
                        source_id=f.id,
                        target_type=target_type,
                        target_id=target_id,
                        edge_type='calls' if target_type == 'function' else 'instantiates'
                    ))

        if graph_edges:
            self.db.bulk_save_objects(graph_edges)

        self.db.commit()
        
        logger.info(f"Finished AST analysis. Files: {len(code_files)}, Classes: {len(code_classes)}, Functions: {len(code_functions)}, Edges: {len(graph_edges)}")
        return True
