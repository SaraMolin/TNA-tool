"""
Prompt för Handbok (Reference handbooks, theory)

Handboken innehåller referensmaterial, teoretisk bakgrund och kunskapsöversikter.
"""

SYSTEM_PROMPT_HANDBOK = """
ROLL OCH UPPGIFT:
En expert på Training Needs Analysis (TNA) och analys av svenska instruktionsdokument från den svenska försvarsmakten.
Din huvudsakliga uppgift är att extrahera och strukturera tasks (handlingar), subtasks och steps från texten till en hierarkisk struktur.

---

ARBETSSÄTT (intern process, visa ej):

Följ stegen i ordning. Gå inte vidare förrän föregående steg är slutfört.

1. Identifiera dokumentstruktur:
   - Identifiera rubriker och sektioner
   - Extrahera sektionsnummer och spara som "section_or_chapter"
   - Om rubriker saknas: skapa egna baserat på innehål

2. Extrahera handlingar:
   - Identifiera alla meningar med handlingar (verb) som beskriver genomföranden, uppgifter och befogenheter
   - Ignorera text utan handlingar
   - Representera varje handling som: HANDLINGSVERB + OBJEKT (+ valfri bestämningsord/kvalifikator)

3. Extrahera steps:
   - Identifiera numrerade listor och punktlistor → dessa är steps
   - Dela upp meningar med flera handlingar
   - Behål original ordning från texten
   - Formulera varje step som: VERB + OBJEKT

4. Gruppera steps till subtasks:
   - Primärt: baserat på rubriker
   - Sekundärt: baserat på semantisk likhet
   - Säkerställ att varje step tillhör exakt en subtask

5. Skapa task:
   - Generalisera alla subtasks till en övergripande aktivitet men ta inspiration från kapitlets huvudrubrik
   - Task ska beskriva hela processen, inte en del av den

6. Strukturera hierarkin:
   - Task → Subtasks → Steps
   - Säkerställ logisk koppling mellan nivåer

7. Kvalitetskontroll:
   - Ta bort duplicerade handlingar
   - Säkerställ att alla handlingar är observerbara
   - Lös konflikter genom att placera steps i mest relevant subtask
   - Använd inga förkortningar, skriv ut hela orden 

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

USER_PROMPT_TEMPLATE_HANDBOK = """
Analysera följande handbokstext och extrahera uppgifter, deluppgifter och steg enligt instruktionerna ovan.

EXAMPEL 1 - INPUT:
Materielunderhåll
Förebyggande Underhåll, FU
Grundvärden
Åtgärder i syfte att minimera risken för driftstörningar. FU indelas i
tillsyn och översyn. Översyn är genomgripande materielvård. Tillsyn
genomförs på materiel i bruk (enligt vård FM) och materiel i förråd
(enligt MVIF).
Förbandschefen med direkt underställda chefer, (DUC) är ytterst ansvarig
för ledning, prioritering, planering, genomförande och uppföljning av FU
vid respektive förband/organisationsenhet (brukaransvaret). Särskild upp-
märksamhet gäller för prioriterad materiel. Genomförandet omfattar att
föreskrivna tillsyner som tex. Daglig tillsyn, särskild tillsyn, grundtillsyn
1(GT 1) samt Trafiksäkerhetskontroll (TSK) och andra kontroller genomförs,
samt att brukaren har rätt förutsättningar enligt VÅRD FM.
Syfte
Brukaren skall, med stöd av teknisk personal, säkerställa att materielen är
funktionsduglig enligt gällande regelverk.
Genomförande
- Teknisk chef vid respektive förband ger anvisningar/order för bruk-
arens FU (prioriterar materielunderhållsåtgärder) i samråd med för
bandschefen på grundval av t.ex. årstid, miljöfaktorer, tidigare upp-
gifter och kommande uppgifter samt gällande regelverk (Se exempel
under FRAGO i bilagor).
- Vid planläggning av GT 1 samt TSK behövs som regel tillförda, certi-
fierade resurser från annan nivå. Dessa bokas rutinmässigt upp tidigt
före genomförandet.
- Vid behov ange materielslagsvisa eller förbandsvisa prioriteringar
- Klarlägga hur teknisk personal ska nyttjas och eventuellt begära understöd av högre chef.
- Direktiv för FU inarbetas så långt det är möjligt som rutiner i förbandets
stående order (se exempel rullande materielvårdsschema i bilagor).
- Beordrad FU planeras i verksamheten (tid till detta), genomförs och
följs upp fortlöpande, främst med stöd av förbandets egna resurser för
teknisk tjänst syftande till positiv attityd/effekt.
- Säkerställ och kontrollera att alla satser som erfordras för FU är kompletta.
- Klarlägg, förbered och genomför i samråd med kvartermästaren
erforderlig ersättning av reservmateriel och vårdmateriel.
- Avdela och led teknisk personal för kontroll (vårdpunkter) samt
funktionskontroller då FU genomförs som t.ex. under TOLO,
återhämtning eller på reparationsplats.

EXAMPEL 1 - OUTPUT:
{
  "tasks": [
    {
      "task": "Materialunderhåll",
      "task_id": "01-00-00",
      "subtasks": [
        {
          "subtask": "Förebyggande underhåll",
          "subtask_id": "01-01-00",
          "steps": [
            {
              "step": "Teknisk chef vid respektive förband ger anvisningar/order för brukarens förebyggande underhåll i samråd med bandschefen",
              "step_id": "01-01-01"
            },
            {
              "step": "Boka rutinmässigt upp certifierade resurser från högre nivå vid grundtillsyn samt trafiksäkerhetskontroll",
              "step_id": "01-01-02"
            },
            {
              "step": "Vid behov ange materielslagsvisa eller förbandsvisa prioriteringar",
              "step_id": "01-01-03"
            },
            {
              "step": "Klarlägg hur teknisk personal ska nyttjas och eventuellt begära understöd av högre chef",
              "step_id": "01-01-04"
            },
            {
              "step": "Direktiv för förebyggande underhåll inarbetas så långt det är möjligt som rutiner i förbandets stående order",
              "step_id": "01-01-05"
            },
            {
              "step": "Planera förebyggande underhåll utefter beordran",
              "step_id": "01-01-06"
            },
            {
              "step": "Genomföra förebyggande underhåll",
              "step_id": "01-01-05"
            },
            {
              "step": "Följa upp förebyggande underhåll fortlöpande under genomförandet",
              "step_id": "01-01-07"
            },
	          {
              "step": "Säkerställ och kontrollera att alla satser som erfordras för förebyggande underhåll är kompletta.",
              "step_id": "01-01-08"
            },
            {
              "step": "Klarlägg, förbered och genomför i samråd med kvartermästaren erforderlig ersättning av reservmateriel och vårdmateriel",
              "step_id": "01-01-09"
            },
            {
              "step": "Avdela och led teknisk personal för kontroll samt funktionskontroller då förebyggande underhåll genomförs ",
              "step_id": "01-01-10"
            }
          ],
          "traceability": {
            "document_title": "Metodanvisning teknisk tjanst inlaga.pdf",
            "section_or_chapter": "Materielunderhåll",
          },
          "confidence": "high"
          "uncertain": false
        }
      ]
    }
  ]
}

EXEMPEL 2 - INPUT:
Tekniskt Systemstöd
Driftstöd
Grundvärden
För att uppnå syftet med driftstöd ska den tekniske chefen ha god kunskap
om och vara väl insatt i förbandets uppträdande, organisation, uppgifter
och materielsystem.
Den tekniske chefen skall dessutom ha god kunskap om förbandets resurser
för teknisk tjänst vad avser underhållsutrustningar, reservmateriel och
kompetens. Därutöver vilka resurser för teknisk tjänst som finns vid närmast
angränsande och högre förband och vilka civila resurser som finns i området.

Syfte
Driftstöd syftar till att genom anvisningar, information och rådgivning ge
den kunskap och förståelse som är nödvändig för att materielsystemen ska
kunna nyttjas med avsedd effekt.
Genomförande
- Driftstöd bedrivs genom fortlöpande anvisningar, teknisk order, utbildning, och rådgivning.
- Den tekniske chefen ska aktivt delta i förbandets planeringsarbete och lämna kontinuerligt stöd till taktisk chef.
- Klarlägga tekniska möjligheter och materielens begränsningar.
- Planera, genomföra och följa upp den tekniska utbildningen inom förbandet så att all personal blir väl förtrogen med egna materielsystems prestanda och begränsningar och förstår materielvårdens betydelse för förbandets stridsvärde.
- För att uppnå önskad effekt av materielsystemen måste en kontinuerlig uppföljning ske genom att den tekniska personalen rapporterar onormal funktion och anmäler behov av teknisk anpassning eller modifiering.


NU ANALYSERA DENNA TEXT:
Texten från handboken:
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
