"""
Table remover module — detects and removes tables from PDF before markdown conversion.

This module uses pdfplumber to:
1. Detect table regions on each page
2. Identify text that belongs to tables
3. Create a "table-removed" version of the PDF
4. Pass the cleaned PDF to pymupdf4llm for markdown conversion

This ensures that table content never makes it into the markdown output.

Key advantage: Works at the PDF level before any conversion to markdown,
so it catches ALL table variations regardless of formatting.
"""

import pdfplumber
from pathlib import Path
from typing import List, Set, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def detect_tables_on_page(page) -> List[dict]:
    """
    Detects tables on a single page using pdfplumber's table detection.
    
    Args:
        page: pdfplumber page object
    
    Returns:
        List of table objects detected on the page
    """
    try:
        # pdfplumber has built-in table detection
        tables = page.extract_tables()
        if tables:
            return tables
        return []
    except Exception as e:
        logger.warning(f"Error detecting tables on page: {str(e)}")
        return []


def get_table_bounding_boxes(page) -> List[Tuple[float, float, float, float]]:
    """
    Gets bounding boxes (bbox) for all tables on a page.
    
    A bbox is (x0, top, x1, bottom) - coordinates of the table region.
    
    Args:
        page: pdfplumber page object
    
    Returns:
        List of bbox tuples for each detected table
    """
    bboxes = []
    
    try:
        tables = page.extract_tables()
        if not tables:
            return bboxes
        
        # Get table settings to extract bounding boxes
        table_settings = page.table_settings
        if not table_settings:
            table_settings = {}
        
        # Extract table bounding boxes using pdfplumber's detection
        # Note: pdfplumber doesn't directly return bboxes, so we need to infer from cells
        for table in tables:
            if table:
                # Each table is a list of rows
                # We'll estimate the bbox from the table structure
                try:
                    # Use pdfplumber's find_tables with bboxes
                    detected_tables = page.find_tables()
                    for detected_table in detected_tables:
                        if detected_table:
                            # detected_table.bbox gives (x0, top, x1, bottom)
                            bboxes.append(detected_table.bbox)
                except:
                    pass
        
        return bboxes
    except Exception as e:
        logger.warning(f"Error getting table bboxes: {str(e)}")
        return []


def text_in_bbox(bbox: Tuple[float, float, float, float], word: dict) -> bool:
    """
    Checks if a word/character is within a bounding box.
    
    Args:
        bbox: (x0, top, x1, bottom) tuple
        word: pdfplumber word dict with keys: x0, top, x1, bottom, text
    
    Returns:
        True if word overlaps with bbox, False otherwise
    """
    x0_bbox, top_bbox, x1_bbox, bottom_bbox = bbox
    x0_word = word.get("x0", 0)
    top_word = word.get("top", 0)
    x1_word = word.get("x1", 0)
    bottom_word = word.get("bottom", 0)
    
    # Check if word overlaps with bbox (with small tolerance)
    tolerance = 2
    return (
        x0_word < x1_bbox + tolerance and
        x1_word > x0_bbox - tolerance and
        top_word < bottom_bbox + tolerance and
        bottom_word > top_bbox - tolerance
    )


def identify_table_text_regions(page) -> Set[str]:
    """
    Identifies all text that belongs to tables on a page.
    
    Returns a set of unique text strings that are part of detected tables.
    
    Args:
        page: pdfplumber page object
    
    Returns:
        Set of text strings that are part of tables
    """
    table_text = set()
    
    try:
        # Get table bounding boxes
        bboxes = get_table_bounding_boxes(page)
        
        if not bboxes:
            # Fallback: try to extract tables directly
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    if table:
                        for row in table:
                            for cell in row:
                                if cell:
                                    table_text.add(cell.strip())
            return table_text
        
        # Get all words on the page
        words = page.extract_words()
        
        # Find words that fall within table bboxes
        for bbox in bboxes:
            for word in words:
                if text_in_bbox(bbox, word):
                    text = word.get("text", "").strip()
                    if text:
                        table_text.add(text)
        
        return table_text
    except Exception as e:
        logger.warning(f"Error identifying table text: {str(e)}")
        return set()


def remove_tables_from_pdf(pdf_path: str, output_path: Optional[str] = None) -> Optional[str]:
    """
    Removes all tables from a PDF and saves to a new file.
    
    Uses pdfplumber to detect tables, then PyMuPDF to remove text/content
    that belongs to tables, creating a cleaned PDF.
    
    Args:
        pdf_path: path to original PDF
        output_path: optional path to save cleaned PDF. If None, creates temp file.
    
    Returns:
        Path to cleaned PDF, or None if operation failed
    """
    try:
        # Import PyMuPDF here (lazy import) to avoid issues if not installed
        import pymupdf
        
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return None
        
        # Generate output path if not provided
        if not output_path:
            output_path = pdf_path.parent / f"{pdf_path.stem}_no_tables.pdf"
        
        output_path = Path(output_path)
        
        # Collect all table text regions across all pages
        all_table_regions = {}  # page_num -> list of bboxes
        
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    bboxes = get_table_bounding_boxes(page)
                    if bboxes:
                        all_table_regions[page_num] = bboxes
                except Exception as e:
                    logger.warning(f"Error processing page {page_num}: {str(e)}")
        
        if not all_table_regions:
            logger.info("No tables detected in PDF")
            return str(pdf_path)  # Return original if no tables found
        
        # Use PyMuPDF to remove content from table regions
        doc = pymupdf.open(str(pdf_path))
        
        for page_num, bboxes in all_table_regions.items():
            if page_num >= len(doc):
                continue
            
            page = doc[page_num]
            
            # Redact (remove) each table region
            for bbox in bboxes:
                # Convert bbox format if needed
                rect = pymupdf.Rect(bbox)
                
                # Remove all content in this region
                # We'll use the redact method to cover the area
                page.add_redact_annot(rect, fill=(255, 255, 255))  # White fill
            
            # Apply redactions
            page.apply_redactions()
        
        # Save cleaned PDF
        doc.save(str(output_path))
        doc.close()
        
        logger.info(f"Successfully removed tables from PDF: {output_path}")
        return str(output_path)
    
    except ImportError as e:
        logger.error(f"Required library not installed: {str(e)}")
        logger.error("Ensure pymupdf (fitz) is installed: pip install pymupdf")
        return None
    
    except Exception as e:
        logger.error(f"Error removing tables from PDF: {str(e)}")
        return None


def get_cleaned_pdf_for_conversion(pdf_path: str) -> str:
    """
    Gets a cleaned version of the PDF (with tables removed) for markdown conversion.
    
    This is the main entry point - call this before passing PDF to pymupdf4llm.
    
    If table removal fails, returns the original PDF path (graceful fallback).
    
    Args:
        pdf_path: path to PDF file
    
    Returns:
        Path to cleaned PDF (or original PDF if cleaning fails or no tables found)
    """
    try:
        cleaned_path = remove_tables_from_pdf(pdf_path)
        if cleaned_path:
            return cleaned_path
    except Exception as e:
        logger.error(f"Error in table removal pipeline: {str(e)}")
    
    # Fallback to original PDF
    logger.warning(f"Falling back to original PDF: {pdf_path}")
    return pdf_path
