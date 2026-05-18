#!/usr/bin/env python3
"""
Test script for markdown-based preprocessing pipeline.

Tests the new markdown conversion and breadcrumb functionality.

Usage:
    python tests/test_markdown_pipeline.py "uploads/M7786-043381 IBOK FM+àL 2015.pdf"
"""

import sys
from pathlib import Path

# Add project root to path (parent of tests directory)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core import preprocessing
from core import chunking


def test_heading_hierarchy(pdf_path: str):
    """Test that shows all headings in their hierarchy from both pipelines."""
    
    print(f"\n{'='*70}")
    print(f"Testing Heading Hierarchy (Markdown Pipeline)")
    print(f"{'='*70}\n")
    
    print(f"📄 Processing: {pdf_path}\n")
    
    try:
        # Process with markdown pipeline
        sections = preprocessing.preprocess_pdf(pdf_path, use_markdown=True)
        
        print(f"✓ Parsed {len(sections)} sections\n")
        print("Heading Hierarchy:\n")
        
        for i, (headline, page, content) in enumerate(sections, 1):
            # Detect level to show indentation
            level = chunking.detect_heading_level(headline)
            indent = "  " * (level - 1) if level > 0 else ""
            
            # Show hierarchy with indentation
            print(f"{i:3d}. {indent}[Lvl {level}] {headline}")
            print(f"        → Page {page}, Content length: {len(content)} chars")
            print()
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_traditional_hierarchy(pdf_path: str):
    """Test showing headings hierarchy from traditional pipeline."""
    
    print(f"\n{'='*70}")
    print(f"Testing Heading Hierarchy (Traditional Pipeline)")
    print(f"{'='*70}\n")
    
    print(f"📄 Processing: {pdf_path}\n")
    
    try:
        # Process with traditional pipeline
        sections = preprocessing.preprocess_pdf(pdf_path, use_markdown=False)
        
        print(f"✓ Parsed {len(sections)} sections\n")
        print("Heading Hierarchy:\n")
        
        for i, (headline, page, content) in enumerate(sections, 1):
            # Detect level to show indentation
            level = chunking.detect_heading_level(headline)
            indent = "  " * (level - 1) if level > 0 else ""
            
            # Show hierarchy with indentation
            print(f"{i:3d}. {indent}[Lvl {level}] {headline}")
            print(f"        → Page {page}, Content length: {len(content)} chars")
            print()
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_markdown_pipeline(pdf_path: str):
    """Test markdown-based preprocessing."""
    
    print(f"\n{'='*70}")
    print(f"Testing Markdown Pipeline")
    print(f"{'='*70}\n")
    
    # Process with markdown pipeline
    print(f"📄 Processing: {pdf_path}\n")
    
    try:
        sections = preprocessing.preprocess_pdf(pdf_path, use_markdown=True)
        
        print(f"✓ Parsed {len(sections)} sections with markdown pipeline\n")
        
        # Display first 10 sections
        print("Sample sections (with breadcrumbs):\n")
        for i, (headline, page, content) in enumerate(sections[:10], 1):
            print(f"{i}. Breadcrumb: {headline}")
            print(f"   Page: {page}")
            print(f"   Content preview: {content[:80]}...")
            print()
        
        if len(sections) > 10:
            print(f"... and {len(sections) - 10} more sections\n")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_traditional_pipeline(pdf_path: str):
    """Test traditional preprocessing for comparison."""
    
    print(f"\n{'='*70}")
    print(f"Testing Traditional Pipeline (for comparison)")
    print(f"{'='*70}\n")
    
    # Process with traditional pipeline
    print(f"📄 Processing: {pdf_path}\n")
    
    try:
        sections = preprocessing.preprocess_pdf(pdf_path, use_markdown=False)
        
        print(f"✓ Parsed {len(sections)} sections with traditional pipeline\n")
        
        # Display first 10 sections
        print("Sample sections:\n")
        for i, (headline, page, content) in enumerate(sections[:10], 1):
            print(f"{i}. Headline: {headline}")
            print(f"   Page: {page}")
            print(f"   Content preview: {content[:80]}...")
            print()
        
        if len(sections) > 10:
            print(f"... and {len(sections) - 10} more sections\n")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tests/test_markdown_pipeline.py <path/to/pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"❌ File not found: {pdf_path}")
        sys.exit(1)
    
    # Test heading hierarchy from both pipelines
    hierarchy_md = test_heading_hierarchy(pdf_path)
    hierarchy_trad = test_traditional_hierarchy(pdf_path)
    
    # Test both full pipelines
    md_success = test_markdown_pipeline(pdf_path)
    trad_success = test_traditional_pipeline(pdf_path)
    
    if hierarchy_md and hierarchy_trad and md_success and trad_success:
        print(f"\n{'='*70}")
        print("✅ All tests completed successfully!")
        print(f"{'='*70}\n")
        sys.exit(0)
    else:
        print(f"\n{'='*70}")
        print("❌ One or more tests failed")
        print(f"{'='*70}\n")
        sys.exit(1)
