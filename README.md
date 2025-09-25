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
from markuplift.predicates import html_block_elements, html_inline_elements, tag_in

# Create formatter with whitespace handling
formatter = Formatter(
    block_predicate_factory=html_block_elements(),
    inline_predicate_factory=html_inline_elements(),
    preserve_whitespace_predicate_factory=tag_in("pre", "code"),
    indent_size=2
)

# Format complex HTML with code examples (preserves whitespace in <code>)
messy_html = (
    '<div><h3>Documentation</h3><p>Here are some    spaced    examples:</p>'
    '<ul><li>Installation: <code>   pip install markuplift   </code></li>'
    '<li>Basic <em>configuration</em> and setup</li><li>Code example:'
    '<pre>    def format_xml():\n        return "beautiful"\n    </pre></li></ul></div>'
)
formatted = formatter.format_str(messy_html)
print(formatted)
```

**Output:**
```html
<div>
  <h3>Documentation</h3>
  <p>Here are some    spaced    examples:</p>
  <ul>
    <li>Installation: <code>   pip install markuplift   </code></li>
    <li>Basic <em>configuration</em> and setup</li>
    <li>Code example:
      <pre>    def format_xml():
        return "beautiful"
    </pre>
    </li>
  </ul>
</div>
```

### Real-World Example

Here's Markuplift formatting a complex article structure with mixed content:

```python
from markuplift import Formatter
from markuplift.predicates import html_block_elements, html_inline_elements, tag_in, any_of

# Real-world messy HTML with code blocks and excessive whitespace
messy_html = (
    '<article><h1>Using   Markuplift</h1><section><h2>Code    Formatting</h2>'
    '<p>Here\'s how to    use   our   API   with   proper   spacing:</p>'
    '<pre><code>from markuplift import Formatter\nformatter = Formatter(\n    '
    'preserve_whitespace=True\n)</code></pre><p>The   <em>preserve_whitespace</em>   '
    'feature   keeps   code   formatting   intact   while   <strong>normalizing</strong>   '
    'text   content!</p></section></article>'
)

formatter = Formatter(
    block_predicate_factory=html_block_elements(),
    inline_predicate_factory=html_inline_elements(),
    preserve_whitespace_predicate_factory=tag_in("pre", "code"),
    normalize_whitespace_predicate_factory=any_of(tag_in("p", "li"), html_inline_elements()),
    indent_size=2
)

formatted = formatter.format_str(messy_html)
print(formatted)
```

**Output:**
```html
<article>
  <h1>Using   Markuplift</h1>
  <section>
    <h2>Code    Formatting</h2>
    <p>Here's how to use our API with proper spacing:</p>
    <pre><code>from markuplift import Formatter formatter = Formatter( preserve_whitespace=True )</code></pre>
    <p>The <em>preserve_whitespace</em> feature keeps code formatting intact while <strong>normalizing</strong> text content!</p>
  </section>
</article>
```

### Advanced Example

Technical documentation with comprehensive whitespace control:

```python
from markuplift import Formatter
from markuplift.predicates import html_block_elements, html_inline_elements, tag_in, any_of

# Technical documentation with code, forms, and mixed content
messy_html = (
    '<div><h2>API   Documentation</h2><p>Use this    form   to   test   the   API:</p>'
    '<form><fieldset><legend>Configuration</legend><div><label>Code Sample: '
    '<textarea name="code">    def example():\n        return "test"\n        # preserve formatting'
    '</textarea></label></div><div><p>Inline   code   like   <code>   format()   </code>   '
    'works   perfectly!</p></div></fieldset></form><h3>Expected   Output:</h3>'
    '<pre>{\n  "status": "formatted",\n  "whitespace": "preserved"\n}</pre></div>'
)

formatter = Formatter(
    block_predicate_factory=html_block_elements(),
    inline_predicate_factory=html_inline_elements(),
    preserve_whitespace_predicate_factory=tag_in("pre", "code", "textarea"),
    normalize_whitespace_predicate_factory=any_of(tag_in("p", "li", "h1", "h2", "h3"), html_inline_elements()),
    indent_size=2
)

formatted = formatter.format_str(messy_html)
print(formatted)
```

**Output:**
```html
<div>
  <h2>API Documentation</h2>
  <p>Use this form to test the API:</p>
  <form>
    <fieldset>
      <legend>Configuration</legend>
      <div>
        <label>Code Sample: <textarea name="code">    def example():
        return "test"
        # preserve formatting</textarea></label>
      </div>
      <div>
        <p>Inline code like <code> format() </code> works perfectly!</p>
      </div>
    </fieldset>
  </form>
  <h3>Expected Output:</h3>
  <pre>{
  "status": "formatted",
  "whitespace": "preserved"
}</pre>
</div>
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
