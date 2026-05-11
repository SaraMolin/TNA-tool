"""
Task table component — displays the hierarchical task/subtask/step structure.

Shows tasks → subtasks → steps with:
- Task row: task_id, task
- Subtask row: subtask_id, subtask, traceability, confidence badge, uncertain warning, flag button
- Step row: step_id, step

Flagged subtasks are tracked in session_state and highlighted.
"""

import streamlit as st
from typing import List, Dict, Optional


def init_flagged_subtasks():
    """
    Initializes the flagged subtasks set in session state if it doesn't exist.
    """
    if "flagged_subtasks" not in st.session_state:
        st.session_state.flagged_subtasks = set()


def get_confidence_color(confidence: str) -> Optional[str]:
    """
    Maps confidence level to a color for highlighting rows.
    
    Args:
        confidence: 'high', 'medium', or 'low'
    
    Returns:
        Hex color code, or None for 'high' (no highlighting)
    """
    if confidence == "high":
        return None  # No highlight
    elif confidence == "medium":
        return "#FFEB3B"  # Yellow
    elif confidence == "low":
        return "#FF5252"  # Red
    return None


def render_task_table(tasks: List[Dict]):
    """
    Renders the full task hierarchy table using Streamlit columns.
    
    Args:
        tasks: List of task dicts from LLM output
    """
    init_flagged_subtasks()
    
    if not tasks:
        st.info("Ingen analys tillgänglig ännu. Ladda upp dokument och kör analys.")
        return
    
    # Create table headers
    col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 1, 0.5])
    
    with col1:
        st.write("**Kod**")
    with col2:
        st.write("**Beskrivning**")
    with col3:
        st.write("**Traceability**")
    with col4:
        st.write("**Confidence**")
    with col5:
        st.write("**Flag**")
    
    st.divider()
    
    # Render tasks and their subtasks
    for task in tasks:
        task_id = task.get("task_id", "")
        task_text = task.get("task", "")
        
        # Task row
        col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 1, 0.5])
        
        with col1:
            st.write(f"**{task_id}**")
        with col2:
            st.write(f"**{task_text}**")
        with col3:
            st.write("")
        with col4:
            st.write("")
        with col5:
            st.write("")
        
        # Render subtasks
        subtasks = task.get("subtasks", [])
        for subtask in subtasks:
            subtask_id = subtask.get("subtask_id", "")
            subtask_text = subtask.get("subtask", "")
            confidence = subtask.get("confidence", "high")
            uncertain = subtask.get("uncertain", False)
            traceability = subtask.get("traceability", {})
            
            # Check if this subtask is flagged
            is_flagged = subtask_id in st.session_state.flagged_subtasks
            
            # Get background color based on confidence
            bg_color = get_confidence_color(confidence)
            
            # Create a container with background color if needed
            if bg_color:
                st.markdown(f"""
                <div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; margin: 5px 0;">
                """, unsafe_allow_html=True)
            
            col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 1, 0.5])
            
            with col1:
                st.write(f"→ {subtask_id}")
            
            with col2:
                # Show uncertain warning if applicable
                uncertain_marker = " ⚠️" if uncertain else ""
                st.write(f"{subtask_text}{uncertain_marker}")
            
            with col3:
                # Display traceability
                doc_title = traceability.get("document_title", "")
                doc_file = traceability.get("document_filename", "")
                section = traceability.get("section_or_chapter", "")
                
                trace_text = f"{doc_title}\n{doc_file}\n{section}"
                st.caption(trace_text)
            
            with col4:
                # Display confidence as text/badge
                conf_text = f"🟢 {confidence}" if confidence == "high" else \
                           f"🟡 {confidence}" if confidence == "medium" else \
                           f"🔴 {confidence}"
                st.write(conf_text)
            
            with col5:
                # Flag button
                flag_label = "🚩" if is_flagged else "🏳️"
                if st.button(flag_label, key=f"flag_{subtask_id}"):
                    if is_flagged:
                        st.session_state.flagged_subtasks.discard(subtask_id)
                    else:
                        st.session_state.flagged_subtasks.add(subtask_id)
                    st.rerun()
            
            if bg_color:
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Render steps for this subtask
            steps = subtask.get("steps", [])
            for step in steps:
                step_id = step.get("step_id", "")
                step_text = step.get("step", "")
                
                col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 1, 0.5])
                
                with col1:
                    st.write(f"  → {step_id}")
                with col2:
                    st.write(step_text)
                with col3:
                    st.write("")
                with col4:
                    st.write("")
                with col5:
                    st.write("")
        
        st.divider()


def get_flagged_subtasks() -> set:
    """
    Gets the set of flagged subtask IDs.
    
    Returns:
        Set of subtask IDs that have been flagged
    """
    init_flagged_subtasks()
    return st.session_state.flagged_subtasks.copy()


def clear_flags():
    """
    Clears all flagged subtasks.
    """
    init_flagged_subtasks()
    st.session_state.flagged_subtasks.clear()
