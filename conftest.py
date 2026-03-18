"""
Root pytest configuration for IL-2 Modular Mission Orchestrator.
Shared fixtures and settings used by all test suites.
"""

import pytest
import sys
from pathlib import Path

# Add src/ to Python path so tests can import mmf modules
# Example: from mmf.parser import deserializer
SRC_PATH = Path(__file__).parent / 'src'
sys.path.insert(0, str(SRC_PATH))


@pytest.fixture
def reference_files():
    """
    Returns the path to reference IL-2 .Group and .Mission files.
    
    These files are used for round-trip testing (parse → serialize → compare).
    They should be collected from your IL-2 installation in Phase 0.1.
    
    Location: tests/fixtures/il2_files/
    """
    path = Path(__file__).parent / 'tests' / 'fixtures' / 'il2_files'
    
    # Note: Directory may be empty until Phase 0.1 (file collection gate)
    # Tests can gracefully skip if files are missing
    
    return path


@pytest.fixture
def test_data_dir():
    """
    Returns the path to test fixture data (JSON schemas, sample modules).
    
    Location: tests/fixtures/
    """
    return Path(__file__).parent / 'tests' / 'fixtures'


@pytest.fixture
def project_root():
    """
    Returns the root directory of the project.
    Useful for tests that need to reference config files or data directories.
    """
    return Path(__file__).parent
