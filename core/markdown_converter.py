"""
Markdown converter module — converts PDF to markdown format using pymupdf4llm.

This module provides utilities to convert PDF documents to markdown format
with preserved heading hierarchy (H1, H2, H3, etc.) and structure,
making it easier to parse document hierarchy and create breadcrumbs.

TABLE FILTERING:
After conversion, detects and removes table content from markdown using TWO detection methods:

METHOD 1 (PRIMARY): detect_and_remove_tables()
- Markdown table format (with pipes |)
- Table separator lines (--- or === patterns)
- Table captions ("Tabell N.", "Table N.")
- Consecutive lines that look like table rows

METHOD 2 (SECONDARY): detect_and_remove_aligned_tables()
- Lines with excessive whitespace (aligned columns)
- Repeated short consecutive lines (table rows pattern)
- Lines with many numeric values
- CSV-like patterns (many commas/semicolons)
- Fixed-width column patterns

Both methods are applied sequentially to catch tables that may be missed
by either method alone (comprehensive table removal).
"""

from typing import Optional
from pathlib import Path
import logging
import re

logger = logging.getLogger(__name__)


def detect_and_remove_aligned_tables(markdown_text: str) -> str:
    """
    Removes aligned/formatted tables from markdown text using pattern detection.
    
    This is an ALTERNATIVE/ADDITIONAL detection method that catches tables
    that may be missed by the primary detect_and_remove_tables() method.
    
    Detects tables by identifying:
    1. Lines with excessive whitespace (aligned columns pattern)
    2. Lines that are short but repeat multiple consecutive lines
    3. Lines with many numeric/alphanumeric values in sequence
    4. CSV-like patterns (many commas or semicolons)
    5. Fixed-width column patterns (aligned pipes without markdown formatting)
    
    This catches tables formatted as:
    - Aligned text columns (fixed-width spacing)
    - Tab-separated values
    - Repeated short lines (table rows)
    - Space-aligned numerical data
    
    Called by: pdf_to_markdown() as secondary table detection
    
    Args:
        markdown_text: raw markdown from pymupdf4llm
    
    Returns:
        Markdown with aligned/formatted tables removed
    """
    lines = markdown_text.split('\n')
    filtered_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip empty lines (preserve them)
        if not stripped:
            filtered_lines.append(line)
            i += 1
            continue
        
        # PATTERN 1: Lines with many consecutive tabs or large spaces (aligned columns)
        # Example: "Value1    Value2    Value3" or "Col1\tCol2\tCol3"
        if re.search(r'[\t]{2,}', line) or re.search(r'[\s]{8,}', stripped):
            # This looks like aligned columns - skip it
            i += 1
            continue
        
        # PATTERN 2: Detect series of repeated short lines (table rows pattern)
        # Count consecutive lines that are all short (< 60 chars) and similar length
        if len(stripped) < 60 and len(stripped) > 5:
            # Look ahead to see if there are multiple similar short lines
            consecutive_short = 1
            j = i + 1
            
            while j < len(lines) and consecutive_short < 5:  # Look ahead max 5 lines
                next_stripped = lines[j].strip()
                
                # If next line is empty, table might be ending
                if not next_stripped:
                    break
                
                # If next line is heading (starts with #), table is ending
                if next_stripped.startswith('#'):
                    break
                
                # If next line has similar length (within 20% variance) and is short
                length_variance = abs(len(next_stripped) - len(stripped)) / len(stripped)
                if length_variance < 0.3 and len(next_stripped) < 60:
                    consecutive_short += 1
                    j += 1
                else:
                    break
            
            # If we found 3+ consecutive short lines of similar length, skip this table block
            if consecutive_short >= 3:
                # Skip all those lines
                i = j
                continue
        
        # PATTERN 3: Lines with many numeric values (numerical tables)
        # Example: "12  34  56  78  90" or "1.2, 3.4, 5.6"
        # Count digits and separators
        digit_count = len(re.findall(r'\d', stripped))
        separator_count = len(re.findall(r'[,;:]', stripped))
        
        # If line has many digits relative to length, it might be numerical data
        if len(stripped) > 20 and digit_count > len(stripped) * 0.3:
            # Could be numerical table data
            # Check if there are many spaces suggesting columns
            space_groups = len(re.findall(r'[\s]{2,}', stripped))
            if space_groups >= 3 or separator_count >= 3:
                i += 1
                continue
        
        # PATTERN 4: CSV-like patterns (many commas or semicolons)
        # Example: "Value1, Value2, Value3, Value4"
        if separator_count >= 4 and len(stripped.split(',')) > 4:
            # Looks like CSV data, skip it
            i += 1
            continue
        
        # Keep this line (not a table)
        filtered_lines.append(line)
        i += 1
    
    return '\n'.join(filtered_lines)


def detect_and_remove_tables(markdown_text: str) -> str:
    """
    PRIMARY METHOD: Removes table content from markdown text.
    
    This is the PRIMARY detection method. Used together with detect_and_remove_aligned_tables()
    for comprehensive table removal.
    
    Detects tables by:
    1. Markdown table format (lines with | pipes in actual table data)
    2. Table separator lines (--- or === patterns)
    3. Table captions ("Tabell N.", "Table N.")
    4. Consecutive lines that look like table rows
    
    Called by: pdf_to_markdown() as primary table detection (method 1 of 2)
    
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
    2. Remove table content using PRIMARY detection method (pipes, separators, captions)
    3. Remove table content using SECONDARY detection method (aligned columns, patterns)
    4. Preserve document structure with heading levels (H1-H6)
    
    This dual-method approach (remove tables AFTER conversion with 2 detection strategies)
    is more reliable than pre-processing the PDF, as it:
    - Works with any PDF format
    - Catches both markdown-formatted tables and aligned/formatted tables
    - Doesn't require additional libraries beyond what's already used
    
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
        
        # METHOD 1: Remove tables using primary detection (pipes, separators, captions)
        logger.info(f"Removing tables (METHOD 1: PRIMARY - pipes/captions)")
        md_text = detect_and_remove_tables(md_text)
        
        # METHOD 2: Remove tables using secondary detection (aligned columns, patterns)
        logger.info(f"Removing tables (METHOD 2: SECONDARY - aligned/formatted)")
        md_text = detect_and_remove_aligned_tables(md_text)
        
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
