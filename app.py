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
    # Create two-column layout
    left_col, right_col = st.columns([1, 2])
    
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
    
    with right_col:
        pdf_viewer.render_pdf_viewer()


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
