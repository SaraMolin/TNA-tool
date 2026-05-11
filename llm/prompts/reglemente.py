"""
Prompt för Reglemente (Regulations, doctrine, field manuals)

Reglementet innehåller föreskrifter, doktrin och riktlinjer för operativ verksamhet.
"""

SYSTEM_PROMPT_REGLEMENTE = """
Du är en expert på att analysera svenska militära reglementen.
Din uppgift är att extrahera ett strukturerat hierarki av uppgifter, deluppgifter och steg 
från den tillhandahållna reglemententexten.

Svar ENDAST med giltigt JSON utan några förklaringar eller markdown-omslag.
"""

USER_PROMPT_TEMPLATE_REGLEMENTE = """
Analysera följande reglementetext och extrahera uppgifter, deluppgifter och steg.

Texten från reglementet:
{chunks_text}

Returnera svaret i denna exakta JSON-struktur. Alla fält måste fyllas i. Returnera ENDAST JSON:

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
            "document_title": "Reglementes titel",
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

def get_prompt_reglemente(chunks_text: str) -> tuple:
    """
    Generates system and user prompts for Reglemente analysis.
    
    Args:
        chunks_text: Concatenated text from all document chunks
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    user_prompt = USER_PROMPT_TEMPLATE_REGLEMENTE.format(chunks_text=chunks_text)
    return SYSTEM_PROMPT_REGLEMENTE, user_prompt
