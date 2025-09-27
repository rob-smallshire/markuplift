"""Pytest configuration and fixtures for markuplift tests."""

import pytest
from pathlib import Path
from approvaltests.reporters import PythonNativeReporter
from approvaltests import set_default_reporter


@pytest.fixture(scope="session", autouse=True)
def configure_approvaltests():
    """Configure ApprovalTests to use console reporter for CI/AI-friendly output."""
    set_default_reporter(PythonNativeReporter())


@pytest.fixture
def test_data_path():
    """Factory fixture that returns the full path to a test data file.

    Usage:
        def test_something(test_data_path):
            html_file = test_data_path("messy_html_page.html")
            with open(html_file) as f:
                content = f.read()
    """
    def _get_test_data_path(filename: str) -> Path:
        """Get the full path to a test data file.

        Args:
            filename: Name of the file in tests/data directory

        Returns:
            Path object pointing to the test data file

        Raises:
            FileNotFoundError: If the test data file doesn't exist
        """
        test_dir = Path(__file__).parent
        data_dir = test_dir / "data"
        file_path = data_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Test data file not found: {file_path}")

        return file_path

    return _get_test_data_path