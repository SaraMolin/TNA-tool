"""
Markdown converter module — converts PDF to markdown format using pymupdf4llm.

This module provides utilities to convert PDF documents to markdown format
with preserved heading hierarchy (H1, H2, H3, etc.) and structure,
making it easier to parse document hierarchy and create breadcrumbs.

TABLE FILTERING:
After conversion, detects and removes table content from markdown by identifying:
- Markdown table format (with pipes |)
- Table-like patterns (multiple aligned columns)
- Repeated short lines that look like table rows
"""

from typing import Optional
from pathlib import Path
import logging
import re

logger = logging.getLogger(__name__)


def detect_and_remove_tables(markdown_text: str) -> str:
    """
    Removes table content from markdown text.
    
    Detects tables by:
    1. Markdown table format (lines with | pipes in actual table data)
    2. Table separator lines (--- or === patterns)
    3. Consecutive lines that look like table rows
    
    Args:
        markdown_text: raw markdown from pymupdf4llm
    
    Returns:
        Markdown with tables removed
    """
    lines = markdown_text.split('\n')
    filtered_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip markdown table format (pipes with content - actual data tables)
        # Pattern: | text | text | or |---|---|
        # But be careful not to skip hash marks or other valid markdown
        if '|' in stripped and not stripped.startswith('#'):
            # Check if this looks like an actual table (not just a pipe in text)
            # Markdown tables have multiple | characters and structured format
            pipe_count = stripped.count('|')
            if pipe_count >= 2:  # At least one cell separator
                # This looks like a table row, skip it
                i += 1
                continue
        
        # Skip table separator lines (many dashes or equals)
        # Pattern: ---, ===, etc.
        # But don't skip single dashes used in markdown (like in headers)
        if re.match(r'^[\s]*[=\-\+]{5,}[\s]*$', stripped):
            i += 1
            continue
        
        # Detect table captions like "Tabell 5." or "Table 3.1"
        # These often appear before a table
        if re.match(r'^(Tabell|Table|tabell|table)\s*\d*\.?\d*[\.\:]?\s+', stripped):
            # Skip the caption
            i += 1
            # Also skip the next few lines if they look like table data
            # Look ahead and skip lines that might be table content
            while i < len(lines):
                next_line = lines[i].strip()
                # If next line is empty or starts a new section, stop skipping
                if not next_line or next_line.startswith('#'):
                    break
                # If next line has table indicators, skip it
                if ('|' in next_line and not next_line.startswith('#') and next_line.count('|') >= 2):
                    i += 1
                else:
                    break
            continue
        
        # Heuristic: detect lines that are likely table rows
        # (many short words separated by spaces, common in Swedish table rows)
        # But be conservative - only skip if it really looks like a table
        words = stripped.split()
        if len(words) > 10 and all(len(w) < 15 for w in words):
            # Could be table row - but need to be careful not to remove real text
            # Only skip if this looks like aligned columns (many tabs or 8+ spaces)
            if re.search(r'[\t]{2,}|[\s]{10,}', line):
                i += 1
                continue
        
        # Keep this line
        filtered_lines.append(line)
        i += 1
    
    return '\n'.join(filtered_lines)


def pdf_to_markdown(pdf_path: str) -> Optional[str]:
    """
    Converts a PDF file to markdown format using pymupdf4llm.
    
    Process:
    1. Convert PDF to markdown using pymupdf4llm
    2. Remove table content from markdown
    3. Preserve document structure with heading levels (H1-H6)
    
    This approach (remove tables AFTER conversion) is more reliable than
    pre-processing the PDF, as it works with any PDF format and doesn't
    require additional libraries beyond what's already used.
    
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
        logger.info(f"Converting PDF to markdown: {pdf_path.name}")
        md_text = pymupdf4llm.to_markdown(str(pdf_path))
        
        if not md_text:
            logger.warning(f"PDF conversion returned empty result: {pdf_path}")
            return None
        
        # Remove tables from markdown
        logger.info(f"Removing tables from markdown content")
        md_text = detect_and_remove_tables(md_text)
        
        logger.info(f"Successfully converted PDF to markdown: {pdf_path.name}")
        return md_text
    
    except ImportError as e:
        logger.error(f"pymupdf4llm is not installed: {str(e)}")
        logger.error("Install with: pip install pymupdf4llm")
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
