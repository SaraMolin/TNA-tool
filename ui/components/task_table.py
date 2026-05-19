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
    Renders the full task hierarchy table in hierarchical format.
    
    Structure:
    - Task row (bold): Task ID | Task | Subtask | Step | Traceability
    - Subtask row: | | Subtask ID + Subtask text | | Traceability
    - Step row: | | | Step ID + Step text | Traceability
    
    Args:
        tasks: List of task dicts from LLM output
    """
    init_flagged_subtasks()
    
    if not tasks:
        st.info("Ingen analys tillgänglig ännu. Ladda upp dokument och kör analys.")
        return
    
    # Create table headers with proper column widths
    col1, col2, col3, col4, col5 = st.columns([0.8, 2, 2, 2, 2.5])
    
    with col1:
        st.write("**Task ID**")
    with col2:
        st.write("**Task**")
    with col3:
        st.write("**Subtask**")
    with col4:
        st.write("**Step**")
    with col5:
        st.write("**Traceability**")
    
    st.divider()
    
    # Render tasks and their subtasks
    for task in tasks:
        task_id = task.get("task_id", "")
        task_text = task.get("task", "")
        
        # Render subtasks
        subtasks = task.get("subtasks", [])
        for subtask_idx, subtask in enumerate(subtasks):
            subtask_id = subtask.get("subtask_id", "")
            subtask_text = subtask.get("subtask", "")
            traceability = subtask.get("traceability", {})
            
            # Get traceability text
            doc_title = traceability.get("document_title", "")
            doc_file = traceability.get("document_filename", "")
            section = traceability.get("section_or_chapter", "")
            trace_text = f"{doc_title}: {doc_file} {section}"
            
            # Render steps for this subtask
            steps = subtask.get("steps", [])
            
            if steps:
                # If there are steps, render first step with task/subtask info
                for step_idx, step in enumerate(steps):
                    step_id = step.get("step_id", "")
                    step_text = step.get("step", "")
                    
                    col1, col2, col3, col4, col5 = st.columns([0.8, 2, 2, 2, 2.5])
                    
                    with col1:
                        # Show task_id only on first subtask
                        if step_idx == 0 and subtask_idx == 0:
                            st.write(f"**{task_id}**")
                        else:
                            st.write("")
                    
                    with col2:
                        # Show task text only on first subtask/step
                        if step_idx == 0 and subtask_idx == 0:
                            st.write(f"**{task_text}**")
                        else:
                            st.write("")
                    
                    with col3:
                        # Show subtask only on first step of this subtask
                        if step_idx == 0:
                            st.write(f"{subtask_id}: {subtask_text}")
                        else:
                            st.write("")
                    
                    with col4:
                        st.write(f"{step_id}: {step_text}")
                    
                    with col5:
                        st.write(trace_text)
            else:
                # No steps, just show subtask row
                col1, col2, col3, col4, col5 = st.columns([0.8, 2, 2, 2, 2.5])
                
                with col1:
                    if subtask_idx == 0:
                        st.write(f"**{task_id}**")
                    else:
                        st.write("")
                
                with col2:
                    if subtask_idx == 0:
                        st.write(f"**{task_text}**")
                    else:
                        st.write("")
                
                with col3:
                    st.write(f"{subtask_id}: {subtask_text}")
                
                with col4:
                    st.write("")
                
                with col5:
                    st.write(trace_text)
        
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
