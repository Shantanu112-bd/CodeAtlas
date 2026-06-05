import ast
from typing import List, Dict, Any

class CodeVisitor(ast.NodeVisitor):
    def __init__(self):
        self.classes = []
        self.functions = []
        self.imports = []
        self.current_function = None

    def _extract_name(self, n):
        if isinstance(n, ast.Name): return n.id
        elif isinstance(n, ast.Attribute): return f"{self._extract_name(n.value)}.{n.attr}"
        return ""

    def visit_ClassDef(self, node):
        bases = [self._extract_name(b) for b in node.bases]
        bases = [b for b in bases if b]
        self.classes.append({
            "name": node.name,
            "start_line": getattr(node, "lineno", 1),
            "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 1)),
            "docstring": ast.get_docstring(node),
            "parent_class_names": bases
        })
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self._handle_function(node)

    def visit_AsyncFunctionDef(self, node):
        self._handle_function(node)

    def _handle_function(self, node):
        prev_func = self.current_function
        func_dict = {
            "name": node.name,
            "start_line": getattr(node, "lineno", 1),
            "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 1)),
            "docstring": ast.get_docstring(node),
            "calls": []
        }
        self.functions.append(func_dict)
        self.current_function = func_dict
        self.generic_visit(node)
        self.current_function = prev_func

    def visit_Call(self, node):
        if self.current_function is not None:
            call_name = self._extract_name(node.func)
            if call_name:
                self.current_function["calls"].append(call_name)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({
                "module": alias.name,
                "type": "import",
                "line": getattr(node, "lineno", 1)
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module if node.module else ""
        for alias in node.names:
            imported_module = f"{module}.{alias.name}" if module else alias.name
            self.imports.append({
                "module": imported_module,
                "type": "from",
                "line": getattr(node, "lineno", 1)
            })
        self.generic_visit(node)


class CodeParser:
    @staticmethod
    def parse_python_file(file_content: str) -> Dict[str, Any]:
        """Parses a Python file and extracts classes, functions, calls, and inheritance."""
        try:
            tree = ast.parse(file_content)
        except SyntaxError:
            return {"classes": [], "functions": [], "imports": []}

        visitor = CodeVisitor()
        visitor.visit(tree)

        return {"classes": visitor.classes, "functions": visitor.functions, "imports": visitor.imports}

    @staticmethod
    def parse_generic_file(file_content: str) -> Dict[str, Any]:
        """A placeholder for future JS/TS/Go regex or tree-sitter parsing."""
        return {"classes": [], "functions": []}
