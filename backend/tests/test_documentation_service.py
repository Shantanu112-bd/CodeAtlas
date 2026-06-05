import pytest
from app.utils.document_formatter import markdown_to_html

def test_markdown_to_html_conversion():
    md_content = """# Test Document
This is a **test** document.

```python
def hello():
    return "world"
```

| Header 1 | Header 2 |
| -------- | -------- |
| Cell 1   | Cell 2   |
"""
    
    html = markdown_to_html(md_content)
    
    assert "<h1>Test Document</h1>" in html
    assert "<strong>test</strong>" in html
    assert "def hello():" in html
    assert "<table>" in html
    assert "<th>Header 1</th>" in html

# Note: We won't strictly test weasyprint pdf generation as it requires system dependencies (libcairo, etc.)
# which may not be available in all test runner environments. 
# In a real CI pipeline, we'd mock it or run inside a docker container with those dependencies.
