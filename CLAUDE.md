# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MarkupLift is a configurable XML and HTML formatter written in Python. The project uses lxml for XML/HTML parsing and provides a flexible formatting system based on user-defined predicates for block vs inline elements, whitespace handling, and attribute formatting.

## Development Commands

This project uses uv for dependency management and Python 3.12+.

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_formatter_from_compact.py

# Run tests with verbose output
pytest -v

# Run tests for specific functionality
pytest tests/test_attribute_formatting.py
pytest tests/test_comments.py
pytest tests/test_doctype.py

# Run approval tests (uses console diff output)
pytest tests/test_with_real_data.py

# Force console reporter for approval tests (if needed)
pytest --approvaltests-use-reporter='PythonNativeReporter'
```

### Linting
```bash
# Install lint dependencies
uv sync --group lint

# Run ruff linting
uv run ruff check

# Run ruff with auto-fix
uv run ruff check --fix

# Format code with ruff
uv run ruff format
```

### Building and Installation
```bash
# Install in development mode
uv sync

# Install with specific dependency groups
uv sync --group dev
uv sync --group test
uv sync --group doc
```

### Version Management
```bash
# Bump version (uses bump-my-version)
uv run bump-my-version bump patch
uv run bump-my-version bump minor
uv run bump-my-version bump major
```

## Architecture

### Core Components

- **`src/markuplift/formatter.py`**: Main Formatter class that handles XML/HTML formatting logic
- **`src/markuplift/cli.py`**: Command-line interface implementation (currently minimal)
- **`src/markuplift/__main__.py`**: Entry point for the package
- **`src/markuplift/utilities.py`**: Utility functions
- **`src/markuplift/__init__.py`**: Package initialization and version info

### Test Infrastructure

- **`tests/data/`**: Real XML/HTML test files used as input for formatter testing
- **`tests/approved/`**: Golden master files (`.approved.txt`) containing expected formatter output
- **`tests/conftest.py`**: Pytest configuration with ApprovalTests console reporter setup
- Uses ApprovalTests for golden master testing with console diff output suitable for CI/AI agents

### Key Classes

- **`Formatter`**: Main formatting engine with configurable predicates for:
  - `block_predicate`: Determines which elements are treated as block elements
  - `inline_predicate`: Determines which elements are treated as inline elements
  - `normalize_whitespace_predicate`: Controls whitespace normalization
  - `preserve_whitespace_predicate`: Controls whitespace preservation
  - `wrap_attributes_predicate`: Controls attribute wrapping behavior
  - `text_content_formatters`: Custom formatters for element text content

- **`Annotations`**: System for storing temporary metadata about elements during formatting

### Test Structure

Tests are organized by functionality:
- `test_formatter_from_compact.py` / `test_formatter_from_indented.py`: Core formatting tests
- `test_attribute_formatting.py`: Attribute handling tests
- `test_comments.py`: Comment preservation tests
- `test_doctype.py`: DOCTYPE handling tests
- `test_processing_instructions.py`: XML processing instruction tests
- `test_self_closing_elements.py`: Self-closing tag tests
- `test_text_formatting.py`: Text content formatting tests
- `test_with_real_data.py`: **Approval tests** with real-world XML/HTML data (uses ApprovalTests)
- `test_readme_examples.py`: Tests ensuring README examples work correctly
- `helpers/predicates.py`: Test helper functions

#### Approval Testing
- Real messy input files in `tests/data/` (e.g., `messy_html_page.html`, `messy_xml_chunked_content.xml`)
- Expected outputs in auto-generated `.approved.txt` files
- Console diff output shows changes clearly for CI and AI agents
- Use `pytest tests/test_with_real_data.py` to run approval tests

### Configuration

The project uses `pyproject.toml` for configuration:
- pytest configuration with testpaths set to "tests"
- ruff linting with 120 character line length
- setuptools build system
- bump-my-version for version management
- Dependency groups for different development needs (test, lint, doc, dev)

## Development Notes

- Uses approval testing (approvaltests) for some test validation
- Hypothesis for property-based testing
- The formatter preserves XML declarations, DOCTYPE declarations, processing instructions, and comments
- Elements are classified as block/inline based on predicates, with fallback logic for unclassified elements
- Whitespace handling is configurable per element type
- The codebase follows Python 3.12+ type annotations
- To run the tests and other Python-based commands that need tools from the environment, use `uv run`.
- Refer to FORMATTING_RULES.md before making any code or test changes.
- Update the README.md file only by modify the template @scripts/README.md.j2 and the examples embedded within by running @scripts/generate_readme.py with `uv run python scripts/generate_readme.py`