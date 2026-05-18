"""
Chunking module — processes and saves preprocessed sections as JSON.

Each chunk represents one section from the markdown hierarchy.
Chunks are saved to chunks/<document_title>/chunks.json as a structured JSON file.

JSON format:
{
  "document_title": "Document Name",
  "total_chunks": 42,
  "chunks": [
    {
      "chunk_id": 1,
      "headline": "Kapitel 1 › Avsnitt 1.1",
      "page_number": 5,
      "content": "Text from section...",
      "breadcrumb": ["Kapitel 1", "Avsnitt 1.1"]
    },
    ...
  ]
}

This JSON format makes it easy to:
- Load all chunks at once into memory
- Display in UI with hierarchy structure
- Send to LLM with metadata preserved
- Process in batches if needed
"""

import os
import re
import json
from pathlib import Path
from typing import List, Tuple, Dict, Optional


CHUNKS_DIR = Path("chunks")


def detect_heading_level(headline: str) -> int:
    """
    Detects the heading level based on the headline format.
    
    Returns:
        0 = No number pattern (treat as level 1)
        1 = Chapter level (1, 2, 3 or "Kapitel 1")
        2 = Subsection level (1.1, 1.2, 2.1 or "Kapitel 1.1")
        3+ = Deeper level (1.1.1, etc.)
    
    Args:
        headline: the heading text to analyze
    
    Returns:
        Integer indicating the heading depth level
    """
    # Match patterns like "1.1", "1.2.1", "Kapitel 1.1", etc.
    match = re.match(r'^(?:[Kk]apitel\s+)?(\d+(?:\.\d+)*)', headline)
    
    if not match:
        # No number pattern - treat as level 1
        return 0
    
    # Count the dots in the number pattern
    number_part = match.group(1)
    dots = number_part.count('.')
    level = dots + 1  # 1 = no dot, 2 = one dot, 3 = two dots, etc.
    
    return level


def is_warning_section(headline: str) -> bool:
    """
    Checks if a heading is a warning/informational section and should be filtered out.
    
    Detects sections with:
    - "varning" / "warning" (Swedish/English warnings)
    - "OBS" (Swedish abbreviation for "Observera" - Note)
    
    These sections are typically informational and not procedural,
    so they should not be chunked for TNA analysis.
    
    Args:
        headline: the heading text to check
    
    Returns:
        True if this is a warning/informational section, False otherwise
    """
    headline_lower = headline.lower()
    filter_keywords = ["varning", "warning", "varningar", "warnings", "obs"]
    
    return any(keyword in headline_lower for keyword in filter_keywords)


def should_include_chunk(headline: str) -> bool:
    """
    Determines if a heading should be chunked (only level 1.X subsections).
    
    Returns True for:
    - Level 2 headings (1.1, 1.2, 2.1, 2.2, etc.)
    - Unnumbered headings (level 0 - treated as subsections when no chapters exist)
    - AND NOT warning sections
    
    Returns False for:
    - Level 1 headings (1, 2, 3 - main chapters)
    - Level 3+ headings (1.1.1 - too deep)
    - Warning sections (contain "varning" or "warning")
    
    Args:
        headline: the heading text to check
    
    Returns:
        Boolean indicating if this heading should become a chunk
    """
    # Filter out warning sections first
    if is_warning_section(headline):
        return False
    
    level = detect_heading_level(headline)
    
    # Include level 2 (1.1, 1.2) and level 0 (unnumbered)
    return level == 2 or level == 0


def ensure_chunk_directory(document_title: str) -> Path:
    """
    Ensures that the chunks directory for a document exists.
    
    Args:
        document_title: title/identifier of the document
    
    Returns:
        Path to the document's chunks directory
    """
    doc_chunks_dir = CHUNKS_DIR / document_title
    doc_chunks_dir.mkdir(parents=True, exist_ok=True)
    return doc_chunks_dir


def sanitize_filename(text: str, max_length: int = 100) -> str:
    """
    Converts a section headline into a valid filename.
    
    Removes invalid characters, truncates to max_length, and appends .txt.
    
    Args:
        text: headline or section name
        max_length: maximum filename length (excluding .txt)
    
    Returns:
        Valid filename string
    """
    # Remove invalid characters
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        text = text.replace(char, '')
    
    # Replace whitespace with underscores
    text = text.replace(' ', '_').replace('\n', '_')
    
    # Remove multiple consecutive underscores
    while '__' in text:
        text = text.replace('__', '_')
    
    # Truncate to max length
    text = text[:max_length]
    
    # Remove trailing underscore if present
    text = text.rstrip('_')
    
    return text + '.txt'


def save_chunks(
    document_title: str,
    sections: List[Dict]
) -> List[Dict]:
    """
    Saves preprocessed sections as JSON chunks in chunks/<document_title>/chunks.json.
    
    Each section from the markdown preprocessing becomes a chunk with FULL METADATA
    that matches LLM output format:
    
    Chunk structure:
    {
        "chunk_id": 1,
        "document_filename": "document.pdf",
        "document_title": "Document Title",
        "section_or_chapter": "Kapitel 1 › Avsnitt 1.1",
        "breadcrumb": ["Kapitel 1", "Avsnitt 1.1"],
        "page_number": 5,
        "level": 2,
        "content": "Text från sektion..."
    }
    
    This structure matches the metadata in LLM output format:
    "traceability": {
        "document_filename": "document.pdf",
        "document_title": "Document Title",
        "section_or_chapter": "Kapitel 1 › Avsnitt 1.1"
    }
    
    Args:
        document_title: title/identifier of the document
        sections: list of dicts from preprocessing with metadata
    
    Returns:
        List of chunk dictionaries saved
    """
    doc_chunks_dir = ensure_chunk_directory(document_title)
    
    chunks = []
    chunk_id = 1
    
    for section in sections:
        # Filter out warning sections
        if is_warning_section(section.get("section_or_chapter", "")):
            continue
        
        # Create chunk entry with full metadata
        chunk = {
            "chunk_id": chunk_id,
            "document_filename": section.get("document_filename", ""),
            "document_title": section.get("document_title", ""),
            "section_or_chapter": section.get("section_or_chapter", ""),
            "breadcrumb": section.get("breadcrumb", []),
            "page_number": section.get("page_number", 0),
            "level": section.get("level", 0),
            "content": section.get("content", "")
        }
        
        chunks.append(chunk)
        chunk_id += 1
    
    # Save all chunks to single JSON file
    chunks_json = {
        "document_title": document_title,
        "total_chunks": len(chunks),
        "chunks": chunks
    }
    
    chunks_file = doc_chunks_dir / "chunks.json"
    
    with open(chunks_file, 'w', encoding='utf-8') as f:
        json.dump(chunks_json, f, ensure_ascii=False, indent=2)
    
    # Return just the list of chunks
    return chunks


def load_chunks(document_title: str) -> List[Dict]:
    """
    Loads all chunks for a document from JSON.
    
    Args:
        document_title: title/identifier of the document
    
    Returns:
        List of chunk dictionaries with structure:
        [
          {
            "chunk_id": 1,
            "headline": "Kapitel 1 › Avsnitt 1.1",
            "page_number": 5,
            "content": "Text...",
            "breadcrumb": ["Kapitel 1", "Avsnitt 1.1"]
          },
          ...
        ]
    """
    doc_chunks_dir = CHUNKS_DIR / document_title
    chunks_file = doc_chunks_dir / "chunks.json"
    
    if not chunks_file.exists():
        return []
    
    try:
        with open(chunks_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("chunks", [])
    
    except json.JSONDecodeError as e:
        print(f"Error reading chunks JSON for {document_title}: {str(e)}")
        return []
    
    except Exception as e:
        print(f"Unexpected error loading chunks: {str(e)}")
        return []


def remove_chunks(document_title: str):
    """
    Removes all chunks for a document (deletes chunks.json file).
    
    Args:
        document_title: title/identifier of the document
    """
    import shutil
    
    doc_chunks_dir = CHUNKS_DIR / document_title
    
    if doc_chunks_dir.exists():
        shutil.rmtree(doc_chunks_dir)
