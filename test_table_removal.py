#!/usr/bin/env python
"""
Quick test of table removal in markdown conversion.
Usage: python test_table_removal.py <pdf_path>
"""

import sys
from pathlib import Path
from core.preprocessing import preprocess_pdf

def test_table_removal():
    if len(sys.argv) < 2:
        print("Usage: python test_table_removal.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF not found: {pdf_path}")
        sys.exit(1)
    
    print(f"📄 Processing: {pdf_path}")
    print("=" * 70)
    
    try:
        # Preprocess PDF (converts to markdown with table removal)
        sections = preprocess_pdf(pdf_path)
        
        print(f"✓ Successfully processed PDF")
        print(f"✓ Found {len(sections)} sections")
        print()
        
        # Show first 3 sections
        for i, section in enumerate(sections[:3], 1):
            print(f"\n--- Section {i} ---")
            print(f"Title: {section.get('section_or_chapter', 'N/A')}")
            print(f"Page: {section.get('page_number', 'N/A')}")
            print(f"Level: {section.get('level', 'N/A')}")
            print(f"Content preview (first 200 chars):")
            content = section.get('content', '')
            # Check if content contains table indicators
            if '|' in content:
                print("  ⚠️  WARNING: Found | character (table indicator)")
            if 'Tabell' in content or 'Table' in content:
                print("  ⚠️  WARNING: Found table caption keyword")
            print(f"  {content[:200]}...")
            
            # Check for table patterns
            if len(content) < 100 and content.count(' ') > 20:
                print("  ⚠️  WARNING: Very short content with many spaces (possible table row)")
        
        print("\n" + "=" * 70)
        print("✓ Test completed successfully")
        print()
        print("TABLE FILTERING SUMMARY:")
        print(f"  Total sections: {len(sections)}")
        
        # Count sections that might contain table content
        table_warnings = 0
        for section in sections:
            content = section.get('content', '')
            # Only flag if multiple pipes (indicating real table structure, not markdown)
            pipe_count = content.count('|')
            if pipe_count > 1:  # Multiple pipes indicate actual table rows
                table_warnings += 1
        
        if table_warnings > 0:
            print(f"  ⚠️  Sections with actual table content (2+ pipes): {table_warnings}")
        else:
            print(f"  ✓ No table content detected in sections (table filtering successful!)")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_table_removal()
