import pytest
from app.utils.ast_parser import CodeParser

def test_parse_python_file():
    code = """
class MyClass:
    \"\"\"This is a class docstring.\"\"\"
    def my_method(self):
        \"\"\"This is a method docstring.\"\"\"
        pass

def standalone_function(arg1):
    pass

import os
from datetime import datetime as dt
from typing import List, Dict
"""
    result = CodeParser.parse_python_file(code)
    
    assert len(result["classes"]) == 1
    assert result["classes"][0]["name"] == "MyClass"
    assert result["classes"][0]["docstring"] == "This is a class docstring."
    
    assert len(result["functions"]) == 2
    # Check method
    method = next(f for f in result["functions"] if f["name"] == "my_method")
    assert method["docstring"] == "This is a method docstring."
    
    # Check standalone func
    func = next(f for f in result["functions"] if f["name"] == "standalone_function")
    assert func["docstring"] is None

    assert len(result["imports"]) == 4
    modules = [imp["module"] for imp in result["imports"]]
    assert "os" in modules
    assert "datetime.datetime" in modules
    assert "typing.List" in modules
    assert "typing.Dict" in modules

def test_parse_invalid_python_file():
    code = "def class: invalid syntax !!"
    result = CodeParser.parse_python_file(code)
    
    assert len(result["classes"]) == 0
    assert len(result["functions"]) == 0
