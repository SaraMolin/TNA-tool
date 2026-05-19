# Preprocessing Pipeline — Developer Guide

## Quick Start

### Using the Pipeline

```python
from core.preprocessing import preprocess_pdf

# Simple usage
sections = preprocess_pdf("uploads/document.pdf")

# With custom title
sections = preprocess_pdf("uploads/document.pdf", document_title="My Document")

# Result: List of section dicts with this structure:
# [
#   {
#       "content": "...",
#       "page_number": 1,
#       "section_or_chapter": "Kapitel 1 › Avsnitt 1.1",
#       "breadcrumb": ["Kapitel 1", "Avsnitt 1.1"],
#       "document_filename": "document.pdf",
#       "document_title": "My Document",
#       "level": 2
#   },
#   ...
# ]
```

---

## File Structure

```
core/
├── preprocessing.py          ← Main preprocessing module (THIS FILE)
│   ├── ACTIVE FUNCTIONS
│   │   ├── remove_toc_from_markdown()
│   │   ├── parse_markdown_structure()
│   │   └── preprocess_pdf()
│   └── DEPRECATED FUNCTIONS
│       └── Legacy page-based functions (not used)
│
├── markdown_converter.py      ← Markdown utilities
│   ├── pdf_to_markdown()      ← STEP 1
│   ├── clean_markdown()       ← STEP 2
│   └── detect_and_remove_tables()
│
└── chunking.py               ← Chunk saving & metadata
    ├── is_warning_section()   ← Used by parse_markdown_structure()
    └── save_chunks()
```

---

## Understanding the Pipeline

### What Each Step Does

```
INPUT PDF
    ↓
[1] pdf_to_markdown()
    • Uses pymupdf4llm for conversion
    • Handles Swedish characters correctly
    • Removes tables automatically
    ↓
[2] clean_markdown()
    • Removes excessive blank lines
    • Removes image references
    ↓
[3] remove_toc_from_markdown()
    • Detects "INNEHÅL" heading
    • Removes table of contents
    • Removes cover pages and front matter
    ↓
[4] parse_markdown_structure()
    • Extracts H1-H5 hierarchy
    • Builds breadcrumb trails
    • Filters warning sections
    • Generates metadata
    ↓
OUTPUT: List[Dict] with sections
```

---

## Function Reference

### Active Functions

#### `remove_toc_from_markdown(markdown_text: str) -> str`

**Purpose:** STEP 3 - Remove table of contents from markdown

**How It Works:**
1. Searches for "INNEHÅL" (Swedish) or "TABLE OF CONTENTS" heading
2. Identifies ToC entry lines (pattern: `text.......digits`)
3. Removes all ToC content and front matter

**Example:**
```python
from core.preprocessing import remove_toc_from_markdown

md = "...markdown with ToC..."
cleaned = remove_toc_from_markdown(md)
# Returns markdown starting after ToC content
```

**Detection Patterns:** (case-insensitive matching)
- "INNEHÅL" (Swedish)
- "TABLE OF CONTENTS" (English)
- "INNEHÅLLSFÖRTECKNING" (Swedish alternative)
- "INNEHLSFÖRTECKNING" (typo variant)

---

#### `parse_markdown_structure(markdown_text, document_filename, document_title) -> List[dict]`

**Purpose:** STEP 4 - Extract hierarchy and create sections

**Key Features:**
- Detects H1-H5 markdown headers
- Maintains header stack for breadcrumb generation
- Filters warning sections automatically
- Generates complete metadata per section

**Warning Keywords Filtered:**
- "varning" (Swedish warning)
- "warning" / "warnings" (English)
- "obs" (Swedish note)
- "varningar" (Swedish warnings plural)

**Breadcrumb Separator:** `" › "`

**Example Output:**
```python
{
    "content": "Fallmål 2015 är en lätt, bärbar utrustning...",
    "page_number": 1,
    "section_or_chapter": "Kapitel 1 › Avsnitt 1.1 › Underavsnitt",
    "breadcrumb": ["Kapitel 1", "Avsnitt 1.1", "Underavsnitt"],
    "document_filename": "document.pdf",
    "document_title": "My Document",
    "level": 3
}
```

---

#### `preprocess_pdf(pdf_path: str, document_title: str = "") -> List[dict]`

**Purpose:** STEP 5 - Main entry point, orchestrates all steps

**Pipeline Sequence:**
```python
1. Call pdf_to_markdown(pdf_path)
2. Call clean_markdown(md_text)
3. Call remove_toc_from_markdown(md_text)
4. Call parse_markdown_structure(md_text, filename, title)
5. Return sections
```

**Error Handling:**
- Raises `Exception` if PDF conversion fails
- Raises `ImportError` if pymupdf4llm not installed

---

### Deprecated Functions

These functions are **NOT USED** in the current pipeline but are kept for backwards compatibility:

| Function | Legacy Pipeline | Replacement |
|----------|-----------------|-------------|
| `extract_text_with_pdfplumber()` | Page extraction | Not needed (markdown-based) |
| `step_1_remove_cover_page()` | Page-based | Not needed (handled by ToC removal) |
| `step_2_detect_and_remove_toc()` | Page-based detection | `remove_toc_from_markdown()` |
| `step_3_remove_headers_footers()` | Page-based | Not needed |
| `step_4_remove_image_regions()` | Page-based | Not needed |
| `step_5_remove_image_captions()` | Page-based | Handled by conversion |
| `step_5b_remove_tables()` | Page-based | `markdown_converter.detect_and_remove_tables()` |
| `step_7_detect_section_boundaries()` | Page-based | `parse_markdown_structure()` |

**Do NOT use these functions** — they will not be called and their use is deprecated.

---

## Extending the Pipeline

### Adding a New Markdown Processing Step

**Step 1: Create your function**
```python
def my_markdown_filter(markdown_text: str) -> str:
    """
    Custom markdown processing step.
    
    Args:
        markdown_text: markdown input
        
    Returns:
        processed markdown
    """
    lines = markdown_text.split('\n')
    filtered_lines = []
    
    for line in lines:
        # Your processing logic
        if should_keep_line(line):
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)
```

**Step 2: Add to preprocess_pdf()**
```python
def preprocess_pdf(pdf_path: str, document_title: str = "") -> List[dict]:
    from core.markdown_converter import pdf_to_markdown, clean_markdown
    
    pdf_path_obj = Path(pdf_path)
    document_filename = pdf_path_obj.name
    if not document_title:
        document_title = pdf_path_obj.stem
    
    md_text = pdf_to_markdown(pdf_path)
    if not md_text:
        raise Exception(f"Failed to convert PDF: {pdf_path}")
    
    md_text = clean_markdown(md_text)
    md_text = remove_toc_from_markdown(md_text)
    md_text = my_markdown_filter(md_text)  # ← ADD HERE
    
    sections = parse_markdown_structure(md_text, document_filename, document_title)
    return sections
```

**Step 3: Test it**
```bash
python -c "
from core.preprocessing import preprocess_pdf
sections = preprocess_pdf('uploads/test.pdf')
print(f'Sections: {len(sections)}')
"
```

---

## Common Patterns

### Accessing Section Metadata

```python
sections = preprocess_pdf("uploads/document.pdf")

for section in sections:
    # Access metadata
    title = section["section_or_chapter"]        # Full breadcrumb
    breadcrumb = section["breadcrumb"]           # Array of hierarchy
    level = section["level"]                      # H1=1, H2=2, etc.
    page = section["page_number"]                 # Estimated page
    content = section["content"]                  # Section text
    filename = section["document_filename"]      # Original PDF name
    doc_title = section["document_title"]        # Document title
```

### Filtering Sections by Level

```python
sections = preprocess_pdf("uploads/document.pdf")

# Get only level-2 sections (H2 headers)
subsections = [s for s in sections if s["level"] == 2]

# Get top-level sections (H1 headers)
chapters = [s for s in sections if s["level"] == 1]
```

### Building a Table of Contents

```python
sections = preprocess_pdf("uploads/document.pdf")

for i, section in enumerate(sections, 1):
    indent = "  " * (section["level"] - 1)
    print(f"{indent}{i}. {section['section_or_chapter']}")
```

---

## Debugging

### Enable Detailed Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)

from core.preprocessing import preprocess_pdf
sections = preprocess_pdf("uploads/document.pdf")
```

### Check ToC Detection

```python
from core.markdown_converter import pdf_to_markdown, clean_markdown
from core.preprocessing import remove_toc_from_markdown

pdf_path = "uploads/document.pdf"
md = pdf_to_markdown(pdf_path)
md = clean_markdown(md)

print("BEFORE ToC removal:", len(md.split('\n')), "lines")

md = remove_toc_from_markdown(md)

print("AFTER ToC removal:", len(md.split('\n')), "lines")
```

### Verify Metadata Structure

```python
sections = preprocess_pdf("uploads/document.pdf")

if sections:
    sample = sections[0]
    required_keys = [
        "content", "page_number", "section_or_chapter",
        "breadcrumb", "document_filename", "document_title", "level"
    ]
    
    for key in required_keys:
        if key in sample:
            print(f"✓ {key}")
        else:
            print(f"✗ MISSING: {key}")
```

---

## Performance Tips

1. **Cache results** if processing same PDF multiple times
2. **Process in batches** if handling many documents
3. **Monitor memory** for very large PDFs (>100MB)

---

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| ToC not removed | Document uses different heading | Check for alternative "INNEHÅL" variants |
| Missing sections | Warning keyword matches real section | Adjust filter keywords |
| Breadcrumbs incorrect | Heading structure inconsistent | Verify markdown structure |
| ImportError: pymupdf4llm | Library not installed | `pip install pymupdf4llm` |

---

## Related Documentation

- **Main Pipeline:** See `PREPROCESSING_PIPELINE.md`
- **Markdown Converter:** See `core/markdown_converter.py`
- **Chunking:** See `core/chunking.py`
- **Full Codebase:** See individual module docstrings

---

Last Updated: May 2026
Status: Production Ready ✓
