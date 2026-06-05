from tree_sitter import Language, Parser
import tree_sitter_javascript as ts_js
import tree_sitter_typescript as ts_ts
from typing import Dict, Any

try:
    # Load languages
    JS_LANGUAGE = Language(ts_js.language())
    TS_LANGUAGE = Language(ts_ts.language_typescript())
    TSX_LANGUAGE = Language(ts_ts.language_tsx())
except Exception as e:
    JS_LANGUAGE = None
    TS_LANGUAGE = None
    TSX_LANGUAGE = None
    print(f"Failed to load tree-sitter languages: {e}")

class TreeSitterParser:
    @staticmethod
    def get_parser(file_extension: str):
        if JS_LANGUAGE is None:
            raise RuntimeError("Tree-sitter languages are not loaded.")

        if file_extension in ['.js', '.jsx']:
            parser = Parser(JS_LANGUAGE)
        elif file_extension == '.ts':
            parser = Parser(TS_LANGUAGE)
        elif file_extension == '.tsx':
            parser = Parser(TSX_LANGUAGE)
        else:
            raise ValueError(f"Unsupported extension: {file_extension}")
        return parser

    @staticmethod
    def parse_file(file_content: str, file_extension: str) -> Dict[str, Any]:
        parser = TreeSitterParser.get_parser(file_extension)
        tree = parser.parse(bytes(file_content, "utf8"))

        classes = []
        functions = []
        imports = []

        def traverse(node, current_func):
            if node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                name = name_node.text.decode('utf8') if name_node else "Anonymous"
                
                parent_class_names = []
                for child in node.children:
                    if child.type == 'class_heritage':
                        def extract_ids(n):
                            if n.type in ['identifier', 'type_identifier']:
                                parent_class_names.append(n.text.decode('utf8'))
                            else:
                                for c in n.children: extract_ids(c)
                        extract_ids(child)

                classes.append({
                    "name": name,
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "docstring": None,
                    "parent_class_names": parent_class_names
                })
            elif node.type in ['function_declaration', 'arrow_function', 'method_definition']:
                name = "Anonymous"
                if node.type == 'function_declaration':
                    name_node = node.child_by_field_name('name')
                    if name_node: name = name_node.text.decode('utf8')
                elif node.type == 'method_definition':
                    name_node = node.child_by_field_name('name')
                    if name_node: name = name_node.text.decode('utf8')
                elif node.type == 'arrow_function':
                    if node.parent and node.parent.type == 'variable_declarator':
                        name_node = node.parent.child_by_field_name('name')
                        if name_node: name = name_node.text.decode('utf8')
                
                func_dict = {
                    "name": name,
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "docstring": None,
                    "calls": []
                }
                functions.append(func_dict)
                for child in node.children:
                    traverse(child, func_dict)
                return # Prevent double traversal
            
            elif node.type == 'import_statement':
                source_node = node.child_by_field_name('source')
                if source_node:
                    module = source_node.text.decode('utf8').strip("'\"")
                    imports.append({
                        "module": module,
                        "type": "import",
                        "line": node.start_point[0] + 1
                    })
            elif node.type == 'call_expression':
                func_node = node.child_by_field_name('function')
                if func_node:
                    func_name = ""
                    if func_node.type == 'identifier':
                        func_name = func_node.text.decode('utf8')
                    elif func_node.type == 'member_expression':
                        prop_node = func_node.child_by_field_name('property')
                        if prop_node:
                            func_name = prop_node.text.decode('utf8')
                    
                    if func_name == 'require':
                        args_node = node.child_by_field_name('arguments')
                        if args_node and args_node.child_count > 1:
                            for child in args_node.children:
                                if child.type == 'string':
                                    module = child.text.decode('utf8').strip("'\"")
                                    imports.append({
                                        "module": module,
                                        "type": "require",
                                        "line": node.start_point[0] + 1
                                    })
                    elif func_name and current_func is not None:
                        current_func["calls"].append(func_name)

            for child in node.children:
                traverse(child, current_func)

        traverse(tree.root_node, None)

        return {"classes": classes, "functions": functions, "imports": imports}
