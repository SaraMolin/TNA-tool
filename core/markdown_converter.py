"""
Markdown converter module — converts PDF to markdown format using pymupdf4llm.

This module provides utilities to convert PDF documents to markdown format
with preserved heading hierarchy (H1, H2, H3, etc.) and structure,
making it easier to parse document hierarchy and create breadcrumbs.
"""

from typing import Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def pdf_to_markdown(pdf_path: str) -> Optional[str]:
    """
    Converts a PDF file to markdown format using pymupdf4llm.
    
    Preserves the document structure with heading levels (H1-H6),
    making it suitable for hierarchy-based chunking and breadcrumb generation.
    
    Args:
        pdf_path: path to the PDF file
    
    Returns:
        Markdown string if successful, None if conversion failed
    """
    try:
        import pymupdf4llm
        
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return None
        
        # Convert PDF to markdown
        md_text = pymupdf4llm.to_markdown(pdf_path)
        
        if not md_text:
            logger.warning(f"PDF conversion returned empty result: {pdf_path}")
            return None
        
        logger.info(f"Successfully converted PDF to markdown: {pdf_path.name}")
        return md_text
    
    except ImportError:
        logger.error("pymupdf4llm is not installed. Install with: pip install pymupdf4llm")
        return None
    
    except Exception as e:
        logger.error(f"Error converting PDF to markdown: {str(e)}")
        return None


def clean_markdown(markdown_text: str) -> str:
    """
    Cleans up markdown output by removing unnecessary formatting.
    
    Removes:
    - Excessive blank lines
    - Unnecessary formatting artifacts
    - Image references (which don't help with TNA)
    
    Args:
        markdown_text: raw markdown from pymupdf4llm
    
    Returns:
        Cleaned markdown string
    """
    lines = markdown_text.split('\n')
    cleaned_lines = []
    prev_blank = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip image references
        if stripped.startswith('!['):
            continue
        
        # Remove excessive blank lines (max 1 consecutive blank)
        if not stripped:
            if not prev_blank:
                cleaned_lines.append(line)
            prev_blank = True
        else:
            cleaned_lines.append(line)
            prev_blank = False
    
    return '\n'.join(cleaned_lines)
