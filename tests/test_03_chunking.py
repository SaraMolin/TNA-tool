"""
Test 03: Chunking - Document Sectioning and File Generation

Verifies that preprocessed text is correctly divided into chunks and saved as files.

Test cases:
- ✓ Chunk files created for all sections?
- ✓ Metadata present in each chunk (Rubrik, Sida, innehål)?
- ✓ Chunk filenames valid and readable?
- ✓ Number of chunks matches identified section count?
- ✓ Chunk content is substantial (not empty)?
- ✓ Chunks saved in correct directory structure?
- ✓ Each chunk is unique (no duplicates)?
"""

import pytest
from pathlib import Path
import sys
import hashlib

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core import chunking


class TestChunking:
    """Test suite for document chunking and sectioning."""

    def test_chunking_module_imports(self):
        """Test that chunking module can be imported."""
        assert chunking is not None
        assert hasattr(chunking, 'save_chunks')
        assert hasattr(chunking, 'load_chunks')
        assert hasattr(chunking, 'remove_chunks')
        assert hasattr(chunking, 'sanitize_filename')

    def test_sanitize_filename(self):
        """Test that filename sanitization works correctly."""
        # Test basic sanitization
        result = chunking.sanitize_filename("Introduktion till systemet")
        assert result == "Introduktion_till_systemet.txt"
        
        # Test with invalid characters
        result = chunking.sanitize_filename('Invalid <chars> "here"')
        assert all(char not in result for char in '<>":"/\\|?*')
        
        # Test with max length truncation
        long_text = "A" * 150
        result = chunking.sanitize_filename(long_text)
        assert len(result) <= 104  # 100 max + .txt
        
        # Test empty/whitespace only
        result = chunking.sanitize_filename("   ")
        assert result == ".txt"

    def test_chunk_files_creation(self):
        """Test that chunk files are created for all sections."""
        # Test data: (headline, page_num, text_block)
        test_document = "test_doc_creation"
        sections = [
            ("Introduktion", 1, "Detta är introduktionen till dokumentet."),
            ("Kapitel 1", 2, "Detta är första kapitlet med innehål."),
            ("Kapitel 2", 5, "Detta är andra kapitlet med mer innehål."),
        ]
        
        # Save chunks
        saved_files = chunking.save_chunks(test_document, sections)
        
        # Verify files were created
        assert len(saved_files) == len(sections), f"Expected {len(sections)} files, got {len(saved_files)}"
        assert len(saved_files) == 3
        
        # Verify files exist on disk
        doc_chunks_dir = chunking.CHUNKS_DIR / test_document
        for filename in saved_files:
            file_path = doc_chunks_dir / filename
            assert file_path.exists(), f"File {filename} was not created"
        
        # Cleanup
        chunking.remove_chunks(test_document)

    def test_chunk_metadata_presence(self):
        """Test that metadata is present in each chunk."""
        test_document = "test_doc_metadata"
        sections = [
            ("Avsnitt 1", 10, "Innehål för avsnitt ett."),
            ("Avsnitt 2", 15, "Innehål för avsnitt två."),
        ]
        
        # Save chunks
        chunking.save_chunks(test_document, sections)
        
        # Load and verify metadata
        chunks = chunking.load_chunks(test_document)
        assert len(chunks) == 2
        
        for idx, (filename, content) in enumerate(chunks):
            headline = sections[idx][0]
            page_num = sections[idx][1]
            
            # Check for metadata
            assert "Rubrik:" in content, f"Missing 'Rubrik:' in {filename}"
            assert headline in content, f"Headline '{headline}' not in {filename}"
            assert "Sida:" in content, f"Missing 'Sida:' in {filename}"
            assert str(page_num) in content, f"Page number {page_num} not in {filename}"
            assert "=" * 60 in content, f"Missing separator line in {filename}"
        
        # Cleanup
        chunking.remove_chunks(test_document)

    def test_chunk_filenames_validity(self):
        """Test that chunk filenames are valid and readable."""
        test_document = "test_doc_filenames"
        sections = [
            ("Introduktion & Start", 1, "Text"),
            ('File <with> "special" chars?', 2, "Text"),
            ("Normal Filename", 3, "Text"),
        ]
        
        saved_files = chunking.save_chunks(test_document, sections)
        
        # Verify all filenames are valid
        for filename in saved_files:
            assert filename.endswith('.txt'), f"Filename {filename} doesn't end with .txt"
            assert len(filename) > 0, "Filename is empty"
            # Check no invalid filesystem characters remain
            invalid_chars = '<>:"/\\|?*'
            assert not any(char in filename for char in invalid_chars), \
                f"Invalid characters found in {filename}"
        
        # Cleanup
        chunking.remove_chunks(test_document)

    def test_chunk_count_matches_sections(self):
        """Test that chunk count matches identified section count."""
        test_document = "test_doc_count"
        test_cases = [
            (1, "Single section"),
            (3, "Three sections"),
            (10, "Many sections"),
        ]
        
        for num_sections, description in test_cases:
            sections = [
                (f"Section {i+1}", i+1, f"Content for section {i+1}")
                for i in range(num_sections)
            ]
            
            saved_files = chunking.save_chunks(test_document, sections)
            assert len(saved_files) == num_sections, \
                f"{description}: Expected {num_sections} chunks, got {len(saved_files)}"
            
            # Cleanup after each iteration
            chunking.remove_chunks(test_document)

    def test_chunk_content_not_empty(self):
        """Test that chunk content is substantial (not empty)."""
        test_document = "test_doc_content"
        sections = [
            ("Section with content", 1, "This is actual content"),
            ("Another section", 2, "More content here"),
        ]
        
        chunking.save_chunks(test_document, sections)
        chunks = chunking.load_chunks(test_document)
        
        for filename, content in chunks:
            assert content.strip(), f"Chunk {filename} is empty"
            # Content should be more than just metadata
            assert len(content) > len("Rubrik: \nSida: \n" + "=" * 60), \
                f"Chunk {filename} contains only metadata, no actual content"
        
        # Cleanup
        chunking.remove_chunks(test_document)

    def test_chunk_directory_structure(self):
        """Test that chunks are saved in correct directory structure."""
        test_document = "test_doc_structure"
        sections = [
            ("Test Section", 1, "Content"),
        ]
        
        chunking.save_chunks(test_document, sections)
        
        # Verify directory structure
        doc_chunks_dir = chunking.CHUNKS_DIR / test_document
        assert doc_chunks_dir.exists(), f"Directory {doc_chunks_dir} was not created"
        assert doc_chunks_dir.is_dir(), f"{doc_chunks_dir} is not a directory"
        
        # Verify chunk files exist in the correct directory
        chunk_files = list(doc_chunks_dir.glob("*.txt"))
        assert len(chunk_files) > 0, "No chunk files found in the directory"
        
        # Cleanup
        chunking.remove_chunks(test_document)

    def test_chunk_uniqueness(self):
        """Test that each chunk has unique content (no exact duplicates)."""
        test_document = "test_doc_uniqueness"
        sections = [
            ("Section 1", 1, "Unique content for section one"),
            ("Section 2", 2, "Unique content for section two"),
            ("Section 3", 3, "Unique content for section three"),
            # Test with different content but same-like name
            ("Section 4", 4, "Unique content for section four"),
        ]
        
        chunking.save_chunks(test_document, sections)
        chunks = chunking.load_chunks(test_document)
        
        # Extract content hashes (excluding metadata headers to compare actual content)
        content_hashes = []
        for filename, full_content in chunks:
            # Extract only the content part (after metadata)
            lines = full_content.split('\n')
            # Find where content starts (after the "====" line)
            content_start_idx = 0
            for i, line in enumerate(lines):
                if '=' in line:
                    content_start_idx = i + 2  # Skip the "====" and empty line
                    break
            
            actual_content = '\n'.join(lines[content_start_idx:]).strip()
            content_hash = hashlib.md5(actual_content.encode()).hexdigest()
            content_hashes.append((filename, content_hash, actual_content))
        
        # Verify no duplicate hashes
        hashes_only = [h for _, h, _ in content_hashes]
        unique_hashes = set(hashes_only)
        
        assert len(hashes_only) == len(unique_hashes), \
            f"Found duplicate chunks! Total: {len(hashes_only)}, Unique: {len(unique_hashes)}"
        
        # Log which chunks are unique
        for filename, content_hash, content in content_hashes:
            assert content_hash in unique_hashes, \
                f"Chunk {filename} with hash {content_hash} is a duplicate"
        
        # Cleanup
        chunking.remove_chunks(test_document)

    def test_chunk_uniqueness_detects_duplicates(self):
        """Test that the uniqueness check DETECTS actual duplicate content correctly."""
        test_document = "test_doc_dup_detection"
        sections = [
            ("Section A", 1, "This is identical content for testing"),
            ("Section B", 2, "This is identical content for testing"),  # SAME as Section A
            ("Section C", 3, "This is different content"),
        ]
        
        chunking.save_chunks(test_document, sections)
        chunks = chunking.load_chunks(test_document)
        
        # Extract content hashes
        content_hashes = []
        for filename, full_content in chunks:
            lines = full_content.split('\n')
            content_start_idx = 0
            for i, line in enumerate(lines):
                if '=' in line:
                    content_start_idx = i + 2
                    break
            
            actual_content = '\n'.join(lines[content_start_idx:]).strip()
            content_hash = hashlib.md5(actual_content.encode()).hexdigest()
            content_hashes.append((filename, content_hash, actual_content))
        
        # Verify that duplicates ARE found when they exist
        hashes_only = [h for _, h, _ in content_hashes]
        unique_hashes = set(hashes_only)
        
        # This SHOULD fail (detect duplicates)
        assert len(hashes_only) != len(unique_hashes), \
            "Expected to find duplicate chunks but none were detected"
        
        # Verify exactly 2 hashes (2 duplicates + 1 unique)
        assert len(unique_hashes) == 2, \
            f"Expected 2 unique hashes (1 duplicate pair + 1 unique), got {len(unique_hashes)}"
        
        # Cleanup
        chunking.remove_chunks(test_document)
        # Cleanup
        chunking.remove_chunks(test_document)

    def test_duplicate_filenames_handling(self):
        """Test that duplicate headline names are handled correctly."""
        test_document = "test_doc_dup_names"
        sections = [
            ("Same Headline", 1, "Content one"),
            ("Same Headline", 2, "Content two"),
            ("Different Headline", 3, "Content three"),
        ]
        
        saved_files = chunking.save_chunks(test_document, sections)
        
        # Should have 3 unique files despite duplicate headline
        assert len(saved_files) == 3
        # Filenames should be unique
        assert len(set(saved_files)) == 3, "Generated filenames are not unique"
        
        # Cleanup
        chunking.remove_chunks(test_document)


if __name__ == "__main__":
    """Run this test directly with: python tests/test_03_chunking.py"""
    print("\n" + "=" * 70)
    print("🧪 TEST 03: Chunking - Document Sectioning")
    print("=" * 70)
    print("\nTo run tests with pytest:")
    print("  python -m pytest tests/test_03_chunking.py -v")
    print("\nTo run a specific test:")
    print("  python -m pytest tests/test_03_chunking.py::TestChunking::test_chunk_uniqueness -v")
    print("=" * 70 + "\n")
