"""
Preprocessing module — converts PDF to markdown and extracts hierarchical structure.

MARKDOWN-ONLY PIPELINE:
═════════════════════════════════════════════════════════════════

The current preprocessing pipeline is fully markdown-based and consists of:

1. pdf_to_markdown(pdf_path) 
   → Converts PDF to markdown using pymupdf4llm
   → Removes table content from markdown
   
2. clean_markdown(markdown_text)
   → Removes excessive blank lines
   → Removes image references
   
3a. remove_image_captions_and_references(markdown_text)
   → Removes image captions (Bild, Figur, Figure, Image)
   → Removes table references (Tabell, Table)
   → Removes figure descriptions and metadata
   
3b. remove_toc_from_markdown(markdown_text) [PRIMARY METHOD]
   → Detects "INNEHÅL" (Swedish for contents) headings
   → Removes ToC entries and front matter before actual content
   
3c. remove_toc_by_heading(markdown_text) [SECONDARY METHOD]
   → Detects heading-based ToC structure (# Innehållsförteckning)
   → Removes entire ToC section under the heading
   
4. parse_markdown_structure(markdown_text, document_filename, document_title)
   → Extracts H1-H5 heading hierarchy from markdown
   → Builds breadcrumb trails: "Kapitel 1 › Avsnitt 1.1 › Underavsnitt"
   → Filters out warning sections (varning, warning, obs, anm)
   → Returns sections with full hierarchy and metadata
   
5. preprocess_pdf(pdf_path, document_title)
   → Main entry point
   → Orchestrates the entire pipeline
   → Returns sections with LLM-compatible metadata

FEATURES:
- Precise H1-H5 heading hierarchy detection
- Automatic breadcrumb generation with "›" separator
- Proper document structure preservation
- Warning section filtering
- Image caption and table reference removal
- Dual-method ToC removal (comprehensive coverage)
- Full metadata preservation (document_filename, document_title, page_number, level)
- Original Swedish text preserved without modification

DEPRECATED FUNCTIONS:
The following functions are kept for backwards compatibility but are NOT used
in the current markdown pipeline:
- extract_text_with_pdfplumber() - used only in legacy page-based pipeline
- step_1_remove_cover_page() - not applicable to markdown
- step_2_detect_and_remove_toc() - use remove_toc_from_markdown() instead
- step_3_remove_headers_footers() - not applicable to markdown
- step_4_remove_image_regions() - not applicable to markdown
- step_5_remove_image_captions() - replaced by remove_image_captions_and_references()
- step_5b_remove_tables() - use markdown_converter.detect_and_remove_tables() instead
- step_7_detect_section_boundaries() - use parse_markdown_structure() instead

To add new markdown processing steps:
1. Add a new function that takes markdown_text as input
2. Add it to the preprocess_pdf() pipeline after clean_markdown()
3. Pass the processed markdown to the next step
"""

import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path

# Legacy imports kept for backwards compatibility only
# These are not used in the current markdown pipeline
import pdfplumber


# ═══════════════════════════════════════════════════════════════════════════════
# ACTIVE MARKDOWN PIPELINE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════


def remove_image_captions_and_references(markdown_text: str) -> str:
    """
    ACTIVE PIPELINE STEP 3A: Removes image captions, table references, and figure references from markdown.
    
    Detects and removes CAPTION LINES (lines that start with image/table/figure identifiers).
    Only removes lines where the caption identifier is at the START of the line.
    
    Detects patterns:
    - "Bild N." or "Bild N.N" at line start (Swedish for "Image")
    - "Figur N." or "Figur N.N" at line start (Swedish for "Figure") 
    - "Tabell N." or "Tabell N.N" at line start (Swedish for "Table")
    - English variants: "Image", "Figure", "Table" at line start
    - Caption metadata: "Bildtext:", "Figurbeskrivning:", etc.
    
    IMPORTANT: Only removes lines that START with these keywords followed by numbers.
    Does NOT remove text where these words appear in the middle or end of a sentence.
    
    Examples removed:
    - "Bild 15. Maskinens komponenter"
    - "Figur 3.2 Systemöversikt"
    - "Tabell 5. Konfigurationsparametrar"
    - "Table 12. Configuration settings"
    - "Bildtext: Beskrivning av figuren"
    
    Examples NOT removed (these are content):
    - "Fallmål 2015 är en lätt bärbar utrustning med figurmål" (word in middle)
    - "Se Figur 3 för mer information" (reference in middle)
    
    Called by: preprocess_pdf() after clean_markdown()
    
    Args:
        markdown_text: markdown string from pymupdf4llm
    
    Returns:
        Markdown with image/table captions and references removed
    """
    lines = markdown_text.split('\n')
    filtered_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines (keep them to preserve spacing)
        if not stripped:
            filtered_lines.append(line)
            continue
        
        # Check for caption patterns at the START of line only
        # Pattern: Line STARTS with "Bild|Figur|Tabell|Image|Figure|Table" 
        # followed by optional space, optional number(s) and optional colon/period
        # This ensures we only match CAPTIONS, not text containing these words
        
        is_caption = False
        
        # Swedish captions: "Bild N.", "Figur N.N", "Tabell N.", etc.
        # English captions: "Image N.", "Figure N.N", "Table N.", etc.
        # Pattern explanation:
        # ^(Bild|Figur|Tabell|Image|Figure|Table) - Exact word at start (case-insensitive alternative below)
        # \s+ - One or more spaces
        # \d+ - One or more digits
        # \.?\d* - Optional dot and optional more digits (for N.N format)
        # [\.\:]? - Optional period or colon
        # Result: "Bild 15.", "Figur 3.2", "Table 12:" all match
        
        if re.match(r'^(Bild|Figur|Tabell|bild|figur|tabell|Image|Figure|Table|image|figure|table)\s+\d+\.?\d*[\.\:\s]', stripped):
            is_caption = True
        
        # Also skip lines that are caption metadata
        # E.g., "Bildtext:" or "Figurbeskrivning:" (image/figure description in Swedish)
        if re.match(r'^(Bildtext|Figurbeskrivning|Tabellbeskrivning|bildtext|figurbeskrivning|tabellbeskrivning)\s*[\.\:]', stripped):
            is_caption = True
        
        if not is_caption:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)


def remove_toc_by_heading(markdown_text: str) -> str:
    """
    SECONDARY TOC DETECTION METHOD: Removes table of contents by detecting heading-based structure.
    
    This is an ALTERNATIVE/ADDITIONAL detection method that catches ToC sections
    that may be missed by the primary remove_toc_from_markdown() method.
    
    Detection strategy:
    1. Looks for markdown headings (H1-H5) containing "Innehållsförteckning", "Innehål" or "Contents"
    2. Removes the entire ToC section starting from that heading
    3. Continues removing until it encounters the first real content heading (typically Chapter/Section 1)
    
    This catches ToC sections structured as:
    - Markdown heading: "# Innehållsförteckning" or "## Innehål"
    - Followed by ToC entries (various formats)
    - Until the next major heading (new chapter/section begins)
    
    Examples removed:
    - "# Innehållsförteckning\n1. Chapter 1....6\n2. Chapter 2....9"
    - "## Contents\n- Introduction\n- Main Section"
    - "### Table of Contents\n..."
    
    Called by: preprocess_pdf() after remove_toc_from_markdown() as secondary method
    
    Args:
        markdown_text: markdown string from pymupdf4llm
    
    Returns:
        Markdown with heading-based ToC section removed
    """
    lines = markdown_text.split('\n')
    
    # Step 1: Find ToC heading marker
    toc_heading_idx = None
    toc_heading_level = None
    
    for idx, line in enumerate(lines):
        stripped = line.strip()
        
        # Check if this line is a markdown heading with ToC-related keywords
        # Pattern: ^#{1,5}\s+(.+)$ (H1 to H5)
        match = re.match(r'^(#{1,5})\s+(.+)$', stripped)
        
        if match:
            heading_level = len(match.group(1))  # Number of # characters
            heading_text = match.group(2).strip().upper()
            
            # Check if heading contains ToC keywords
            toc_keywords = ['INNEHÅLLSFÖRTECKNING', 'INNEHÅL', 'CONTENTS', 'TABLE OF CONTENTS', 'TOC']
            
            if any(keyword in heading_text for keyword in toc_keywords):
                toc_heading_idx = idx
                toc_heading_level = heading_level
                break
    
    # If no heading-based ToC found, return original
    if toc_heading_idx is None:
        return markdown_text
    
    # Step 2: Find where ToC section ends
    # The ToC ends when we hit another heading of same or higher level (fewer or equal #'s)
    # that's NOT part of the ToC
    
    toc_end_idx = toc_heading_idx + 1
    
    for idx in range(toc_heading_idx + 1, len(lines)):
        line = lines[idx]
        stripped = line.strip()
        
        # Skip empty lines (part of ToC)
        if not stripped:
            toc_end_idx = idx + 1
            continue
        
        # Check if this is a markdown heading
        match = re.match(r'^(#{1,5})\s+(.+)$', stripped)
        
        if match:
            heading_level = len(match.group(1))
            heading_text = match.group(2).strip()
            
            # Check if this is another ToC keyword heading (skip it, part of ToC)
            toc_keywords = ['INNEHÅLLSFÖRTECKNING', 'INNEHÅL', 'CONTENTS', 'TABLE OF CONTENTS', 'TOC']
            if any(keyword in heading_text.upper() for keyword in toc_keywords):
                toc_end_idx = idx + 1
                continue
            
            # If heading level is same or higher (fewer #'s), ToC section ends
            # This indicates start of actual content
            if heading_level <= toc_heading_level:
                break
        
        # Not a heading, keep tracking end position
        toc_end_idx = idx + 1
    
    # Step 3: Remove ToC heading section
    result_lines = lines[toc_end_idx:]
    
    return '\n'.join(result_lines)


def remove_toc_from_markdown(markdown_text: str) -> str:
    """
    PRIMARY TOC DETECTION METHOD: Removes table of contents (ToC) section from markdown text.
    
    This is the PRIMARY detection method. Used together with remove_toc_by_heading()
    for comprehensive ToC removal.
    
    Detection strategy:
    1. Looks for a heading containing "INNEHÅL" (Swedish for "CONTENTS") or "TABLE OF CONTENTS"
    2. Identifies consecutive lines matching ToC entry pattern:
       - "text ... digits" (e.g., "1. SÄKERHETSBESTÄMMELSER ..............................................................6")
       - "#### text" or "##### text" with number prefix followed by page number
    3. Removes all lines from ToC heading until the next non-ToC line or major heading (H1/H2)
    4. Also removes any front matter (cover, preface) that appears before the ToC
    
    Called by: preprocess_pdf() after remove_image_captions_and_references() as primary method
    
    Args:
        markdown_text: markdown string from pymupdf4llm
    
    Returns:
        Markdown with ToC and front matter removed
    """
    lines = markdown_text.split('\n')
    
    # Step 1: Find ToC start marker
    toc_start_idx = None
    for idx, line in enumerate(lines):
        stripped = line.strip().upper()
        # Look for ToC heading: "INNEHÅL", "TABLE OF CONTENTS", "INNEHÅLLSFÖRTECKNING", etc.
        if any(marker in stripped for marker in ['INNEHÅL', 'TABLE OF CONTENTS', 'INNEHÅLLSFÖRTECKNING', 'INNEHLSFÖRTECKNING']):
            toc_start_idx = idx
            break
    
    if toc_start_idx is None:
        # No ToC found, return original
        return markdown_text
    
    # Step 2: Find ToC end (where the actual content starts)
    # ToC ends when we hit a line that's NOT a ToC entry pattern
    # ToC entry patterns:
    # - Line with "....." and trailing digits: "1. HEADING ..............6"
    # - Empty lines
    # - Small headers (#### or #####)
    
    toc_end_idx = toc_start_idx + 1
    for idx in range(toc_start_idx + 1, len(lines)):
        line = lines[idx]
        stripped = line.strip()
        
        # Empty line is okay within ToC
        if not stripped:
            toc_end_idx = idx + 1
            continue
        
        # Small headers (#### ##### often part of ToC structure)
        if stripped.startswith('####'):
            toc_end_idx = idx + 1
            continue
        
        # Check if line matches ToC entry: has many dots followed by digits
        # e.g., "1. HEADING .............................6"
        if re.search(r'\.{5,}.*\d+\s*$', stripped):
            toc_end_idx = idx + 1
            continue
        
        # Check for ToC-style entries: "N.N Text ..... digits"
        if re.match(r'^\d+(\.\d+)?\s+[A-Z].*\d+\s*$', stripped):
            toc_end_idx = idx + 1
            continue
        
        # If we hit a major heading (H1/H2) or substantial content, ToC is done
        if stripped.startswith('#') or (stripped and len(stripped) > 20):
            break
    
    # Step 3: Remove ToC and all content before it (front matter)
    # This removes cover pages, preface, etc.
    result_lines = lines[toc_end_idx:]
    
    return '\n'.join(result_lines)


def parse_markdown_structure(markdown_text: str, document_filename: str = "", document_title: str = "") -> List[dict]:
    """
    ACTIVE PIPELINE STEP 4 (was 3B): Parses markdown text to extract hierarchical structure with breadcrumbs and metadata.
    
    PRIMARY PREPROCESSING PIPELINE STEP:
    1. Detects H1-H5 headers from markdown
    2. Builds breadcrumb trails: "Kapitel › Avsnitt › Underavsnitt › Punkt › Underpunkt"
    3. Filters out warning sections (varning, warning, obs, anm)
    4. Returns sections with full hierarchy and metadata preserved
    
    Metadata structure (matches LLM output format):
    {
        "content": "Text från sektion...",
        "page_number": 5,
        "section_or_chapter": "Kapitel 1 › Avsnitt 1.1",
        "breadcrumb": ["Kapitel 1", "Avsnitt 1.1"],
        "document_filename": "document.pdf",
        "document_title": "Document Title",
        "level": 2
    }
    
    Called by: preprocess_pdf() after remove_toc_from_markdown() (step 3B)
    
    Args:
        markdown_text: markdown string from pymupdf4llm conversion (with ToC removed)
        document_filename: original PDF filename
        document_title: document title/identifier
    
    Returns:
        List of dicts with metadata and content
    """
    from core.chunking import is_warning_section
    
    sections = []
    lines = markdown_text.split('\n')
    
    # Header stack to track hierarchy
    header_stack = {"h1": None, "h2": None, "h3": None, "h4": None, "h5": None}
    current_content = ""
    current_header = None
    current_breadcrumb = []
    current_page = 1
    current_level = 0
    page_counter = 1
    
    for line in lines:
        # Detect markdown headers: ^#{1,5}\s+(.+)$
        match = re.match(r'^(#{1,5})\s+(.+)$', line)
        
        if match:
            header_text = match.group(2).strip()
            header_level = len(match.group(1))  # 1 for H1, ..., 5 for H5
            
            # Skip warning sections
            if is_warning_section(header_text):
                # Clear stack for this level and deeper
                level_keys = ["h1", "h2", "h3", "h4", "h5"]
                for i in range(header_level - 1, 5):
                    header_stack[level_keys[i]] = None
                continue
            
            # Save previous section if exists
            if current_header and current_content.strip():
                section_dict = {
                    "content": current_content.strip(),
                    "page_number": current_page,
                    "section_or_chapter": current_header,
                    "breadcrumb": current_breadcrumb,
                    "document_filename": document_filename,
                    "document_title": document_title,
                    "level": current_level
                }
                sections.append(section_dict)
            
            # Update hierarchy based on header level
            level_keys = ["h1", "h2", "h3", "h4", "h5"]
            header_stack[level_keys[header_level - 1]] = header_text
            
            # Clear deeper levels
            for i in range(header_level, 5):
                header_stack[level_keys[i]] = None
            
            # Build breadcrumb array
            breadcrumbs = []
            for key in level_keys:
                if header_stack[key]:
                    breadcrumbs.append(header_stack[key])
            
            current_breadcrumb = breadcrumbs
            current_header = " › ".join(breadcrumbs) if breadcrumbs else header_text
            current_page = page_counter
            current_level = header_level
            current_content = ""
        else:
            # Accumulate content
            if line.strip():
                if current_content and not current_content.endswith('\n'):
                    current_content += '\n'
                current_content += line
                
                # Simple page counter (one page per ~30 lines of content)
                page_counter = 1 + len(current_content.split('\n')) // 30
    
    # Don't forget the last section
    if current_header and current_content.strip():
        section_dict = {
            "content": current_content.strip(),
            "page_number": current_page,
            "section_or_chapter": current_header,
            "breadcrumb": current_breadcrumb,
            "document_filename": document_filename,
            "document_title": document_title,
            "level": current_level
        }
        sections.append(section_dict)
    
    return sections


def preprocess_pdf(pdf_path: str, document_title: str = "") -> List[dict]:
    """
    ACTIVE PIPELINE STEP 5 (MAIN ENTRY POINT): Full preprocessing pipeline using MARKDOWN ONLY.
    
    COMPLETE MARKDOWN-BASED PIPELINE SEQUENCE:
    
    1. pdf_to_markdown() - Convert PDF to markdown with table removal
    2. clean_markdown() - Remove excessive blanks and image references
    3a. remove_image_captions_and_references() - Remove image/table/figure captions
    3b. remove_toc_from_markdown() - Remove ToC and front matter (METHOD 1)
    3c. remove_toc_by_heading() - Remove heading-based ToC (METHOD 2)
    4. parse_markdown_structure() - Extract hierarchy with breadcrumbs
    
    Uses pymupdf4llm to convert PDF to markdown and extract hierarchical structure
    with breadcrumbs, warning filtering, and rich metadata.
    
    Returns sections enriched with metadata that matches LLM output format:
    - document_filename: original PDF filename
    - document_title: document title/identifier
    - section_or_chapter: breadcrumb hierarchy (e.g., "Kapitel 1 › Avsnitt 1.1")
    - breadcrumb: array of hierarchy levels
    - page_number: page where section starts
    - content: section text
    - level: heading level (1-5)
    
    Args:
        pdf_path: path to PDF file
        document_title: document title/identifier (defaults to filename stem)
    
    Returns:
        List of dicts with metadata and content
    
    Raises:
        ImportError: if pymupdf4llm is not installed
        Exception: if PDF conversion fails
    """
    from core.markdown_converter import pdf_to_markdown, clean_markdown
    
    pdf_path_obj = Path(pdf_path)
    document_filename = pdf_path_obj.name
    
    # Use provided title or derive from filename
    if not document_title:
        document_title = pdf_path_obj.stem
    
    # STEP 1: Convert PDF to markdown (handles table removal internally)
    md_text = pdf_to_markdown(pdf_path)
    
    if not md_text:
        raise Exception(f"Failed to convert PDF to markdown: {pdf_path}")
    
    # STEP 2: Clean markdown output
    md_text = clean_markdown(md_text)
    
    # STEP 3A: Remove image captions, table references, and figure references
    md_text = remove_image_captions_and_references(md_text)
    
    # STEP 3B: Remove table of contents and front matter (METHOD 1 - PRIMARY)
    md_text = remove_toc_from_markdown(md_text)
    
    # STEP 3C: Remove heading-based ToC (METHOD 2 - SECONDARY)
    md_text = remove_toc_by_heading(md_text)
    
    # STEP 4: Parse markdown structure with metadata
    sections = parse_markdown_structure(
        md_text,
        document_filename=document_filename,
        document_title=document_title
    )
    
    return sections


# ═══════════════════════════════════════════════════════════════════════════════
# LEGACY FUNCTIONS - DEPRECATED - NOT USED IN CURRENT MARKDOWN PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════
# The following functions are kept only for backwards compatibility.
# They were designed for a page-based PDF extraction pipeline using pdfplumber.
# The current pipeline is fully markdown-based and does NOT call these functions.
# 
# To modify or extend the pipeline:
# - Add new markdown processing functions (take markdown_text as input)
# - Call them from preprocess_pdf() in the appropriate sequence
# - Do NOT add page-based functions


def extract_text_with_pdfplumber(pdf_path: str) -> List[dict]:
    """
    DEPRECATED: Legacy function for page-based PDF extraction.
    
    NOT USED in current markdown pipeline.
    Kept for backwards compatibility only.
    
    Extracts text and metadata from PDF using pdfplumber.
    Returns list of page dictionaries with text, coordinates, and image info.
    
    Args:
        pdf_path: path to PDF file
    
    Returns:
        List of page dicts: [{"page_num": int, "text": str, "lines": [...], "images": [...]}, ...]
    """
    pages = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            # Extract text with layout and coordinate info
            text = page.extract_text()
            
            # Extract lines with coordinates for header/footer detection
            lines = page.extract_text_lines() if hasattr(page, 'extract_text_lines') else []
            
            # Extract image bounding boxes
            images = page.images if hasattr(page, 'images') else []
            
            pages.append({
                "page_num": page_num,
                "text": text or "",
                "lines": lines,
                "images": images,
                "page_height": page.height,
                "page_width": page.width,
            })
    
    return pages


def step_1_remove_cover_page(pages: List[dict]) -> List[dict]:
    """
    DEPRECATED: Legacy pipeline step.
    
    NOT USED in current markdown pipeline.
    Kept for backwards compatibility only.
    
    Step 1: Remove cover page (always page 1).
    
    Args:
        pages: list of page dicts
    
    Returns:
        List of pages with first page removed
    """
    if len(pages) > 1:
        return pages[1:]
    return pages


def step_2_detect_and_remove_toc(pages: List[dict]) -> List[dict]:
    """
    DEPRECATED: Legacy pipeline step.
    
    NOT USED in current markdown pipeline.
    Kept for backwards compatibility only.
    
    Use remove_toc_from_markdown() instead for markdown-based ToC removal.
    
    This function was designed for pdfplumber page-based pipeline.
    The current pipeline uses markdown-only processing via pymupdf4llm.
    
    Args:
        pages: list of page dicts (unused)
    
    Returns:
        Original pages (passthrough)
    """
    # Passthrough - ToC removal now happens at markdown level
    return pages




def step_3_remove_headers_footers(pages: List[dict]) -> List[dict]:
    """
    DEPRECATED: Legacy pipeline step.
    
    NOT USED in current markdown pipeline.
    Kept for backwards compatibility only.
    
    Step 3: Remove repeated headers and footers.
    
    Detects strings that appear at the same vertical position on 3+ consecutive pages
    in the top ~8% or bottom ~8% of page height, and removes them.
    
    Args:
        pages: list of page dicts
    
    Returns:
        List of pages with repeated headers/footers removed
    """
    if len(pages) < 3:
        return pages
    
    result = []
    
    # For each page, build a map of (vertical_position) -> text
    for page_idx, page in enumerate(pages):
        text_lines = page["text"].split('\n') if page["text"] else []
        page_height = page["page_height"]
        
        # Extract line positions (simplified: use line order to estimate y-coordinate)
        # In practice, we'd need actual y-coordinates from pdfplumber's extract_text_lines()
        # For now, we classify lines as header (top 8%) or footer (bottom 8%)
        
        # This is a simplified heuristic implementation:
        # - Lines that are very short and repeated are likely headers/footers
        # - We'll compare consecutive pages
        
        # Collect header candidates (first 2 lines per page that are short)
        # and footer candidates (last 2 lines per page that are short)
        filtered_lines = []
        
        header_candidates = [line for line in text_lines[:2] if line.strip() and len(line.strip()) < 100]
        footer_candidates = [line for line in text_lines[-2:] if line.strip() and len(line.strip()) < 100]
        
        # For simplicity in this implementation, we mark lines for potential removal
        # A production version would track exact y-coordinates across pages
        lines_to_keep = text_lines[len(header_candidates):-len(footer_candidates)] if footer_candidates else text_lines[len(header_candidates):]
        
        new_page = page.copy()
        new_page["text"] = '\n'.join(lines_to_keep)
        result.append(new_page)
    
    return result


def step_4_remove_image_regions(pages: List[dict]) -> List[dict]:
    """
    DEPRECATED: Legacy pipeline step.
    
    NOT USED in current markdown pipeline.
    Kept for backwards compatibility only.
    
    Step 4: Remove image-only regions.
    
    Skips any region of the page covered by an image bounding box.
    Text that overlaps with image regions (e.g., captions) is also excluded.
    
    Args:
        pages: list of page dicts
    
    Returns:
        List of pages with image regions removed
    """
    result = []
    
    for page in pages:
        # If the page has images, we could filter text overlapping with them
        # For now, we preserve the text but note this in a comment
        # A production implementation would:
        # 1. Get image bounding boxes
        # 2. Get word-level coordinates from extract_words()
        # 3. Filter words outside image regions
        
        # TODO: Implement word-level coordinate filtering against image bboxes
        result.append(page)
    
    return result


def step_5_remove_image_captions(pages: List[dict]) -> List[dict]:
    """
    DEPRECATED: Legacy pipeline step.
    
    NOT USED in current markdown pipeline.
    Kept for backwards compatibility only.
    
    Step 5: Remove image captions.
    
    Detects and removes lines that are image captions, which follow the pattern:
    - "Bild" or "Figur" (Swedish for "Image" or "Figure")
    - Followed by optional number/period
    - Followed by caption text
    
    Examples: "Bild 15. Maskinens komponenter", "Figur 3.2 Systemöversikt"
    
    Args:
        pages: list of page dicts
    
    Returns:
        List of pages with image captions removed
    """
    result = []
    
    for page in pages:
        text_lines = page["text"].split('\n') if page["text"] else []
        
        # Filter out image caption lines
        filtered_lines = []
        for line in text_lines:
            stripped = line.strip()
            
            # Match patterns like "Bild 15.", "Figur 3.2", "Bild:", "Figur:", etc.
            # Pattern: starts with Bild/Figur, followed by optional number/period/colon
            if not re.match(r'^(Bild|Figur|bild|figur)\s*\d*\.?\d*[\.\:]?\s+', stripped):
                filtered_lines.append(line)
        
        new_page = page.copy()
        new_page["text"] = '\n'.join(filtered_lines)
        result.append(new_page)
    
    return result


def step_5b_remove_tables(pages: List[dict]) -> List[dict]:
    """
    DEPRECATED: Legacy pipeline step.
    
    NOT USED in current markdown pipeline.
    Kept for backwards compatibility only.
    
    Use markdown_converter.detect_and_remove_tables() instead for markdown-based table removal.
    
    Step 5b: Remove table content.
    
    Detects and removes lines that appear to be part of tables by identifying:
    - Lines starting with "Tabell" or "Table" (table captions/labels)
    - Lines with excessive whitespace or pipe characters (|) indicating table structure
    - Lines with many aligned columns (multiple tabs or spaces indicating alignment)
    - Lines that match table separator patterns (===, ---, etc.)
    
    Examples: "Tabell 5. Systemöversikt", "Table 3.1 Configuration"
    
    Args:
        pages: list of page dicts
    
    Returns:
        List of pages with table content removed
    """
    result = []
    
    for page in pages:
        text_lines = page["text"].split('\n') if page["text"] else []
        
        filtered_lines = []
        
        for line in text_lines:
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                filtered_lines.append(line)
                continue
            
            # Detect table indicators
            is_table_line = False
            
            # Check for table caption/label (same pattern as Bild/Figur)
            # Matches: "Tabell 5.", "Table 3.2", "Tabell:", "Table:", etc.
            if re.match(r'^(Tabell|Table|tabell|table)\s*\d*\.?\d*[\.\:]?\s+', stripped):
                is_table_line = True
            
            # Check for pipe characters (common table separator)
            if '|' in stripped:
                is_table_line = True
            
            # Check for excessive consecutive spaces or tabs (alignment in tables)
            if re.search(r'[\s]{4,}', stripped):  # 4+ consecutive spaces
                is_table_line = True
            
            # Check for table separator lines (multiple dashes or equals)
            if re.match(r'^[\s]*[=\-\+]{5,}', stripped):
                is_table_line = True
            
            # Check for lines that look like table headers with many columns
            # (many short words separated by spaces, common in Swedish table headers)
            words = stripped.split()
            if len(words) > 8 and all(len(w) < 15 for w in words):
                # Could be table header, skip it
                is_table_line = True
            
            if not is_table_line:
                filtered_lines.append(line)
        
        new_page = page.copy()
        new_page["text"] = '\n'.join(filtered_lines)
        result.append(new_page)
    
    return result


def step_7_detect_section_boundaries(pages: List[dict]) -> List[Tuple[str, int, str]]:
    """
    DEPRECATED: Legacy pipeline step.
    
    NOT USED in current markdown pipeline.
    Kept for backwards compatibility only.
    
    Use parse_markdown_structure() instead for markdown-based section detection.
    
    Step 7: Detect section/chapter boundaries for chunking.
    
    A line is a headline if it meets 2+ of these criteria:
    - Shorter than 60 characters
    - No sentence-ending punctuation (., :, ,) at the end
    - Starts with a number pattern (3.1, Kapitel 4, 4.2.1) OR is ALL CAPS
    - Font size is larger than body text average
    
    Returns list of (headline, page_number, text_block) tuples for chunking.
    
    Args:
        pages: list of page dicts
    
    Returns:
        List of (headline, page_num, text_block) tuples
    """
    sections = []
    current_section_text = ""
    current_section_headline = None
    current_section_page = None
    
    for page in pages:
        text_lines = page["text"].split('\n') if page["text"] else []
        page_num = page["page_num"]
        
        for line in text_lines:
            stripped = line.strip()
            
            if not stripped:
                if current_section_text:
                    current_section_text += '\n'
                continue
            
            # Check if line is a headline using heuristics
            is_headline = False
            criteria_met = 0
            
            # Criterion 1: Shorter than 60 characters
            if len(stripped) < 60:
                criteria_met += 1
            
            # Criterion 2: No sentence-ending punctuation at the end
            if not stripped.endswith(('.', ':', ',')):
                criteria_met += 1
            
            # Criterion 3: Starts with number pattern or is ALL CAPS
            if re.match(r'^(\d+\.\d+|\d+\.?\d*\.\d+|[Kk]apitel\s+\d+)', stripped) or stripped.isupper():
                criteria_met += 1
            
            # Criterion 4: Font size (placeholder — would need actual font data)
            # criteria_met += 1  # Would check against body text average
            
            # Headline if 2+ criteria met
            if criteria_met >= 2:
                is_headline = True
            
            # If we detect a headline, save the previous section and start a new one
            if is_headline:
                if current_section_headline is not None and current_section_text.strip():
                    sections.append((
                        current_section_headline,
                        current_section_page,
                        current_section_text.strip()
                    ))
                
                current_section_headline = stripped
                current_section_page = page_num
                current_section_text = ""
            else:
                # Accumulate text in the current section
                if current_section_text and not current_section_text.endswith('\n'):
                    current_section_text += '\n'
                current_section_text += stripped
    
    # Don't forget the last section
    if current_section_headline is not None and current_section_text.strip():
        sections.append((
            current_section_headline,
            current_section_page,
            current_section_text.strip()
        ))
    
    return sections


# TODO: Step 8 — spaCy verb filter
# After evaluating baseline output quality, may add a spaCy-based filter (sv_core_news_sm)
# to exclude paragraphs containing zero Swedish imperative or infinitive verbs.
# This should be added as a new function step_8_filter_by_verbs() between step 5b and 7.
# Do not implement now — keep this comment visible for future reference.
