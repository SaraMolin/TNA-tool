"""
PDF viewer module — displays uploaded PDFs in the right panel.

Shows document titles as buttons. Clicking a button displays that PDF.
Uses base64 encoding to embed PDF in HTML iframe.
"""

import streamlit as st
import base64
from pathlib import Path
from typing import Optional

from core import ingestion, document_registry


def get_pdf_as_base64(pdf_path: str) -> Optional[str]:
    """
    Reads a PDF file and encodes it as base64 for embedding in HTML.
    
    Args:
        pdf_path: path to PDF file
    
    Returns:
        Base64-encoded PDF, or None if file doesn't exist
    """
    try:
        with open(pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
            return base64.b64encode(pdf_bytes).decode()
    except Exception as e:
        print(f"Error reading PDF: {str(e)}")
        return None


def render_pdf_viewer():
    """
    Renders the PDF viewer panel in the right column.
    Shows document buttons and displays the selected PDF.
    """
    st.subheader("PDF-visare")
    
    all_docs = document_registry.get_all_documents()
    
    if not all_docs:
        st.info("Ladda upp ett dokument för att se det här.")
        return
    
    # Initialize selected document in session state
    if "selected_pdf_doc_id" not in st.session_state:
        # Default to first document
        first_doc_id = list(all_docs.keys())[0]
        st.session_state.selected_pdf_doc_id = first_doc_id
    
    # Document selection buttons
    st.write("**Välj dokument:**")
    
    for doc_id, doc in all_docs.items():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            if st.button(
                doc["document_title"],
                key=f"pdf_select_{doc_id}",
                use_container_width=True
            ):
                st.session_state.selected_pdf_doc_id = doc_id
        
        with col2:
            # Show status indicator
            status_icon = "✅" if doc["status"] == "completed" else "⏳"
            st.caption(status_icon)
    
    st.divider()
    
    # Display selected PDF
    selected_doc_id = st.session_state.selected_pdf_doc_id
    
    if selected_doc_id not in all_docs:
        st.warning("Valtt dokument inte längre tillgängligt.")
        return
    
    selected_doc = all_docs[selected_doc_id]
    pdf_path = selected_doc["file_path"]
    
    # Check if file exists
    if not Path(pdf_path).exists():
        st.error(f"PDF-fil inte hittad: {pdf_path}")
        return
    
    st.write(f"**{selected_doc['document_title']}**")
    
    # Encode and display PDF
    pdf_base64 = get_pdf_as_base64(pdf_path)
    
    if pdf_base64:
        # Embed PDF using iframe
        pdf_display = f"""
        <iframe
            src="data:application/pdf;base64,{pdf_base64}"
            width="100%"
            height="800"
            type="application/pdf"
        ></iframe>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.error("Kunde inte läsa PDF-filen.")
