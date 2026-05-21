"""
Sidebar module — left panel with upload controls, document management, and run analysis button.

Handles:
- PDF file         with col3:
            if st.button("🗑️", key=f"remove_{doc_id}", use_container_width=True, type="primary"):loader
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
    
    # Check if we should clear the uploader
    if "clear_uploader" not in st.session_state:
        st.session_state.clear_uploader = False
    
    uploaded_file = st.file_uploader(
        "Välj en PDF-fil",
        type="pdf",
        label_visibility="collapsed",
        key=f"file_uploader_{st.session_state.get('uploader_key', 0)}"
    )
    
    if uploaded_file is not None:
        # Document type selection (required)
        doc_type = st.selectbox(
            "Dokumenttyp",
            options=[None] + classifier.VALID_DOCUMENT_TYPES,
            format_func=lambda x: "Välj dokumenttyp..." if x is None else classifier.get_document_type_label(x),
            key=f"doc_type_select_{st.session_state.get('uploader_key', 0)}"
        )
        
        # Confirm button - only enabled if document type is selected
        if st.button("Bekräfta och ladda upp", use_container_width=True, type="primary", disabled=(doc_type is None)):
            if doc_type is None:
                st.error("Du måste välja en dokumenttyp innan du laddar upp.")
                return
            
            try:
                # Ensure directories exist
                ingestion.ensure_directories()
                
                # Save the PDF (use filename as title since custom title was removed)
                doc_name, doc_title, file_path = ingestion.save_uploaded_pdf(
                    uploaded_file,
                    doc_type,
                    None
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
                    # Reset the uploader by incrementing the key
                    st.session_state.uploader_key = st.session_state.get('uploader_key', 0) + 1
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
    st.subheader("Uppladdade dokument")
    
    all_docs = document_registry.get_all_documents()
    
    if not all_docs:
        st.info("Inga dokument uppladdade ännu.")
        return
    
    for doc_id, doc in all_docs.items():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            status_icon = "✓" if doc["status"] == "completed" else \
                         "⏳" if doc["status"] == "processing" else \
                         "✕" if doc["status"] == "error" else "📄"
            
            st.write(f"{status_icon} {doc['document_title']}")
            st.caption(f"Typ: {classifier.get_document_type_label(doc['document_type'])}")
        
        with col2:
            if st.button("✕", key=f"remove_{doc_id}", use_container_width=True, type="secondary"):
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


def render_section_selector():
    """
    Renders a dropdown to select which level-2 section to analyze.
    Only shown if at least one document is completed.
    
    For sections with numeric headers (e.g., "2. Vård"), shows only those with a digit.
    For sections without numeric headers (pure text), shows all sections as before.
    """
    import re
    
    all_docs = document_registry.get_all_documents()
    completed_docs = [d for d in all_docs.values() if d["status"] == "completed"]
    
    if not completed_docs:
        return
    
    # Use the first (primary) completed document
    primary_doc = completed_docs[0]
    doc_id = primary_doc["document_id"]
    doc_title = primary_doc["document_title"]
    
    st.subheader("Välj analysomfång")
    
    # Load available sections from the document's chunks
    sections = chunking.get_level2_sections(doc_title)
    
    if not sections:
        st.info("Inga analyseringar sektioner hittades i dokumentet.")
        return
    
    # Create dropdown options as lists to preserve order
    section_names = [s["section_name"] for s in sections]
    section_ids = [s["section_id"] for s in sections]
    
    # Check if there are any numeric sections
    has_numeric_sections = any(re.search(r'\d', name) for name in section_names)
    
    # If there are numeric sections, filter to show only those with digits
    if has_numeric_sections:
        filtered_sections = [(name, sid) for name, sid in zip(section_names, section_ids) if re.search(r'\d', name)]
        if filtered_sections:
            section_names, section_ids = zip(*filtered_sections)
            section_names = list(section_names)
            section_ids = list(section_ids)
    
    current_selection = document_registry.get_selected_section(doc_id)
    
    # Find the correct index by section_id
    try:
        current_index = section_ids.index(current_selection) if current_selection in section_ids else 0
    except (ValueError, IndexError):
        current_index = 0
    
    # Render dropdown
    selected_name = st.selectbox(
        "Sektion att analysera",
        options=section_names,
        index=current_index,
        key=f"section_selector_{doc_id}"
    )
    
    # Save selection to registry
    if selected_name:
        selected_index = section_names.index(selected_name)
        selected_id = section_ids[selected_index]
        document_registry.set_selected_section(doc_id, selected_id)
        st.caption(f"📍 Analyserar sektion: **{selected_name}**")


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
            # Get the primary (first) completed document
            all_docs = document_registry.get_all_documents()
            completed_docs = [d for d in all_docs.values() if d["status"] == "completed"]
            
            if not completed_docs:
                st.error("Inga bearbetade dokument tillgängliga.")
                return
            
            primary_doc = completed_docs[0]
            doc_id = primary_doc["document_id"]
            doc_title = primary_doc["document_title"]
            
            # Get selected section
            selected_section_id = document_registry.get_selected_section(doc_id)
            
            if not selected_section_id:
                st.error("Välj en sektion innan du analyserar.")
                return
            
            # Load chunks for the selected section only
            section_chunks = chunking.get_chunks_for_section(doc_title, selected_section_id)
            
            if not section_chunks:
                st.error(f"Inga chunks hittades för sektion {selected_section_id}.")
                return
            
            # Format chunks for LLM with metadata
            all_chunks_text = ""
            for chunk in section_chunks:
                section_or_chapter = chunk.get("section_or_chapter", "Unknown")
                content = chunk.get("content", "")
                page_num = chunk.get("page_number", "?")
                
                all_chunks_text += f"\n\n--- {doc_title}: {section_or_chapter} (Sida {page_num}) ---\n{content}"
            
            if not all_chunks_text.strip():
                st.error("Ingen textinnehål hittades i vald sektion.")
                return
            
            # Limit input size for safety (same as before)
            max_chars = 50000
            if len(all_chunks_text) > max_chars:
                st.warning(f"⚠️ Sektionen är stor. Analyserar de första {max_chars} tecknen för att säkerställa korrekt JSON-output.")
                all_chunks_text = all_chunks_text[:max_chars]
            
            # Get document type from primary document
            doc_type = primary_doc["document_type"]
            
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
                    max_tokens=16384  # Increased from 4096 to handle large responses
                )
            
            if result_json is None:
                st.error("❌ Misslyckades att få svar från AI-modellen. Kontrollera konsolen för detaljerade felmeddelanden.")
                return
            
            # Validate that result has expected structure
            if "tasks" not in result_json:
                st.error("❌ AI-svaret saknar 'tasks'-fält. Kontrollera konsolen för detaljerade felmeddelanden.")
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
    if "analysis_result" not in st.session_state or st.session_state.analysis_result is None:
        return

    st.subheader("Ladda ner resultat")

    try:
        from export.excel_exporter import generate_excel
        
        result = st.session_state.analysis_result
        tasks = result.get("tasks", [])
        
        if tasks:
            excel_bytes = generate_excel(tasks)
            
            st.download_button(
                label="⬇ Ladda ner Excel-fil",
                data=excel_bytes,
                file_name="TNA_Analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
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
        
        # NEW: Section selector between document list and analysis button
        render_section_selector()
        st.divider()
        
        render_run_analysis_button()
        st.divider()
        
        render_download_excel_button()
