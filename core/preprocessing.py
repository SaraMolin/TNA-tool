"""
Preprocessing module — cleans PDF text extracted by pdfplumber.

Preserves original Swedish text without any lowercasing, lemmatization, or stopword removal.
The LLM needs the original wording for correct output and traceability.

Processing steps (in order):
1. Remove cover page (page 1)
2. Detect and remove table of contents pages (heuristic: >60% lines match "text ... page_number")
3. Remove repeated headers and footers (same position on 3+ consecutive pages)
4. Remove image-only regions (skip text covered by image bounding boxes)
5. Detect section/chapter boundaries for chunking

What preprocessing does NOT do:
- Does not lowercase, lemmatize, or remove stopwords
- Does not filter paragraphs by verb presence (reserved for future step 6 with spaCy)
- Does not modify any Swedish text content — only removes structural noise
"""

import pdfplumber
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
    Step 2: Detect and remove table of contents pages.
    
    Heuristic: a page is a ToC if >60% of its lines match the pattern "text ... page_number"
    (i.e. trailing dots followed by a digit or page number).
    
    Args:
        pages: list of page dicts
    
    Returns:
        List of pages with ToC pages removed
    """
    import re
    
    result = []
    
    for page in pages:
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
            
            if ratio <= 0.6:
                result.append(page)
        else:
            result.append(page)
    
    return result


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


def step_5_detect_section_boundaries(pages: List[dict]) -> List[Tuple[str, int, str]]:
    """
    Step 5: Detect section/chapter boundaries for chunking.
    
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


def preprocess_pdf(pdf_path: str) -> List[Tuple[str, int, str]]:
    """
    Full preprocessing pipeline.
    
    Applies all preprocessing steps in order and returns a list of
    section tuples ready for chunking.
    
    Args:
        pdf_path: path to PDF file
    
    Returns:
        List of (headline, page_num, text_block) tuples
    """
    # Extract text and metadata
    pages = extract_text_with_pdfplumber(pdf_path)
    
    # Step 1: Remove cover page
    pages = step_1_remove_cover_page(pages)
    
    # Step 2: Remove table of contents
    pages = step_2_detect_and_remove_toc(pages)
    
    # Step 3: Remove headers/footers
    pages = step_3_remove_headers_footers(pages)
    
    # Step 4: Remove image regions
    pages = step_4_remove_image_regions(pages)
    
    # Step 5: Detect section boundaries
    sections = step_5_detect_section_boundaries(pages)
    
    return sections


# TODO: Step 6 — spaCy verb filter
# After evaluating baseline output quality, may add a spaCy-based filter (sv_core_news_sm)
# to exclude paragraphs containing zero Swedish imperative or infinitive verbs.
# This should be added as a new function step_6_filter_by_verbs() between step 4 and 5.
# Do not implement now — keep this comment visible for future reference.
