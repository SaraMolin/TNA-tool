"""
Chunking module — saves preprocessed text sections as readable .txt files.

Each chunk represents one section at the 1.X level (subsection level).
Chunks are saved to chunks/<document_title>/ with descriptive filenames.

Examples of what gets chunked:
- 1.1, 1.2, 1.3 (subsections of chapter 1)
- 2.1, 2.2 (subsections of chapter 2)
- Eller om ingen numrering: rubrik med två nivåer djuphet
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


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


def should_include_chunk(headline: str) -> bool:
    """
    Determines if a heading should be chunked (only level 1.X subsections).
    
    Returns True for:
    - Level 2 headings (1.1, 1.2, 2.1, 2.2, etc.)
    - Unnumbered headings (level 0 - treated as subsections when no chapters exist)
    
    Returns False for:
    - Level 1 headings (1, 2, 3 - main chapters)
    - Level 3+ headings (1.1.1 - too deep)
    
    Args:
        headline: the heading text to check
    
    Returns:
        Boolean indicating if this heading should become a chunk
    """
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
    sections: List[Tuple[str, int, str]]
) -> List[str]:
    """
    Saves preprocessed sections as .txt files in chunks/<document_title>/.
    
    Only saves sections at the 1.X level (subsections), skipping:
    - Main chapter headings (1, 2, 3)
    - Deeper subsections (1.1.1, 1.2.1)
    
    For each 1.X level section, also includes the parent chapter heading (1, 2, 3)
    in the metadata and filename.
    
    Args:
        document_title: title/identifier of the document
        sections: list of (headline, page_num, text_block) tuples from preprocessing
    
    Returns:
        List of saved chunk filenames (only for 1.X level sections)
    """
    doc_chunks_dir = ensure_chunk_directory(document_title)
    saved_files = []
    
    # Track the last seen chapter-level heading for context
    current_chapter_heading = None
    current_chapter_level = None
    
    for idx, (headline, page_num, text_block) in enumerate(sections, start=1):
        level = detect_heading_level(headline)
        
        # Update current chapter if we encounter a level 1 heading
        if level == 1:
            current_chapter_heading = headline
            current_chapter_level = level
            continue  # Don't save level 1 headings as chunks
        
        # Only include sections at the right level (1.1, 1.2, 2.1, etc.)
        if not should_include_chunk(headline):
            continue
        
        # Build combined headline: "Chapter / Subsection" format
        if current_chapter_heading:
            combined_headline = f"{current_chapter_heading} / {headline}"
        else:
            # If no parent chapter was found, use the headline as-is
            combined_headline = headline
        
        # Create filename from the subsection headline (not the combined one)
        filename = sanitize_filename(headline)
        
        # If filename is empty, use a generic name
        if not filename or filename == '.txt':
            filename = f"section_{idx:03d}.txt"
        
        # Ensure filename is unique if multiple sections have the same headline
        file_path = doc_chunks_dir / filename
        counter = 1
        base_name, ext = filename.rsplit('.', 1)
        while file_path.exists():
            new_filename = f"{base_name}_{counter}.{ext}"
            file_path = doc_chunks_dir / new_filename
            counter += 1
        
        # Write chunk to file with combined headline
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Rubrik: {combined_headline}\n")
            f.write(f"Sida: {page_num}\n")
            f.write(f"{'='*60}\n\n")
            f.write(text_block)
        
        saved_files.append(file_path.name)
    
    return saved_files


def load_chunks(document_title: str) -> List[Tuple[str, str]]:
    """
    Loads all chunks for a document from disk.
    
    Args:
        document_title: title/identifier of the document
    
    Returns:
        List of (filename, content) tuples
    """
    doc_chunks_dir = CHUNKS_DIR / document_title
    
    if not doc_chunks_dir.exists():
        return []
    
    chunks = []
    for chunk_file in sorted(doc_chunks_dir.glob("*.txt")):
        with open(chunk_file, 'r', encoding='utf-8') as f:
            content = f.read()
            chunks.append((chunk_file.name, content))
    
    return chunks


def remove_chunks(document_title: str):
    """
    Removes all chunks for a document from disk.
    
    Args:
        document_title: title/identifier of the document
    """
    import shutil
    
    doc_chunks_dir = CHUNKS_DIR / document_title
    
    if doc_chunks_dir.exists():
        shutil.rmtree(doc_chunks_dir)
