"""
Flag controls component — manages flagging of subtasks for human review.

This is integrated into the task_table.py component.
Flags are stored in st.session_state.flagged_subtasks as a set of subtask IDs.
"""

import streamlit as st
from typing import Set


def toggle_flag(subtask_id: str):
    """
    Toggles the flag status of a subtask.
    
    Args:
        subtask_id: ID of the subtask to toggle
    """
    if "flagged_subtasks" not in st.session_state:
        st.session_state.flagged_subtasks = set()
    
    if subtask_id in st.session_state.flagged_subtasks:
        st.session_state.flagged_subtasks.discard(subtask_id)
    else:
        st.session_state.flagged_subtasks.add(subtask_id)


def is_flagged(subtask_id: str) -> bool:
    """
    Checks if a subtask is flagged.
    
    Args:
        subtask_id: ID of the subtask
    
    Returns:
        True if flagged, False otherwise
    """
    if "flagged_subtasks" not in st.session_state:
        st.session_state.flagged_subtasks = set()
    
    return subtask_id in st.session_state.flagged_subtasks


def get_all_flagged() -> Set[str]:
    """
    Gets all flagged subtask IDs.
    
    Returns:
        Set of subtask IDs
    """
    if "flagged_subtasks" not in st.session_state:
        st.session_state.flagged_subtasks = set()
    
    return st.session_state.flagged_subtasks.copy()


def clear_all_flags():
    """
    Clears all flags.
    """
    if "flagged_subtasks" in st.session_state:
        st.session_state.flagged_subtasks.clear()
