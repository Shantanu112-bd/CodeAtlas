import pytest
from app.utils.treesitter_parser import TreeSitterParser, JS_LANGUAGE

@pytest.mark.skipif(JS_LANGUAGE is None, reason="tree-sitter languages not installed")
def test_parse_javascript_file():
    code = """
import React, { useState } from 'react';
import { Button } from './components/Button';
const axios = require('axios');

class MyComponent extends React.Component {
    render() {
        return <div />;
    }
}

function calculateSum(a, b) {
    return a + b;
}

const multiply = (a, b) => a * b;
"""
    result = TreeSitterParser.parse_file(code, '.js')
    
    # Check classes
    assert len(result["classes"]) == 1
    assert result["classes"][0]["name"] == "MyComponent"
    
    # Check functions
    assert len(result["functions"]) >= 2
    func_names = [f["name"] for f in result["functions"]]
    assert "calculateSum" in func_names
    assert "multiply" in func_names # Note: arrow functions might not be extracted nicely depending on AST structure, but let's test if it handles standard function_declaration well.
    
    # Check imports
    assert len(result["imports"]) == 3
    modules = [imp["module"] for imp in result["imports"]]
    assert "react" in modules
    assert "./components/Button" in modules
    assert "axios" in modules
