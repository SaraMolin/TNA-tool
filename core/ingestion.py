"""
Ingestion module — handles PDF upload, storage, and document registration.

This module manages:
- PDF uploads through the Streamlit interface
- Storage of original PDFs in the uploads/ directory
- Registration of documents in the session-state registry
- Cleanup when documents are removed
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Tuple
import streamlit as st


# Define base directories
UPLOADS_DIR = Path("uploads")
CHUNKS_DIR = Path("chunks")
OUTPUT_DIR = Path("output")


def ensure_directories():
    """
    Ensures that required directories exist.
    Creates uploads/, chunks/, and output/ directories if they don't exist.
    """
    UPLOADS_DIR.mkdir(exist_ok=True)
    CHUNKS_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)


def save_uploaded_pdf(
    uploaded_file,
    document_type: str,
    document_title: Optional[str] = None
) -> Tuple[str, str]:
    """
    Saves an uploaded PDF file to the uploads/ directory.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        document_type: Type of document (instruktionsbok, reglemente, handbok, reparationsbok)
        document_title: Optional title for the document (defaults to filename without extension)
    
    Returns:
        Tuple of (document_name, document_title, file_path)
        - document_name: original filename with extension
        - document_title: title for display/identification
        - file_path: absolute path where PDF was saved
    """
    ensure_directories()
    
    # Use provided title or derive from filename
    if document_title is None:
        document_title = uploaded_file.name.rsplit('.', 1)[0]
    
    document_name = uploaded_file.name
    
    # Save PDF to uploads/ directory
    file_path = UPLOADS_DIR / document_name
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return document_name, document_title, str(file_path)


def remove_document(document_name: str, document_title: str):
    """
    Removes a document and all associated files (PDF, chunks, output).
    
    Args:
        document_name: original filename of the document
        document_title: title/identifier of the document
    """
    # Remove uploaded PDF
    pdf_path = UPLOADS_DIR / document_name
    if pdf_path.exists():
        pdf_path.unlink()
    
    # Remove chunks folder for this document
    chunks_folder = CHUNKS_DIR / document_title
    if chunks_folder.exists():
        shutil.rmtree(chunks_folder)
    
    # Remove output file for this document (if it exists)
    output_file = OUTPUT_DIR / f"{document_title}.json"
    if output_file.exists():
        output_file.unlink()


def get_uploaded_pdf_path(document_name: str) -> Optional[str]:
    """
    Gets the path to an uploaded PDF file.
    
    Args:
        document_name: original filename of the document
    
    Returns:
        Absolute path to the PDF file, or None if it doesn't exist
    """
    pdf_path = UPLOADS_DIR / document_name
    if pdf_path.exists():
        return str(pdf_path)
    return None


def get_all_uploaded_documents() -> list:
    """
    Gets a list of all currently uploaded PDF documents.
    
    Returns:
        List of document metadata dicts from session state registry
    """
    if "document_registry" not in st.session_state:
        return []
    
    return list(st.session_state.document_registry.values())


def list_uploaded_pdfs() -> list:
    """
    Lists all PDF files in the uploads/ directory.
    
    Returns:
        List of filenames (without directory path)
    """
    ensure_directories()
    
    if not UPLOADS_DIR.exists():
        return []
    
    return [f.name for f in UPLOADS_DIR.glob("*.pdf")]
