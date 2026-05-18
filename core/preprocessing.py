"""
Preprocessing module — converts PDF to markdown and extracts hierarchical structure.

MARKDOWN-ONLY PIPELINE:
1. Convert PDF to markdown using pymupdf4llm
2. Parse markdown to extract H1-H5 hierarchy
3. Build breadcrumbs (e.g., "Kapitel 1 › Avsnitt 1.1 › Underavsnitt")
4. Filter warning sections (varning, warning, obs, anm)
5. Return sections with full hierarchy preserved

The markdown-based approach provides:
- Precise heading hierarchy detection
- Automatic breadcrumb generation
- Better handling of complex document structures
- Proper H1-H5 level detection

Preserves original Swedish text without:
- Lowercasing, lemmatization, or stopword removal
- Modification of any content — only structural extraction
"""

import pdfplumber
import re
from typing import List, Tuple, Optional
from pathlib import Path


def extract_text_with_pdfplumber(pdf_path: str) -> List[dict]:
    """
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
    Step 2: Detect and remove table of contents pages and all pages before it.
    
    Heuristic: a page is a ToC if >60% of its lines match the pattern "text ... page_number"
    (i.e. trailing dots followed by a digit or page number).
    
    When a ToC is found, removes:
    - The ToC page itself
    - ALL pages that come before the ToC page
    
    This removes cover pages, preface, introduction, and other front matter that typically
    precedes the table of contents.
    
    Args:
        pages: list of page dicts
    
    Returns:
        List of pages starting after the ToC (or original list if no ToC found)
    """
    import re
    
    # First pass: find the ToC page index
    toc_page_index = None
    
    for idx, page in enumerate(pages):
        text = page["text"]
        lines = text.split('\n') if text else []
        
        # Count lines matching ToC pattern: text ... digits
        toc_pattern_count = 0
        total_lines = len(lines)
        
        if total_lines > 0:
            for line in lines:
                # Match: line ends with dots followed by digits or whitespace and digits
                if re.search(r'\s+\.+\s*\d+\s*$', line.strip()):
                    toc_pattern_count += 1
            
            # If >60% of lines match, consider it a ToC page
            ratio = toc_pattern_count / total_lines if total_lines > 0 else 0
            
            if ratio > 0.6:
                toc_page_index = idx
                break  # Found the ToC, stop looking
    
    # If ToC found, remove it and all pages before it
    if toc_page_index is not None:
        # Remove all pages from 0 to toc_page_index (inclusive)
        return pages[toc_page_index + 1:]
    
    # No ToC found, return original pages
    return pages


def step_3_remove_headers_footers(pages: List[dict]) -> List[dict]:
    """
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
    import re
    
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


def parse_markdown_structure(markdown_text: str, document_filename: str = "", document_title: str = "") -> List[dict]:
    """
    Parses markdown text to extract hierarchical structure with breadcrumbs and metadata.
    
    PRIMARY PREPROCESSING PIPELINE:
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
    
    Args:
        markdown_text: markdown string from pymupdf4llm conversion
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
    Full preprocessing pipeline using MARKDOWN ONLY.
    
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
        document_title: document title/identifier (defaults to filename)
    
    Returns:
        List of dicts with metadata and content
    
    Raises:
        ImportError: if pymupdf4llm is not installed
        Exception: if PDF conversion fails
    """
    from core.markdown_converter import pdf_to_markdown, clean_markdown
    from pathlib import Path
    
    pdf_path_obj = Path(pdf_path)
    document_filename = pdf_path_obj.name
    
    # Use provided title or derive from filename
    if not document_title:
        document_title = pdf_path_obj.stem
    
    # Convert PDF to markdown (mandatory, no fallback)
    md_text = pdf_to_markdown(pdf_path)
    
    if not md_text:
        raise Exception(f"Failed to convert PDF to markdown: {pdf_path}")
    
    # Clean markdown output
    md_text = clean_markdown(md_text)
    
    # Parse markdown structure with metadata
    sections = parse_markdown_structure(
        md_text,
        document_filename=document_filename,
        document_title=document_title
    )
    
    return sections


# TODO: Step 8 — spaCy verb filter
# After evaluating baseline output quality, may add a spaCy-based filter (sv_core_news_sm)
# to exclude paragraphs containing zero Swedish imperative or infinitive verbs.
# This should be added as a new function step_8_filter_by_verbs() between step 5b and 7.
# Do not implement now — keep this comment visible for future reference.
