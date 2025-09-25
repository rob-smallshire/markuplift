# Contributing to Markuplift

Thank you for your interest in contributing to Markuplift! We welcome contributions through issue reports and pull requests.

## Getting Started

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/rob-smallshire/markuplift.git
   cd markuplift
   ```

2. **Install development dependencies**
   ```bash
   uv sync --all-extras
   ```

3. **Verify your setup**
   ```bash
   uv run pytest
   uv run ruff check
   ```

### Project Structure

- `src/markuplift/` - Main package source code
- `tests/` - Test suite using pytest
- `docs/` - Documentation and assets
- `pyproject.toml` - Project configuration and dependencies

## How to Contribute

### Reporting Issues

When reporting bugs or requesting features, please:

1. **Check existing issues** to avoid duplicates
2. **Use descriptive titles** that summarize the problem
3. **Provide details** including:
   - Python version and operating system
   - Markuplift version
   - Minimal code example that reproduces the issue
   - Expected vs actual behavior
   - Error messages and stack traces

### Submitting Pull Requests

1. **Fork the repository** and create a feature branch
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our development practices:
   - Write clear, focused commits
   - Add tests for new functionality
   - Update documentation if needed
   - Follow the existing code style

3. **Test your changes**
   ```bash
   # Run all tests
   uv run pytest

   # Run linting
   uv run ruff check

   # Format code if needed
   uv run ruff format
   ```

4. **Update README examples** if your changes affect user-facing functionality
   - All README examples are tested in `tests/test_readme_examples.py`
   - Update tests when you change examples

5. **Submit the pull request**
   - Write a clear description of your changes
   - Reference any related issues
   - Include screenshots for UI-related changes

## Development Guidelines

### Code Style

- **Follow existing patterns** in the codebase
- **Use type hints** for all public APIs
- **Write docstrings** for modules, classes, and functions
- **Keep functions focused** and reasonably sized
- **Use descriptive variable names**

### Testing

- **Write tests** for all new functionality
- **Maintain test coverage** for critical code paths
- **Test edge cases** and error conditions
- **Use descriptive test names** that explain what's being tested

Example test structure:
```python
def test_formatter_handles_nested_lists():
    """Test that nested lists are formatted with proper indentation."""
    # Test implementation
```

### Documentation

- **Update docstrings** when changing function signatures
- **Add examples** to docstrings for complex functionality
- **Keep README.md current** with any new features
- **Update type annotations** when changing interfaces

### Performance

- **Consider performance impact** of changes
- **Use the factory pattern** for predicates to avoid repeated computations
- **Profile performance-critical paths** when making optimizations
- **Maintain existing performance characteristics**

## Architecture Notes

### Key Concepts

- **ElementPredicate**: Functions that determine if an element matches criteria
- **ElementPredicateFactory**: Functions that create optimized predicates for documents
- **Factory Pattern**: Used to avoid repeated XPath evaluations and improve performance
- **Annotations**: Temporary metadata system for storing element classifications

### Adding New Predicates

When adding new predicate factories:

1. **Follow the factory pattern**:
   ```python
   def your_predicate(param: str) -> ElementPredicateFactory:
       def create_document_predicate(root: etree._Element) -> ElementPredicate:
           # Expensive operations here (e.g., XPath evaluation)
           def element_predicate(element: etree._Element) -> bool:
               # Fast element checks here
               return condition
           return element_predicate
       return create_document_predicate
   ```

2. **Add validation** for parameters using the `PredicateError` exception
3. **Write comprehensive tests** including edge cases
4. **Document the predicate** with clear examples

## Release Process

Releases are managed by the maintainers:

1. Version bumping using `bump-my-version`
2. Automated testing via GitHub Actions
3. Publication to PyPI on tagged releases

## Getting Help

- **Check the documentation** and existing issues first
- **Start discussions** in issues for design questions
- **Be patient** - maintainers review contributions as time allows
- **Be respectful** in all interactions

## Questions?

If you have questions about contributing, feel free to open an issue with the "question" label. We're here to help make your contribution successful!

---

Thank you for helping make Markuplift better! 🚀
