import markdown
import os
import uuid
import logging

logger = logging.getLogger(__name__)

def markdown_to_html(md_content: str) -> str:
    """
    Converts Markdown content to HTML, wrapping it in a basic CSS styling layout.
    """
    html_body = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
    
    html_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 2rem;
            }}
            h1, h2, h3 {{ color: #111; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }}
            code {{ background-color: #f4f4f4; padding: 0.2em 0.4em; border-radius: 3px; font-family: monospace; font-size: 0.9em; }}
            pre code {{ background-color: transparent; padding: 0; }}
            pre {{ background-color: #f4f4f4; padding: 1em; border-radius: 5px; overflow-x: auto; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 1rem; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """
    return html_page

def html_to_pdf(html_content: str) -> bytes:
    """
    Converts HTML content to PDF bytes using WeasyPrint.
    If WeasyPrint fails or is unavailable, raises an Exception.
    """
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except ImportError as e:
        logger.error(f"WeasyPrint is not installed or configured correctly: {e}")
        raise Exception("PDF generation is not available. Please ensure WeasyPrint is installed.")
