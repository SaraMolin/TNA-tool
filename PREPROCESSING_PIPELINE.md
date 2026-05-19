# Preprocessing Pipeline — Complete Documentation

## Overview

The preprocessing module uses a **fully markdown-based pipeline** to convert PDFs to structured hierarchical sections with breadcrumbs and metadata.

**All processing happens at the markdown level** — no page-based extraction is used in the current implementation.

---

## Active Pipeline (5 Steps)

### Step 1: PDF → Markdown Conversion
**Function:** `pdf_to_markdown()` (in `core/markdown_converter.py`)

- Uses **pymupdf4llm** to convert PDF to markdown format
- Preserves H1-H6 heading structure
- Automatically removes table content using `detect_and_remove_tables()`
- Handles special characters and Swedish text

**Input:** PDF file path
**Output:** Markdown string with tables removed

---

### Step 2: Clean Markdown
**Function:** `clean_markdown()` (in `core/markdown_converter.py`)

- Removes excessive blank lines (max 1 consecutive blank)
- Removes image references (`![...]` patterns)
- Cleans up formatting artifacts

**Input:** Raw markdown from pymupdf4llm
**Output:** Cleaned markdown string

---

### Step 3: Remove Table of Contents
**Function:** `remove_toc_from_markdown()` (in `core/preprocessing.py`)

- Detects "INNEHÅL" (Swedish for contents) or "TABLE OF CONTENTS" headings
- Identifies ToC entry lines (pattern: `text...digits`)
- Removes all ToC entries and front matter (cover pages, preface)
- Also removes all content before the ToC

**Detection Patterns:**
- Lines with 5+ dots followed by digits: `1. HEADING.......................6`
- ToC-style entries: `N.N Text ..... digits`
- Heading markers (####, #####)
- Empty lines within ToC

**Input:** Markdown with potential ToC
**Output:** Markdown starting after ToC, with front matter removed

---

### Step 4: Parse Markdown Structure with Breadcrumbs
**Function:** `parse_markdown_structure()` (in `core/preprocessing.py`)

**Core Functionality:**
1. Detects H1-H5 headers from markdown
2. Maintains header stack to track hierarchy depth
3. Builds breadcrumb trails using "›" separator
4. Filters out warning sections (varning, warning, obs, anm)
5. Generates metadata for each section

**Breadcrumb Examples:**
- `"Kapitel 1"` (H1 only)
- `"Kapitel 1 › Avsnitt 1.1"` (H1 + H2)
- `"Kapitel 1 › Avsnitt 1.1 › Underavsnitt"` (H1 + H2 + H3)

**Warning Sections Filtered:**
- Headers containing "varning", "warning", "warnings", "obs", "varningar"
- These are automatically skipped and not included in output

**Metadata Generated per Section:**
```python
{
    "content": "Text från sektion...",
    "page_number": 5,
    "section_or_chapter": "Kapitel 1 › Avsnitt 1.1",
    "breadcrumb": ["Kapitel 1", "Avsnitt 1.1"],
    "document_filename": "document.pdf",
    "document_title": "Document Title",
    "level": 2
}
```

**Input:** Markdown with ToC removed
**Output:** List of section dictionaries with full metadata

---

### Step 5: Main Entry Point (Orchestration)
**Function:** `preprocess_pdf()` (in `core/preprocessing.py`)

Orchestrates the entire pipeline:

```python
1. Extract document metadata (filename, title)
2. Call pdf_to_markdown()
3. Call clean_markdown()
4. Call remove_toc_from_markdown()
5. Call parse_markdown_structure()
6. Return sections with LLM-compatible metadata
```

**Usage:**
```python
from core.preprocessing import preprocess_pdf

sections = preprocess_pdf("uploads/document.pdf", document_title="My Doc")
# Returns: List[dict] with metadata and content
```

---

## Deprecated Functions

The following functions are **NOT used** in the current markdown pipeline but are kept for backwards compatibility:

| Function | Reason for Deprecation |
|----------|------------------------|
| `extract_text_with_pdfplumber()` | Used only in legacy page-based pipeline |
| `step_1_remove_cover_page()` | Not applicable to markdown |
| `step_2_detect_and_remove_toc()` | Replaced by `remove_toc_from_markdown()` |
| `step_3_remove_headers_footers()` | Not applicable to markdown |
| `step_4_remove_image_regions()` | Not applicable to markdown |
| `step_5_remove_image_captions()` | Handled by pymupdf4llm conversion |
| `step_5b_remove_tables()` | Replaced by `markdown_converter.detect_and_remove_tables()` |
| `step_7_detect_section_boundaries()` | Replaced by `parse_markdown_structure()` |

These functions are page-based (work with pdfplumber page dictionaries) and are **not called** in the active pipeline.

---

## Data Flow Diagram

```
PDF File
   ↓
[Step 1: pdf_to_markdown()]
   → pymupdf4llm conversion
   → detect_and_remove_tables()
   ↓
Markdown (with tables removed)
   ↓
[Step 2: clean_markdown()]
   → Remove excess blank lines
   → Remove image references
   ↓
Cleaned Markdown
   ↓
[Step 3: remove_toc_from_markdown()]
   → Detect "INNEHÅL" heading
   → Remove ToC entries
   → Remove front matter
   ↓
Markdown (ToC removed, actual content only)
   ↓
[Step 4: parse_markdown_structure()]
   → Detect H1-H5 headers
   → Build breadcrumbs with "›" separator
   → Filter warning sections
   → Generate metadata
   ↓
List[Dict] with sections:
  - content
  - page_number
  - section_or_chapter (breadcrumb)
  - breadcrumb (array)
  - document_filename
  - document_title
  - level
```

---

## Adding New Markdown Processing Steps

To add a new markdown processing step to the pipeline:

1. **Create a function** that takes markdown text as input:
   ```python
   def my_markdown_processor(markdown_text: str) -> str:
       """Process markdown and return processed markdown."""
       # Your processing logic
       return processed_markdown
   ```

2. **Add it to `preprocess_pdf()`** in the appropriate sequence:
   ```python
   def preprocess_pdf(pdf_path: str, document_title: str = "") -> List[dict]:
       md_text = pdf_to_markdown(pdf_path)
       md_text = clean_markdown(md_text)
       md_text = remove_toc_from_markdown(md_text)
       md_text = my_markdown_processor(md_text)  # ← ADD HERE
       sections = parse_markdown_structure(md_text, ...)
       return sections
   ```

3. **Do NOT add page-based functions** — the pipeline is fully markdown-based.

---

## Key Design Principles

1. **Markdown-First:** All processing uses markdown representations, not page-based extraction
2. **Non-Destructive:** Original Swedish text is never modified (no lowercasing, lemmatization, stopword removal)
3. **Hierarchical:** Full H1-H5 structure is preserved with breadcrumb trails
4. **Metadata-Rich:** Each section includes filename, title, page number, and heading level
5. **Warning-Filtered:** Informational sections (varning, obs) are automatically excluded
6. **Sequence Matters:** Pipeline steps must be executed in order

---

## Testing the Pipeline

```bash
python -c "
from core.preprocessing import preprocess_pdf

sections = preprocess_pdf('uploads/document.pdf')
print(f'Extracted {len(sections)} sections')
for section in sections[:3]:
    print(f'  - {section[\"section_or_chapter\"]}')
"
```

---

## Common Issues & Solutions

### Issue: ToC not being removed
- **Check:** Does the document have an "INNEHÅL" heading?
- **Check:** Does `remove_toc_from_markdown()` detect the pattern correctly?
- **Solution:** Add debug prints or adjust detection regex patterns

### Issue: Warning sections not filtered
- **Check:** Are warning headings recognized by `is_warning_section()`?
- **Check:** Keywords in `chunking.py`: "varning", "warning", "obs", etc.
- **Solution:** Add new keywords to filter list

### Issue: Breadcrumbs incorrect
- **Check:** Are all heading levels (H1-H5) properly detected?
- **Check:** Is the header stack being updated correctly?
- **Solution:** Verify heading format in markdown output

---

## Performance Notes

- **Typical execution time:** 0.5-2 seconds per PDF (depending on size)
- **Memory usage:** Proportional to markdown size (usually < 5MB per document)
- **Bottleneck:** PDF → markdown conversion (pymupdf4llm)

---

## Version History

- **Current:** Markdown-only pipeline (May 2026)
- **Legacy:** Page-based pipeline with pdfplumber (deprecated)

For questions or issues, refer to the module docstrings in `core/preprocessing.py`.
