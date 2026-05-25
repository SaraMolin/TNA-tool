# TNA Tool — Training Needs Analysis Automation

En Streamlit-baserad applikation för att automatisera analys av svenska militär- och tekniska PDF-dokument med hjälp av AI.

## Funktioner

- **PDF-uppladdning**: Ladda upp svenska militära dokument (instruktionsböcker, reglementen, handböcker, reparationsböcker)
- **Automatisk bearbetning**: Förbehandling och segmentering av PDF-innehål
- **AI-analys**: Använder Azure AI Foundry för att synthesera en strukturerad uppgifts-hierarki
- **Interaktiv granskning**: Mänsklig recensent kan flagga utgångar för granskning
- **Excel-export**: Ladda ned resultaten som en strukturerad Excel-fil

## Installation

### Förutsättningar

- Python 3.11 eller senare
- macOS (eller Linux/Windows med motsvarande kommandon)

### Setup

1. **Klona eller navigera till projektet:**
```bash
cd /Users/saramolin/Desktop/TNA_app/TNA-tool
```

2. **Skapa en virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Installera dependencies:**
```bash
pip install -r requirements.txt
```

4. **Konfigurera Azure AI Foundry-autentisering:**

Skapa en `.env`-fil i projektets root-mapp (kopiera `.env.example`):
```bash
cp .env.example .env
```

Fyll i dina Azure-uppgifter i `.env`:
```
AZURE_ENDPOINT=https://your-resource.services.ai.azure.com/models
AZURE_API_KEY=your-api-key-here
AZURE_MODEL_NAME=your-model-deployment-name
```

## Körning

Starta Streamlit-appen:
```bash
streamlit run app.py
```

Appen öppnas automatiskt i din webbläsare på `http://localhost:8501`.

## Användning

### 1. Ladda upp dokument
- Klicka på "Välj en PDF-fil" i sidofältet
- Välj dokumenttyp från rullgardinsmeny
- (Valfritt) Ange en custom titel
- Klicka "✅ Bekräfta och ladda upp"

### 2. Kör analys
- Ladda upp ett eller flera dokument
- Klicka på "🚀 Kör analys" i sidofältet
- Vänta på att AI-modellen analyserar innehållet

### 3. Granska resultat
- Visa resultat i den vänstra kolumnen med hierarki för uppgift → deluppgift → steg
- Flagga deluppgifter genom att klicka på 🚩-knappen för granskning
- Visa PDF-filer i höger kolumn

### 4. Exportera resultat
- Klicka på "⬇️ Ladda ner Excel-fil" för att hämta resultaten

## Projektstruktur

```
tna-tool/
├── app.py                          # Streamlit entry point
├── requirements.txt                # Python dependencies
├── .env.example                    # Template för hemliga nycklar
├── .gitignore
│
├── config/
│   └── settings.py                 # Konfiguration från .env
│
├── core/
│   ├── ingestion.py                # PDF-uppladdning och lagring
│   ├── preprocessing.py            # Textrengöring och strukturanalys
│   ├── chunking.py                 # Segmentering av text
│   └── document_registry.py        # Session-state-register för dokument
│
├── llm/
│   ├── client.py                   # Azure AI Foundry-klient
│   ├── classifier.py               # Routing till rätt prompt efter dokumenttyp
│   └── prompts/                    # Prompter för varje dokumenttyp
│       ├── instruktionsbok.py
│       ├── reglemente.py
│       ├── handbok.py
│       └── reparationsbok.py
│
├── ui/
│   ├── sidebar.py                  # Vänster panel (upload, kontroller)
│   ├── pdf_viewer.py               # Höger panel (PDF-visare)
│   └── components/
│       ├── task_table.py           # Hierarki-tabell med färger
│       └── flag_controls.py        # Flaggningsmöjligheter
│
├── export/
│   └── excel_exporter.py           # Excel-generering
│
├── evaluation/
│   ├── sts_evaluator.py            # Semantisk similaritetsutvärdering (STS)
│   └── label_coverage.py           # Täckningsrapport: GT vs chunks vs analys
│
├── goldlabels/
│   └── groundtruth_sts.json        # Manuellt annoterad ground truth för STS
│
├── uploads/                        # (Gitignored) Ursprungliga PDF:er
├── chunks/                         # (Gitignored) Segmenterad text
└── output/                         # (Gitignored) LLM-resultat
```

## Dokumenttyper

| Namn | Kod | Beskrivning |
|---|---|---|
| Instruktionsbok | `instruktionsbok` | Operativ- och instruktionshandböcker |
| Reglemente | `reglemente` | Föreskrifter, doktrin, fälthandböcker |
| Handbok | `handbok` | Referenshandböcker, teoretisk bakgrund |
| Reparationsbok | `reparationsbok` | Underhålls- och reparationsprocedurer |

## API-Schema (JSON-utgång från LLM)

```json
{
  "tasks": [
    {
      "task": "Beskrivning av huvuduppgift",
      "task_id": "01-00-00",
      "subtasks": [
        {
          "subtask": "Beskrivning av deluppgift",
          "subtask_id": "01-01-00",
          "steps": [
            {
              "step": "Beskrivning av steg",
              "step_id": "01-01-01"
            }
          ],
          "traceability": {
            "document_filename": "filnamn.pdf",
            "document_title": "Dokumentets titel",
            "section_or_chapter": "Avsnitt eller kapitel"
          },
          "confidence": "high | medium | low",
          "uncertain": false
        }
      ]
    }
  ]
}
```

## Excel-export

Exporterad Excel-fil innehåller:
- **Column A**: Reference Code (uppgifts-/deluppgifts-/steg-ID)
- **Column B**: Task Title (endast uppgiftsrader)
- **Column C**: Sub Task Title (endast deluppgiftsrader)
- **Column D**: Step Title (endast stegrad)
- **Column E**: Standards/Document Reference (endast deluppgiftsrader)

Rad-färgkodning: blå = uppgifter, grön = deluppgifter, gul = steg

## Utvärdering

Evalueringsverktygen körs från projektets rotkatalog (`TNA-tool/`) efter att en analys har genomförts via appen.

### Förutsättningar

```bash
pip install sentence-transformers matplotlib
```

### STS-utvärdering — semantisk similaritet

Jämför LLM-extraherade subtasks mot manuellt annoterad ground truth (`goldlabels/groundtruth_sts.json`) med cosine similarity via sentence-transformer-embeddings.

**Kräver:** `output/latest_analysis.json` och `goldlabels/groundtruth_sts.json`

```bash
python -m evaluation.sts_evaluator
```

Skriver ut en tabell med similaritetspoäng per subtask och sparar resultatet till `output/sts_results.json`.

### Label Coverage — täckningsrapport

Jämför vilka sektioner som finns i ground truth, i chunks och i analysresultatet — allt filtrerat till samma avsnitt som senaste analysen täckte. Synliggör täckningsgap och namnkonventionsskillnader.

**Kräver:** `output/latest_analysis.json`, `output/sts_results.json` och `goldlabels/groundtruth_sts.json`

```bash
python -m evaluation.label_coverage
```

Skriver ut en 4-kolumnstabell i terminalen och sparar en PNG-plot till `output/label_coverage.png`.

| Kolumn | Innehåll |
|--------|----------|
| GT section_or_chapter | Sektioner från ground truth i analysens scope |
| Chunk section_or_chapter | Sektioner från chunks.json som skickades till LLM |
| analysis_section | Rubrik som LLM-analysen hänvisar till |
| gt_section | Matchad GT-rubrik med similaritetspoäng |

---

## Framtida utveckling

- [ ] Stöd för blandade dokumenttyper i en enda analys
- [ ] SpaCy-baserad verbfiltrering för att förbättra kvantifiering
- [ ] Utökad PDF-extraktion med OCR för skannade dokument
- [ ] Databaskoppla för resultathistorik

## Problemlösning

### "Missing required environment variables"
Kontrollera att `.env`-filen är korrekt konfigurerad med alla Azure-uppgifter.

### "Error parsing LLM response as JSON"
Azure-modellen returnerade inte giltigt JSON. Kontrollera promptmallarna i `llm/prompts/`.

### PDF-visare visar inte innehål
Kontrollera att PDF-filen är korrekt uppladdat i `uploads/`-mappen.

## Licens

Internt projekt — ej licensierat för externa användare.

## Support

Kontakta utvecklingsteamet för frågor.
