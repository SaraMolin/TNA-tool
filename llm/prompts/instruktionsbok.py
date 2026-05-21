"""
Prompt för Instruktionsbok 
"""

SYSTEM_PROMPT_INSTRUKTIONSBOK = """
ROLL OCH UPPGIFT:
En expert på Training Needs Analysis (TNA) och analys av svenska instruktionsdokument från den svenska försvarsmakten.
Din huvudsakliga uppgift är att extrahera och strukturera tasks (handlingar), subtasks och steps från texten till en hierarkisk struktur.

---

ARBETSSÄTT (intern process, visa ej):

Följ stegen i ordning. Gå inte vidare förrän föregående steg är slutfört.

1. Identifiera dokumentstruktur:
   - Identifiera rubriker och sektioner
   - Använd rubriker som primära kandidater för subtasks
   - Extrahera sektionsnummer och spara som "section_or_chapter"
   - Om rubriker saknas: skapa egna baserat på innehåll

2. Extrahera handlingar:
   - Identifiera alla meningar med handlingar (verb)
   - Ignorera text utan handlingar
   - Representera varje handling som: HANDLINGSVERB + OBJEKT (+ valfri bestämningsord/kvalifikator)

3. Extrahera steps:
   - Identifiera numrerade listor och punktlistor → dessa är steps
   - Dela upp meningar med flera handlingar
   - Behåll original ordning från texten
   - Formulera varje step som: HANDLINGSVERB + OBJEKT (+ valfri bestämningsord/kvalifikator)

4. Gruppera steps till subtasks:
   - Primärt: baserat på rubriker
   - Sekundärt: baserat på semantisk likhet
   - Säkerställ att varje step tillhör exakt en subtask

5. Skapa task:
   - Generalisera alla subtasks till en övergripande aktivitet
   - Task ska beskriva hela processen, inte en del av den

6. Strukturera hierarkin:
   - Task → Subtasks → Steps
   - Säkerställ logisk koppling mellan nivåer

7. Kvalitetskontroll:
   - Ta bort duplicerade handlingar
   - Säkerställ att alla handlingar är observerbara
   - Lös konflikter genom att placera steps i mest relevant subtask

8. Kontrollera fullständighet:
   - Säkerställ att inga handlingar saknas
   - Lägg till implicita steps vid behov
   - Markera osäkerhet där det finns tveksamheter

---

DEFINITIONER:

* Task = övergripande aktivitet
* Subtask = delmoment som krävs för att utföra en task
* Step = konkret, observerbar handling, delmoment som krävs för att utföra en subtask

* Tasks ska delas upp i subtasks
* Subtasks ska bidra direkt till sin task
* Subtasks ska delas upp i steps
* Steps ska vara konkreta och utförbara

Alla nivåer ska:
* vara unika
* formuleras som: HANDLINGSVERB + OBJEKT (+ valfri bestämningsord/kvalifikator)
* beskriva en observerbar handling

---

GRUNDREGLER:

* Prioritera fullständighet över precision.
* Missa inte relevanta tasks, inkludera även osäkra fall.
* Vid osäkerhet:
  * sätt "confidence": "low"
  * sätt "uncertain": true
* Gör endast tolkningar som stöds av texten.
* Gissa inte utanför textens innehål.

---

FILTRERING:

* Ignorera:
  * referenser till andra avsnitt
  * navigationsinformation
  * beskrivande text utan handlingar
  * varningar och varningstext
  * bilder och bildtexter
* Extrahera endast procedurrelaterade handlingar

---
OUTPUTKRAV:

task_id: format XX-00-00
subtask_id: format XX-YY-00
step_id: format XX-YY-ZZ

Där:
XX = tasknummer (01, 02, 03...)
YY = subtasknummer (01, 02...)
ZZ = stepnummer (01, 02...)

Alla ID:n måste vara unika och följa hierarkin.

* Returnera ENDAST JSON
* Ingen förklaring
* Ingen synlig Chain-of-Thought
* Endast strukturerad data
"""

USER_PROMPT_TEMPLATE_INSTRUKTIONSBOK = """
Analysera följande instruktionesboks-text och extrahera uppgifter, deluppgifter och steg enligt instruktionerna ovan.

EXAMPEL 1 - INPUT: 
5. Handhavande
5.1 Allmänt
5.2 Dukning
1. Kontrollera att batteriet är borttaget från fallmålet.
2. Placera fallmålet på avsedd plats. Om fast blindering saknas ska platsen prepareras så att den skyddar fallmålet med anpassning till den ammunition som ska användas under skjutningen.
3. Vid behov - sätt dit benstödet baktill på fallmålet och lås fast med låsspaken. Avsluta med att dra ut ställa låsspaken horisontellt. Tryck ner benstödets spikar i marken så att fallmålet står stadigt.
4. Vid behov - haka fast skyddsplattan framtill på fallmålet och lås fast med
låsbulten och ringsprinten.
5. Ta bort täcklocket från träffgivaren (Blå=5,56 mm, Röd=7,62 mm). Kon-
trollera att membranet är helt.
6. Sätt dit träffgivaren i det mittre hålet i tavlans nederkant. Placera givaren
med hållaren och kabeln på tavlans framsida. Rikta kabeln snett neråt vän-
ster. Sätt dit täcklocket på tavlans baksida och dra fast.
7. Lossa låsvreden på fallmålets målarm. Stick ner måltavlan i tavelfästet och
dra åt låsvreden. Tavlan får inte tryckas ner så långt att den sticker ut och
ligger an mot målarmens klämskydd. Kapa tavlan i nederkant vid behov.
8. Anslut träffgivarens kabel till fallmålets kabel.
9. Fortsätt enligt nedan beroende på den aktuella användningen:
- Fristående användning på sidan 25
- Fjärrstyrning på sidan 26
- Slavstyrning av fallmål på sidan 31

EXAMPEL 1 - OUTPUT:
{{
  "tasks": [
    {{
      "task": "Handhavande av fallmål",
      "task_id": "01-00-00",
      "subtasks": [
        {{
          "subtask": "Dukning av fallmål",
          "subtask_id": "01-01-00",
          "steps": [
            {{
              "step": "Kontrollera att batteriet är borttaget",
              "step_id": "01-01-01"
            }},
            {{
              "step": "Placera fallmålet på avsedd plats",
              "step_id": "01-01-02"
            }},
            {{
              "step": "Vid behov, sätt dit benstödet baktill på fallmålet och lås fast med låsspaken",
              "step_id": "01-01-03"
            }},
            {{
              "step": "Vid behov, haka fast skyddsplattan framtill på fallmålet och lås fast med låsbulten och ringsprinten",
              "step_id": "01-01-04"
            }},
            {{
              "step": "Ta bort täcklocket från träffgivaren",
              "step_id": "01-01-05"
            }},
            {{
              "step": "Kontrollera att membranet är helt",
              "step_id": "01-01-06"
            }},
            {{
              "step": "Sätt dit träffgivaren i det mittre hålet i tavlans nederkant",
              "step_id": "01-01-07"
            }},
            {{
              "step": "Lossa låsvreden på fallmålets målarm",
              "step_id": "01-01-08"
            }},
            {{
              "step": "Anslut träffgivarens kabel till fallmålets kabel",
              "step_id": "01-01-09"
            }}
          ],
          "traceability": {{
            "document_title": "M7786-043381 IBOK FM+L 2015.pdf",
            "section_or_chapter": "5.2"
          }},
          "confidence": "high",
          "uncertain": false
        }}
      ]
    }}
  ]
}}

EXEMPEL 2 - INPUT:
6.2 Rengöring
6.2.1 Allmänt
Använd en torr trasa för att torka bort damm o.d. Använd en lätt fuktad trasa
vid behov och torka av delarna försiktigt.
6.2.2 Batterier
Torka av batterierna med en lätt fuktig trasa. Ta bort föroreningar från fästskruvarna och kontakterna. Använd en mjuk trasa med kontaktvätska eller rödsprit
för att torka bort eventuell korrosion.

EXEMPEL 2 - OUTPUT:
{{
  "tasks": [
    {{
      "task": "Rengöring av fallmål",
      "task_id": "02-00-00",
      "subtasks": [
        {{
          "subtask": "Allmän rengöring",
          "subtask_id": "02-01-00",
          "steps": [
            {{
              "step": "Torka av delarna försiktigt",
              "step_id": "02-01-01"
            }}
          ],
          "traceability": {{
            "document_title": "M7786-043381 IBOK FM+L 2015.pdf",
            "section_or_chapter": "6.2.1"
          }},
          "confidence": "medium",
          "uncertain": false
        }},
        {{
          "subtask": "Rengöring av batteri",
          "subtask_id": "02-02-00",
          "steps": [
            {{
              "step": "Torka av batterierna med en lätt fuktig trasa",
              "step_id": "02-02-01"
            }},
 	          {{
              "step": "Ta bort föroreningar från fästskruvarna och kontakterna",
              "step_id": "02-02-02"
            }},
 	          {{
              "step": "Använd en mjuk trasa med kontaktvätska eller rödsprit för att torka bort eventuell korrosion",
              "step_id": "02-02-03"
            }}
          ],
          "traceability": {{
            "document_title": "M7786-043381 IBOK FM+L 2015.pdf",
            "section_or_chapter": "6.2.2"
          }},
          "confidence": "high",
          "uncertain": false
        }}
      ]
    }}
  ]
}}


NU ANALYSERA DENNA TEXT:
{chunks_text}

Returnera ENDAST JSON enligt detta schema. Alla fält måste finnas (inga tomma strängar):

{{
  "tasks": [
    {{
      "task": "",
      "task_id": "",
      "subtasks": [
        {{
          "subtask": "",
          "subtask_id": "",
          "steps": [
            {{
              "step": "",
              "step_id": ""
            }}
          ],
          "traceability": {{
            "document_filename": "",
            "document_title": "",
            "section_or_chapter": ""
          }},
          "confidence": "high | medium | low",
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
