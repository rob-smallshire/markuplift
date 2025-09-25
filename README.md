<div align="center">
  <img src="https://raw.githubusercontent.com/rob-smallshire/markuplift/master/docs/images/logo.png" alt="Markuplift Logo" width="300">

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
from markuplift.predicates import html_block_elements, html_inline_elements

# Create formatter with HTML-aware defaults
formatter = Formatter(
    block_predicate_factory=html_block_elements(),
    inline_predicate_factory=html_inline_elements(),
    indent_size=2
)

# Format complex nested HTML (minified input)
messy_html = (
    '<ul><li>Getting Started<ul><li>Installation via <code>pip install markuplift</code>'
    '</li><li>Basic <em>configuration</em> and setup</li></ul></li><li>Advanced Features'
    '<ul><li>Custom <strong>predicates</strong> and XPath</li><li>External formatter <co'
    'de>integration</code></li></ul></li></ul>'
)
formatted = formatter.format_str(messy_html)
print(formatted)
```

**Output:**
```html
<ul>
  <li>Getting Started
    <ul>
      <li>Installation via <code>pip install markuplift</code></li>
      <li>Basic <em>configuration</em> and setup</li>
    </ul>
  </li>
  <li>Advanced Features
    <ul>
      <li>Custom <strong>predicates</strong> and XPath</li>
      <li>External formatter <code>integration</code></li>
    </ul>
  </li>
</ul>
```

### Real-World Example

Here's Markuplift formatting a complex article structure with mixed content:

```python
from markuplift import Formatter
from markuplift.predicates import html_block_elements, html_inline_elements

# Real-world messy HTML (imagine this came from a CMS or generator)
messy_html = (
    '<article><h1>Using Markuplift</h1><section><h2>Introduction</h2><p>Markuplift is a <em>'
    'powerful</em> formatter for <strong>XML and HTML</strong>.</p><p>Key features include:<'
    '/p><ul><li>Configurable <code>block</code> and <code>inline</code> elements</li><li>XPa'
    'th-based element selection</li><li>Custom text formatters for <pre><code>code blocks</c'
    'ode></pre></li></ul></section></article>'
)

formatter = Formatter(
    block_predicate_factory=html_block_elements(),
    inline_predicate_factory=html_inline_elements(),
    indent_size=2
)

formatted = formatter.format_str(messy_html)
print(formatted)
```

**Output:**
```html
<article>
  <h1>Using Markuplift</h1>
  <section>
    <h2>Introduction</h2>
    <p>Markuplift is a <em>powerful</em> formatter for <strong>XML and HTML</strong>.</p>
    <p>Key features include:</p>
    <ul>
      <li>Configurable <code>block</code> and <code>inline</code> elements</li>
      <li>XPath-based element selection</li>
      <li>Custom text formatters for
        <pre><code>code blocks</code></pre>
      </li>
    </ul>
  </section>
</article>
```

### Advanced Example

Complex HTML form with custom formatting rules:

```python
from markuplift import Formatter
from markuplift.predicates import html_block_elements, html_inline_elements

# HTML form structure (typical from form builders)
messy_form = (
    '<form><fieldset><legend>User Information</legend><div><label>Name: <input type="text" '
    'name="name" required="required"/></label></div><div><label>Email: <input type="email" '
    'name="email"/></label></div><div><label><input type="checkbox" name="subscribe"/> Subs'
    'cribe to <em>newsletter</em></label></div></fieldset><button type="submit">Submit <str'
    'ong>Form</strong></button></form>'
)

formatter = Formatter(
    block_predicate_factory=html_block_elements(),
    inline_predicate_factory=html_inline_elements(),
    indent_size=2
)

formatted = formatter.format_str(messy_form)
print(formatted)
```

**Output:**
```html
<form>
  <fieldset>
    <legend>User Information</legend>
    <div>
      <label>Name: <input type="text" name="name" required="required" /></label>
    </div>
    <div>
      <label>Email: <input type="email" name="email" /></label>
    </div>
    <div>
      <label><input type="checkbox" name="subscribe" /> Subscribe to <em>newsletter</em></label>
    </div>
  </fieldset>
  <button type="submit">Submit <strong>Form</strong></button>
</form>
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
- **Diffing and version control** - Improve readability of markup changes in version control systems

## License

Markuplift is released under the [MIT License](https://github.com/rob-smallshire/markuplift/blob/master/LICENSE).

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Setting up the development environment
- Running tests and linting
- Submitting pull requests
- Reporting issues
