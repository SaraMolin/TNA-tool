"""
Shared test configuration and fixtures.

Provides common setup, utilities, and fixtures for all test modules.
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path so we can import project modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def uploads_dir():
    """Fixture that provides path to uploads directory."""
    path = project_root / "uploads"
    path.mkdir(exist_ok=True)
    return path


@pytest.fixture
def chunks_dir():
    """Fixture that provides path to chunks directory."""
    path = project_root / "chunks"
    path.mkdir(exist_ok=True)
    return path


@pytest.fixture
def output_dir():
    """Fixture that provides path to output directory."""
    path = project_root / "output"
    path.mkdir(exist_ok=True)
    return path


@pytest.fixture
def get_uploaded_pdfs():
    """Fixture that returns list of all PDFs in uploads directory."""
    uploads_path = project_root / "uploads"
    if not uploads_path.exists():
        return []
    return list(uploads_path.glob("*.pdf"))


@pytest.fixture
def project_root_path():
    """Fixture that provides the project root path."""
    return project_root
