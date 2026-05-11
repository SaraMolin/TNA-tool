"""
Sidebar module — left panel with upload controls, document management, and run analysis button.

Handles:
- PDF file uploader
- Document type selection (dropdown)
- Document list with remove buttons
- "Run Analysis" button
- Download Excel button (when results exist)
"""

import streamlit as st
from typing import Optional, Tuple
import json
from pathlib import Path

from core import ingestion, document_registry, preprocessing, chunking
from llm import classifier, client
from ui.components import task_table


def render_upload_section():
    """
    Renders the upload section with file uploader and document type selector.
    """
    st.subheader("Ladda upp dokument")
    
    uploaded_file = st.file_uploader(
        "Välj en PDF-fil",
        type="pdf",
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        # Document type selection
        doc_type = st.selectbox(
            "Dokumenttyp",
            options=classifier.VALID_DOCUMENT_TYPES,
            format_func=classifier.get_document_type_label,
            key="doc_type_select"
        )
        
        # Optional custom title
        custom_title = st.text_input(
            "Dokumenttitel (valfritt, använder filnamn annars)",
            label_visibility="collapsed"
        )
        
        # Confirm button
        if st.button("Bekräfta och ladda upp", use_container_width=True):
            try:
                # Ensure directories exist
                ingestion.ensure_directories()
                
                # Save the PDF
                doc_name, doc_title, file_path = ingestion.save_uploaded_pdf(
                    uploaded_file,
                    doc_type,
                    custom_title if custom_title else None
                )
                
                # Register document
                doc_id = document_registry.register_document(
                    document_name=doc_name,
                    document_title=doc_title,
                    document_type=doc_type,
                    file_path=file_path
                )
                
                # Start processing in background (preprocessing + chunking)
                try:
                    document_registry.update_document_status(doc_id, "processing")
                    
                    # Preprocess and chunk
                    sections = preprocessing.preprocess_pdf(file_path)
                    chunks_saved = chunking.save_chunks(doc_title, sections)
                    
                    # Update status
                    document_registry.update_document_status(doc_id, "completed", chunks_saved)
                    
                    st.success(f"{doc_title} laddat upp och bearbetat!")
                    st.rerun()
                
                except Exception as e:
                    document_registry.update_document_status(
                        doc_id,
                        "error",
                        error_message=str(e)
                    )
                    st.error(f"Fel vid bearbetning: {str(e)}")
            
            except Exception as e:
                st.error(f"Fel vid uppladdning: {str(e)}")


def render_document_list():
    """
    Renders the list of uploaded documents with remove buttons.
    """
    st.subheader("📋 Uppladdade dokument")
    
    all_docs = document_registry.get_all_documents()
    
    if not all_docs:
        st.info("Inga dokument uppladdade ännu.")
        return
    
    for doc_id, doc in all_docs.items():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            status_icon = "✅" if doc["status"] == "completed" else \
                         "⏳" if doc["status"] == "processing" else \
                         "❌" if doc["status"] == "error" else "📄"
            
            st.write(f"{status_icon} {doc['document_title']}")
            st.caption(f"Typ: {classifier.get_document_type_label(doc['document_type'])}")
        
        with col2:
            st.caption(doc["status"])
        
        with col3:
            if st.button("🗑️", key=f"remove_{doc_id}", use_container_width=True):
                try:
                    # Remove files
                    ingestion.remove_document(
                        doc["document_name"],
                        doc["document_title"]
                    )
                    
                    # Remove from registry
                    document_registry.remove_document(doc_id)
                    
                    st.success("Dokument borttaget.")
                    st.rerun()
                
                except Exception as e:
                    st.error(f"Fel vid borttagning: {str(e)}")


def render_run_analysis_button():
    """
    Renders the "Run Analysis" button.
    Collects all chunks from all uploaded documents and sends to LLM.
    """
    st.subheader("Generera TNA-analys")
    
    all_docs = document_registry.get_all_documents()
    completed_docs = [d for d in all_docs.values() if d["status"] == "completed"]
    
    if not completed_docs:
        st.info("Ladda upp och bearbeta minst ett dokument innan du analyserar.")
        return
    
    if st.button("Kör analys", use_container_width=True, type="primary"):
        try:
            # Collect chunks from all completed documents
            all_chunks_text = ""
            
            for doc in completed_docs:
                doc_title = doc["document_title"]
                chunks = chunking.load_chunks(doc_title)
                
                for chunk_filename, chunk_content in chunks:
                    all_chunks_text += f"\n\n--- {doc_title}: {chunk_filename} ---\n{chunk_content}"
            
            if not all_chunks_text.strip():
                st.error("Ingen textinnehål hittades i dokumenten.")
                return
            
            # Get document type from first document (assuming uniform type for now)
            # TODO: Future enhancement — handle mixed document types
            doc_type = completed_docs[0]["document_type"]
            
            # Get prompts
            system_prompt, user_prompt = classifier.get_prompt_for_document_type(
                doc_type,
                all_chunks_text
            )
            
            # Call LLM
            with st.spinner("Analyserar med AI..."):
                llm_client = client.get_azure_client()
                result_json = llm_client.send_prompt_for_json(
                    system_prompt=system_prompt,
                    user_message=user_prompt,
                    temperature=0.3,
                    max_tokens=4096
                )
            
            if result_json is None:
                st.error("Misslyckades att få svar från AI-modellen.")
                return
            
            # Save result to session state and file
            st.session_state.analysis_result = result_json
            
            # Save to output/ for reference
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / "latest_analysis.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_json, f, ensure_ascii=False, indent=2)
            
            st.success("✅ Analys slutförd!")
            st.rerun()
        
        except Exception as e:
            st.error(f"Fel vid analys: {str(e)}")


def render_download_excel_button():
    """
    Renders the Excel download button when analysis results exist.
    """
    if "analysis_result" not in st.session_state:
        return

    st.subheader("Ladda ner resultat")

    try:
        from export.excel_exporter import generate_excel
        
        result = st.session_state.analysis_result
        tasks = result.get("tasks", [])
        
        if tasks:
            excel_bytes = generate_excel(tasks)
            
            st.download_button(
                label="⬇️ Ladda ner Excel-fil",
                data=excel_bytes,
                file_name="TNA_Analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    except Exception as e:
        st.error(f"Fel vid generering av Excel-fil: {str(e)}")


def render_sidebar():
    """
    Renders the complete left sidebar.
    """
    with st.sidebar:
        st.title("TNA-verktyg")
        
        render_upload_section()
        st.divider()
        
        render_document_list()
        st.divider()
        
        render_run_analysis_button()
        st.divider()
        
        render_download_excel_button()
