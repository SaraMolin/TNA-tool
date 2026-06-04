"""
Task table component — displays the hierarchical task/subtask/step structure.

Shows tasks → subtasks → steps with:
- Task row: task_id, task
- Subtask row: subtask_id, subtask, traceability, confidence badge, uncertain warning, flag button
- Step row: step_id, step

Flagged subtasks are tracked in session_state and highlighted.
"""

import html as html_lib
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
    Renders the full task hierarchy table in staircase format.

    Each level gets its own row:
    - Task row:    ID=task_id    | Task text | (empty)        | (empty)     | (empty)
    - Subtask row: ID=subtask_id | (empty)   | Subtask text   | (empty)     | Traceability
    - Step row:    ID=step_id    | (empty)   | (empty)        | Step text   | (empty)

    Args:
        tasks: List of task dicts from LLM output
    """
    init_flagged_subtasks()

    if not tasks:
        st.info("Ingen analys tillgänglig ännu. Ladda upp dokument och kör analys.")
        return

    def e(text: str) -> str:
        return html_lib.escape(str(text))

    def td(content: str, bold: bool = False) -> str:
        inner = f"<strong>{content}</strong>" if bold else content
        return f'<td style="padding:8px 12px; vertical-align:top;">{inner}</td>'

    TASK_BG    = "#C8C8C8"
    SUBTASK_BG = "#E8E8E8"
    STEP_BG    = "#FFFFFF"

    rows = []
    for task in tasks:
        task_id   = e(task.get("task_id", ""))
        task_text = e(task.get("task", ""))

        rows.append(
            f'<tr style="background:{TASK_BG};">'
            + td(task_id, bold=True)
            + td(task_text, bold=True)
            + td("") + td("") + td("")
            + "</tr>"
        )

        for subtask in task.get("subtasks", []):
            subtask_id   = e(subtask.get("subtask_id", ""))
            subtask_text = e(subtask.get("subtask", ""))
            traceability = subtask.get("traceability", {})
            trace_text   = e(
                f"{traceability.get('document_filename', '')} "
                f"{traceability.get('section_or_chapter', '')}"
            )
            confidence   = subtask.get("confidence", "high")
            row_bg       = get_confidence_color(confidence) or SUBTASK_BG

            rows.append(
                f'<tr style="background:{row_bg};">'
                + td(subtask_id)
                + td("") + td(subtask_text) + td("")
                + td(trace_text)
                + "</tr>"
            )

            for step in subtask.get("steps", []):
                step_id   = e(step.get("step_id", ""))
                step_text = e(step.get("step", ""))

                rows.append(
                    f'<tr style="background:{STEP_BG};">'
                    + td(step_id)
                    + td("") + td("") + td(step_text) + td("")
                    + "</tr>"
                )

    header_style = "padding:8px 12px; text-align:left; border-bottom:2px solid #999; background:#F5F5F5;"
    html = f"""
    <table style="width:100%; border-collapse:collapse; font-size:14px;">
      <thead>
        <tr>
          <th style="{header_style} width:9%;">ID</th>
          <th style="{header_style} width:22%;">Task</th>
          <th style="{header_style} width:22%;">Subtask</th>
          <th style="{header_style} width:22%;">Step</th>
          <th style="{header_style} width:25%;">Traceability</th>
        </tr>
      </thead>
      <tbody>
        {"".join(rows)}
      </tbody>
    </table>
    """
    st.markdown(html, unsafe_allow_html=True)


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
