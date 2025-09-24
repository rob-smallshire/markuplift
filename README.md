<div align="center">
  <img src="docs/images/logo.png" alt="Markuplift Logo" width="300">

  # Markuplift

  **A configurable XML and HTML formatter for Python**

  [![CI](https://img.shields.io/github/actions/workflow/status/rob-smallshire/markuplift/ci.yml?branch=master&label=CI)](https://github.com/rob-smallshire/markuplift/actions/workflows/ci.yml)
  [![PyPI version](https://img.shields.io/pypi/v/markuplift)](https://pypi.org/project/markuplift/)
  [![Python versions](https://img.shields.io/pypi/pyversions/markuplift)](https://pypi.org/project/markuplift/)
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/rob-smallshire/markuplift/blob/master/LICENSE)
  [![Downloads](https://img.shields.io/pypi/dm/markuplift)](https://pypi.org/project/markuplift/)
</div>

Markuplift provides flexible, configurable formatting of XML and HTML documents. Unlike basic pretty-printers, Markuplift gives you complete control over how your markup is formatted through user-defined predicates for block vs inline elements, whitespace handling, and custom text content formatters.

## Key Features

- **Configurable element classification** - Define block/inline elements using XPath expressions or Python predicates
- **Flexible whitespace control** - Normalize, preserve, or strip whitespace on a per-element basis
- **External formatter integration** - Pipe element text content through external tools (e.g., js-beautify, prettier)
- **Comprehensive format options** - Control indentation, attribute wrapping, self-closing tags, and more
- **CLI and Python API** - Use from command line or integrate into your Python applications
- **Performance optimized** - Uses factory pattern with single-pass XPath evaluation

## Quick Start

### Installation

Install from PyPI using pip:
```bash
pip install markuplift
```

Or using uv (recommended for modern Python development):
```bash
uv add markuplift
```

For development installation with all dependencies:
```bash
git clone https://github.com/rob-smallshire/markuplift.git
cd markuplift
uv sync --all-extras
```

### CLI Usage

```bash
# Basic formatting
markuplift format input.xml

# Format with custom block elements
markuplift format input.html --block "//div | //section | //article"

# Use external JavaScript formatter for script tags
markuplift format input.html --text-formatter "//script[@type='text/javascript']" "js-beautify"

# Format from stdin to stdout
cat messy.xml | markuplift format --output formatted.xml
```

### Python API

```python
from markuplift import Formatter
from markuplift.predicates import html_block_elements, tag_in

# Create formatter with HTML-aware defaults
formatter = Formatter(
    block_predicate_factory=html_block_elements(),
    inline_predicate_factory=tag_in("em", "strong", "code", "a"),
    indent_size=2
)

# Format HTML string
messy_html = "<div><p>Hello <em>world</em>!</p><p>Another paragraph.</p></div>"
formatted = formatter.format_str(messy_html)
print(formatted)
```

**Output:**
```html
<div>
  <p>Hello <em>world</em>!</p>
  <p>Another paragraph.</p>
</div>
```

### Advanced Example

```python
from markuplift import Formatter
from markuplift.predicates import matches_xpath, html_block_elements

# Custom formatter with XPath-based rules
formatter = Formatter(
    block_predicate_factory=html_block_elements(),
    inline_predicate_factory=matches_xpath("//code | //kbd | //var"),
    normalize_whitespace_predicate_factory=matches_xpath("//p | //div"),
    preserve_whitespace_predicate_factory=matches_xpath("//pre | //script"),
    text_content_formatters={
        matches_xpath("//script[@type='text/javascript']"): lambda text, fmt, level: js_beautify(text),
    }
)

result = formatter.format_str(your_html)
```

## Documentation

- **[API Documentation](https://markuplift.readthedocs.io/)** - Comprehensive API reference
- **[User Guide](https://markuplift.readthedocs.io/en/latest/guide/)** - Detailed usage examples and tutorials
- **[Predicate Reference](https://markuplift.readthedocs.io/en/latest/predicates/)** - Built-in predicates and custom predicate creation
- **[CLI Reference](https://markuplift.readthedocs.io/en/latest/cli/)** - Complete command-line interface documentation

## Use Cases

Markuplift is perfect for:

- **Web development** - Format HTML templates and components with consistent styling
- **Data processing** - Clean up XML data feeds and configuration files
- **Documentation** - Standardize markup in documentation systems
- **Code generation** - Format dynamically generated XML/HTML with precise control
- **CI/CD pipelines** - Ensure consistent markup formatting across your codebase

## Requirements

- **Python 3.12+**
- **Dependencies**: `lxml`, `click`

## License

Markuplift is released under the [MIT License](https://github.com/rob-smallshire/markuplift/blob/master/LICENSE).

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Setting up the development environment
- Running tests and linting
- Submitting pull requests
- Reporting issues

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

---

**Made with love by [Robert Smallshire](https://github.com/rob-smallshire)**