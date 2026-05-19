"""
TNA Tool — Training Needs Analysis automation tool

Main Streamlit application entry point.
Combines all modules into a cohesive interface for document upload,
LLM analysis, and result visualization/export.

Two-column layout:
- Left: Upload controls, document list, analysis button, Excel download
- Right: PDF viewer

The app uses session_state to maintain state across interactions.
"""

import streamlit as st
from pathlib import Path

# Import core modules
from core import document_registry, ingestion
from ui import sidebar, pdf_viewer
from ui.components import task_table


def init_app_state():
    """
    Initializes application session state on first load.
    """
    # Initialize document registry
    document_registry.init_registry()
    
    # Ensure directories exist
    ingestion.ensure_directories()
    
    # Initialize analysis result
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    
    # Initialize flagged subtasks
    if "flagged_subtasks" not in st.session_state:
        st.session_state.flagged_subtasks = set()


def configure_page():
    """
    Configures Streamlit page settings.
    """
    st.set_page_config(
        page_title="TNA Tool - Training Needs Analysis",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better layout
    st.markdown("""
        <style>
            .main {
                padding: 2rem 1rem;
            }
            [data-testid="stSidebar"] {
                background-color: #f0f2f6;
            }
        </style>
    """, unsafe_allow_html=True)


def render_main_content():
    """
    Renders the main content area with two columns.
    """
    # Initialize PDF viewer visibility state
    if "show_pdf_viewer" not in st.session_state:
        st.session_state.show_pdf_viewer = True
    
    # Determine column layout based on PDF viewer visibility
    if st.session_state.show_pdf_viewer:
        # Create two-column layout
        # Left column (analysis results): 2/3, Right column (PDF viewer): 1/3
        left_col, right_col = st.columns([2, 1])
    else:
        # Single column for analysis results only
        left_col = st.container()
        right_col = None
    
    with left_col:
        st.subheader("Analysresultat")
        
        if "analysis_result" in st.session_state and st.session_state.analysis_result:
            result = st.session_state.analysis_result
            tasks = result.get("tasks", [])
            
            if tasks:
                # Display task table
                task_table.render_task_table(tasks)
                
                # Show flagged subtasks summary
                flagged = task_table.get_flagged_subtasks()
                if flagged:
                    st.warning(f"🚩 {len(flagged)} deluppgifter flaggade för granskning")
            else:
                st.info("Ingen uppgifter i analysresultatet.")
        else:
            st.info("Kör en analys för att se resultat.")
    
    if st.session_state.show_pdf_viewer and right_col is not None:
        with right_col:
            # Toggle button for PDF viewer
            col1, col2 = st.columns([5, 1])
            with col2:
                if st.button("✕", key="close_pdf_viewer", help="Stäng PDF-visare"):
                    st.session_state.show_pdf_viewer = False
                    st.rerun()
            
            with col1:
                pass  # Spacer for layout
            
            pdf_viewer.render_pdf_viewer()
    else:
        # Show button to open PDF viewer when closed
        if st.button("📄 Öppna PDF-visare", use_container_width=True):
            st.session_state.show_pdf_viewer = True
            st.rerun()


def main():
    """
    Main application entry point.
    """
    # Configure page
    configure_page()
    
    # Initialize state
    init_app_state()
    
    # Render sidebar
    sidebar.render_sidebar()
    
    # Render main content
    render_main_content()


if __name__ == "__main__":
    main()
