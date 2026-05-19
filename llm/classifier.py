"""
Classifier module — routes documents to correct prompts based on document type.

The user confirms the document type via dropdown when uploading.
This module does NOT auto-detect — it routes based on user-confirmed type.
"""

from typing import Tuple
from llm.prompts import instruktionsbok, reglemente, handbok, reparationsbok


# Document type constants
DOC_TYPE_INSTRUKTIONSBOK = "instruktionsbok"
DOC_TYPE_REGLEMENTE = "reglemente"
DOC_TYPE_HANDBOK = "handbok"
DOC_TYPE_REPARATIONSBOK = "reparationsbok"

# List of valid document types
VALID_DOCUMENT_TYPES = [
    DOC_TYPE_INSTRUKTIONSBOK,
    DOC_TYPE_REGLEMENTE,
    DOC_TYPE_HANDBOK,
    DOC_TYPE_REPARATIONSBOK,
]

# Swedish names for display
DOCUMENT_TYPE_LABELS = {
    DOC_TYPE_INSTRUKTIONSBOK: "Instruktionsbok",
    DOC_TYPE_REGLEMENTE: "Reglemente",
    DOC_TYPE_HANDBOK: "Handbok",
    DOC_TYPE_REPARATIONSBOK: "Reparationsbok",
}


def get_prompt_for_document_type(document_type: str, chunks_text: str) -> Tuple[str, str]:
    """
    Routes to the correct prompt based on user-confirmed document type.
    
    Args:
        document_type: type of document (must be one of VALID_DOCUMENT_TYPES)
        chunks_text: concatenated text from all document chunks
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    
    Raises:
        ValueError if document_type is not valid
    """
    if document_type not in VALID_DOCUMENT_TYPES:
        raise ValueError(f"Invalid document type: {document_type}. Must be one of {VALID_DOCUMENT_TYPES}")
    
    if document_type == DOC_TYPE_INSTRUKTIONSBOK:
        return instruktionsbok.get_prompt_instruktionsbok(chunks_text)
    
    elif document_type == DOC_TYPE_REGLEMENTE:
        return reglemente.get_prompt_reglemente(chunks_text)
    
    elif document_type == DOC_TYPE_HANDBOK:
        return handbok.get_prompt_handbok(chunks_text)
    
    elif document_type == DOC_TYPE_REPARATIONSBOK:
        return reparationsbok.get_prompt_reparationsbok(chunks_text)


def get_document_type_label(document_type: str) -> str:
    """
    Gets the Swedish display label for a document type.
    
    Args:
        document_type: document type code
    
    Returns:
        Swedish display label
    """
    return DOCUMENT_TYPE_LABELS.get(document_type, document_type)
