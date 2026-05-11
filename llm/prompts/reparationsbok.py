"""
Prompt för Reparationsbok (Maintenance and repair procedures)

Reparationsboken innehåller procedurer för underhål och reparation av utrustning.
"""

SYSTEM_PROMPT_REPARATIONSBOK = """
Du är en expert på att analysera svenska militära reparationsbokhandböcker.
Din uppgift är att extrahera ett strukturerat hierarki av uppgifter, deluppgifter och steg 
från den tillhandahållna reparationsboktexten.

Svar ENDAST med giltigt JSON utan några förklaringar eller markdown-omslag.
"""

USER_PROMPT_TEMPLATE_REPARATIONSBOK = """
Analysera följande reparationsbok-text och extrahera uppgifter, deluppgifter och steg.

Texten från reparationsboken:
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
            "document_title": "Reparationsbokens titel",
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

def get_prompt_reparationsbok(chunks_text: str) -> tuple:
    """
    Generates system and user prompts for Reparationsbok analysis.
    
    Args:
        chunks_text: Concatenated text from all document chunks
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    user_prompt = USER_PROMPT_TEMPLATE_REPARATIONSBOK.format(chunks_text=chunks_text)
    return SYSTEM_PROMPT_REPARATIONSBOK, user_prompt
