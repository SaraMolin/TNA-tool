"""
Document registry module — manages uploaded document metadata in session state.

Tracks all uploaded documents with their metadata:
- document_name: original filename
- document_title: title for display/identification
- document_type: instruktionsbok, reglemente, handbok, or reparationsbok
- file_path: path to saved PDF
- status: 'pending', 'processing', 'completed', 'error'
- chunks_saved: list of saved chunk filenames
"""

import streamlit as st
from typing import Dict, Optional
from datetime import datetime


def init_registry():
    """
    Initializes the document registry in session state if it doesn't exist.
    """
    if "document_registry" not in st.session_state:
        st.session_state.document_registry = {}


def register_document(
    document_name: str,
    document_title: str,
    document_type: str,
    file_path: str
) -> str:
    """
    Registers a new document in the session-state registry.
    
    Args:
        document_name: original filename
        document_title: title for display/identification
        document_type: type of document (instruktionsbok, reglemente, handbok, reparationsbok)
        file_path: path to saved PDF file
    
    Returns:
        Unique document ID used in the registry
    """
    init_registry()
    
    # Use document_title as the unique key
    doc_id = document_title
    
    st.session_state.document_registry[doc_id] = {
        "document_id": doc_id,
        "document_name": document_name,
        "document_title": document_title,
        "document_type": document_type,
        "file_path": file_path,
        "status": "pending",
        "chunks_saved": [],
        "created_at": datetime.now().isoformat(),
        "error_message": None,
    }
    
    return doc_id


def update_document_status(
    document_id: str,
    status: str,
    chunks_saved: Optional[list] = None,
    error_message: Optional[str] = None
):
    """
    Updates the status of a registered document.
    
    Args:
        document_id: unique document ID from registry
        status: new status (pending, processing, completed, error)
        chunks_saved: optional list of saved chunk filenames
        error_message: optional error message if status is 'error'
    """
    init_registry()
    
    if document_id in st.session_state.document_registry:
        st.session_state.document_registry[document_id]["status"] = status
        
        if chunks_saved is not None:
            st.session_state.document_registry[document_id]["chunks_saved"] = chunks_saved
        
        if error_message is not None:
            st.session_state.document_registry[document_id]["error_message"] = error_message


def get_document(document_id: str) -> Optional[Dict]:
    """
    Retrieves a document from the registry.
    
    Args:
        document_id: unique document ID
    
    Returns:
        Document metadata dict, or None if not found
    """
    init_registry()
    return st.session_state.document_registry.get(document_id)


def get_all_documents() -> Dict[str, Dict]:
    """
    Gets all registered documents.
    
    Returns:
        Dict of document_id -> document metadata
    """
    init_registry()
    return st.session_state.document_registry.copy()


def remove_document(document_id: str):
    """
    Removes a document from the registry.
    
    Args:
        document_id: unique document ID
    """
    init_registry()
    
    if document_id in st.session_state.document_registry:
        del st.session_state.document_registry[document_id]


def document_exists(document_id: str) -> bool:
    """
    Checks if a document exists in the registry.
    
    Args:
        document_id: unique document ID
    
    Returns:
        True if document exists, False otherwise
    """
    init_registry()
    return document_id in st.session_state.document_registry


def get_documents_by_status(status: str) -> list:
    """
    Gets all documents with a specific status.
    
    Args:
        status: status to filter by
    
    Returns:
        List of document metadata dicts
    """
    init_registry()
    return [
        doc for doc in st.session_state.document_registry.values()
        if doc["status"] == status
    ]


def get_document_type(document_id: str) -> Optional[str]:
    """
    Gets the document type for a registered document.
    
    Args:
        document_id: unique document ID
    
    Returns:
        Document type, or None if not found
    """
    doc = get_document(document_id)
    if doc:
        return doc["document_type"]
    return None
