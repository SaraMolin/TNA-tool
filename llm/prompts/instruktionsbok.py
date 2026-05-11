"""
Prompt för Instruktionsbok (Operation/instruction manuals)

Instruktionsboken innehåller detaljerade instruktioner för att genomföra operativa uppgifter.
"""

SYSTEM_PROMPT_INSTRUKTIONSBOK = """
Du är en expert på att analysera svenska militära instruktionsbokhandböcker.
Din uppgift är att extrahera ett strukturerat hierarki av uppgifter, deluppgifter och steg 
från den tillhandahållna texten.

Svar ENDAST med giltigt JSON utan några förklaringar eller markdown-omslag.
"""

USER_PROMPT_TEMPLATE_INSTRUKTIONSBOK = """
Analysera följande instruktionsbok-text och extrahera uppgifter, deluppgifter och steg.

Texten från instruktionsboken:
{chunks_text}

Retunera svaret i denna exakta JSON-struktur. Alla fält måste fyllas i. Returnera ENDAST JSON:

{{
  "tasks": [
    {{
      "task": "Beskrivning av huvuduppgift",
      "task_id": "01-00-00",
      "subtasks": [
        {{
          "subtask": "Beskrivning av deluppgift",
          "subtask_id": "01-01-00",
          "steps": [
            {{
              "step": "Beskrivning av steg",
              "step_id": "01-01-01"
            }}
          ],
          "traceability": {{
            "document_filename": "filnamn.pdf",
            "document_title": "Instruktionsbokens titel",
            "section_or_chapter": "Avsnitt eller kapitel"
          }},
          "confidence": "high",
          "uncertain": false
        }}
      ]
    }}
  ]
}}
"""

def get_prompt_instruktionsbok(chunks_text: str) -> tuple:
    """
    Generates system and user prompts for Instruktionsbok analysis.
    
    Args:
        chunks_text: Concatenated text from all document chunks
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    user_prompt = USER_PROMPT_TEMPLATE_INSTRUKTIONSBOK.format(chunks_text=chunks_text)
    return SYSTEM_PROMPT_INSTRUKTIONSBOK, user_prompt
