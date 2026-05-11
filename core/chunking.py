"""
Chunking module — saves preprocessed text sections as readable .txt files.

Each chunk represents one section or chapter from a document.
Chunks are saved to chunks/<document_title>/ with descriptive filenames.
"""

import os
from pathlib import Path
from typing import List, Tuple


CHUNKS_DIR = Path("chunks")


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
    
    Args:
        document_title: title/identifier of the document
        sections: list of (headline, page_num, text_block) tuples from preprocessing
    
    Returns:
        List of saved chunk filenames
    """
    doc_chunks_dir = ensure_chunk_directory(document_title)
    saved_files = []
    
    for idx, (headline, page_num, text_block) in enumerate(sections, start=1):
        # Create filename from headline
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
        
        # Write chunk to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Rubrik: {headline}\n")
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
