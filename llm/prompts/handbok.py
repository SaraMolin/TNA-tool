"""
Prompt för Handbok (Reference handbooks, theory)

Handboken innehåller referensmaterial, teoretisk bakgrund och kunskapsöversikter.
"""

SYSTEM_PROMPT_HANDBOK = """
Du är en expert på att analysera svenska militära handböcker.
Din uppgift är att extrahera ett strukturerat hierarki av uppgifter, deluppgifter och steg 
från den tillhandahållna handbokstexten.

Svar ENDAST med giltigt JSON utan några förklaringar eller markdown-omslag.
"""

USER_PROMPT_TEMPLATE_HANDBOK = """
Analysera följande handbokstext och extrahera uppgifter, deluppgifter och steg.

Texten från handboken:
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
            "document_title": "Handbokens titel",
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

def get_prompt_handbok(chunks_text: str) -> tuple:
    """
    Generates system and user prompts for Handbok analysis.
    
    Args:
        chunks_text: Concatenated text from all document chunks
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    user_prompt = USER_PROMPT_TEMPLATE_HANDBOK.format(chunks_text=chunks_text)
    return SYSTEM_PROMPT_HANDBOK, user_prompt
