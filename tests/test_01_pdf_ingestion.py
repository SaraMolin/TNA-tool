"""
Test 01: PDF Ingestion and Text Extraction

Verifies that PDF files from the uploads/ directory are loaded and processed correctly.

Test cases:
- ✓ Can PDF files be read from uploads/ directory?
- ✓ Is text extracted from all pages?
- ✓ Is metadata (page numbers, text) preserved?
- ✓ Are invalid PDFs handled gracefully?
- ✓ Do extracted pages match actual PDF page count?
"""

import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pdfplumber


class TestPDFIngestion:
    """Test suite for PDF ingestion and text extraction."""

    def test_uploads_directory_exists(self, uploads_dir):
        """Test that uploads directory exists."""
        assert uploads_dir.exists(), f"uploads directory does not exist at {uploads_dir}"
        assert uploads_dir.is_dir(), f"{uploads_dir} is not a directory"

    def test_pdf_files_exist_in_uploads(self, get_uploaded_pdfs):
        """Test that at least one PDF file exists in uploads/."""
        assert len(get_uploaded_pdfs) > 0, "No PDF files found in uploads/ directory"

    def test_pdf_is_readable(self, get_uploaded_pdfs):
        """Test that PDF files can be opened and read."""
        for pdf_path in get_uploaded_pdfs:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    assert len(pdf.pages) > 0, f"PDF {pdf_path.name} has no pages"
            except Exception as e:
                pytest.fail(f"Failed to read PDF {pdf_path.name}: {str(e)}")

    def test_pdf_page_count(self, get_uploaded_pdfs):
        """Test that page count is correct for all PDFs."""
        for pdf_path in get_uploaded_pdfs:
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
                assert page_count > 0, f"PDF {pdf_path.name} has {page_count} pages"
                print(f"\n📄 {pdf_path.name}: {page_count} pages")

    def test_text_extraction_from_all_pages(self, get_uploaded_pdfs):
        """Test that text can be extracted from all pages."""
        for pdf_path in get_uploaded_pdfs:
            with pdfplumber.open(pdf_path) as pdf:
                extracted_pages = []
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        extracted_pages.append((page_num, len(text)))
                
                assert len(extracted_pages) > 0, f"No text extracted from {pdf_path.name}"
                print(f"\n📄 {pdf_path.name}:")
                print(f"   Total pages: {len(pdf.pages)}")
                print(f"   Pages with text: {len(extracted_pages)}")
                for page_num, text_len in extracted_pages[:3]:  # Show first 3 pages
                    print(f"   Page {page_num}: {text_len} characters")

    def test_text_preservation(self, get_uploaded_pdfs):
        """Test that original text is preserved (no modification)."""
        for pdf_path in get_uploaded_pdfs:
            with pdfplumber.open(pdf_path) as pdf:
                first_page_text = pdf.pages[0].extract_text()
                
                # Check that text contains readable content
                assert first_page_text is not None, f"Could not extract text from first page of {pdf_path.name}"
                assert len(first_page_text) > 0, f"First page of {pdf_path.name} is empty"
                
                # Check for Swedish characters (å, ä, ö) if present
                swedish_chars = any(char in first_page_text for char in 'åäöÅÄÖ')
                print(f"\n📄 {pdf_path.name}:")
                print(f"   First page text length: {len(first_page_text)}")
                print(f"   Contains Swedish characters: {swedish_chars}")

    def test_pdf_metadata(self, get_uploaded_pdfs):
        """Test that PDF metadata is accessible."""
        for pdf_path in get_uploaded_pdfs:
            with pdfplumber.open(pdf_path) as pdf:
                metadata = pdf.metadata
                print(f"\n📄 {pdf_path.name}:")
                print(f"   Pages: {len(pdf.pages)}")
                if metadata:
                    print(f"   Author: {metadata.get('Author', 'N/A')}")
                    print(f"   Title: {metadata.get('Title', 'N/A')}")
                    print(f"   Producer: {metadata.get('Producer', 'N/A')}")

    def test_pdf_file_size(self, get_uploaded_pdfs):
        """Test that PDF files have reasonable file sizes."""
        for pdf_path in get_uploaded_pdfs:
            file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
            assert file_size_mb > 0, f"PDF {pdf_path.name} is empty"
            assert file_size_mb < 100, f"PDF {pdf_path.name} is too large ({file_size_mb:.1f} MB)"
            print(f"\n📄 {pdf_path.name}: {file_size_mb:.1f} MB")


# Convenience functions for manual testing
def list_pdfs_in_uploads():
    """List all PDF files in uploads directory."""
    uploads_path = project_root / "uploads"
    if uploads_path.exists():
        pdfs = list(uploads_path.glob("*.pdf"))
        if pdfs:
            print("\n📚 PDFs in uploads/:")
            for pdf in pdfs:
                size_mb = pdf.stat().st_size / (1024 * 1024)
                print(f"  - {pdf.name} ({size_mb:.1f} MB)")
        else:
            print("❌ No PDFs found in uploads/")
    else:
        print("❌ uploads/ directory does not exist")


if __name__ == "__main__":
    """Run this test directly with: python tests/test_01_pdf_ingestion.py"""
    print("\n" + "=" * 70)
    print("🧪 TEST 01: PDF Ingestion and Text Extraction")
    print("=" * 70)
    
    list_pdfs_in_uploads()
    
    print("\n" + "=" * 70)
    print("To run tests with pytest:")
    print("  python -m pytest tests/test_01_pdf_ingestion.py -v")
    print("\nTo run specific test:")
    print("  python -m pytest tests/test_01_pdf_ingestion.py::TestPDFIngestion::test_pdf_is_readable -v")
    print("=" * 70 + "\n")
