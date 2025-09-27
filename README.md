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

Here are three comprehensive examples showing different ways to use MarkupLift from the command line:

#### Demo 1: Basic XML Formatting

This demonstrates the most basic usage - formatting a messy XML configuration file with default settings.

**Input:**

```xml
<!-- messy_config.xml -->
<?xml version="1.0"?>
<configuration>
<database><host>localhost</host><port>5432</port><name>myapp</name></database>
<features><feature name="logging" enabled="true">   <level>INFO</level>  <file>/var/log/app.log</file>   </feature>
<feature name="caching" enabled="false"></feature><feature name="auth" enabled="true"><provider>oauth</provider><timeout>3600</timeout></feature>
</features>
</configuration>
```

**Command:**
```bash
$ markuplift format messy_config.xml
```

```xml
<!-- Formatted output -->
<configuration>
  <database>
    <host>localhost</host>
    <port>5432</port>
    <name>myapp</name>
  </database>
  <features>
    <feature name="logging" enabled="true">
      <level>INFO</level>
      <file>/var/log/app.log</file>
    </feature>
    <feature name="caching" enabled="false" />
    <feature name="auth" enabled="true">
      <provider>oauth</provider>
      <timeout>3600</timeout>
    </feature>
  </features>
</configuration>
```

#### Demo 2: Custom Block Elements

This shows how to customize which elements are treated as block elements using XPath expressions. This is particularly useful for HTML documents where you want specific semantic elements to be formatted as blocks.

**Input:**

```html
<!-- messy_article.html -->
<!DOCTYPE html>
<html><head><title>Blog Post</title></head><body><div><article><header><h1>Understanding     XML     Formatting</h1></header><section><p>XML formatting is   important   for   readability.</p><div><code class="language-xml">&lt;root&gt;&lt;child&gt;content&lt;/child&gt;&lt;/root&gt;</code></div><p>Here's how    to   format   it   properly:</p></section></article></div></body></html>
```

**Command:**
```bash
$ markuplift format messy_article.html --block "//div | //section | //article"
```

```html
<!-- Formatted output -->
<!DOCTYPE html>
<html>
  <head>
    <title>Blog Post</title>
  </head>
  <body>
    <div>
      <article>
        <header>
          <h1>Understanding     XML     Formatting</h1>
        </header>
        <section>
          <p>XML formatting is   important   for   readability.</p>
          <div>
            <code class="language-xml">&lt;root&gt;&lt;child&gt;content&lt;/child&gt;&lt;/root&gt;</code>
          </div>
          <p>Here's how    to   format   it   properly:</p>
        </section>
      </article>
    </div>
  </body>
</html>
```

#### Demo 3: Stdin/Stdout Processing

This demonstrates pipeline usage, reading from stdin and formatting the output. This is useful for integrating MarkupLift into shell scripts and build processes.

**Command:**
```bash
$ cat messy_config.xml | markuplift format --output formatted_config.xml
```

```xml
<!-- Formatted output -->
<configuration>
  <database>
    <host>localhost</host>
    <port>5432</port>
    <name>myapp</name>
  </database>
  <features>
    <feature name="logging" enabled="true">
      <level>INFO</level>
      <file>/var/log/app.log</file>
    </feature>
    <feature name="caching" enabled="false" />
    <feature name="auth" enabled="true">
      <provider>oauth</provider>
      <timeout>3600</timeout>
    </feature>
  </features>
</configuration>
```


### Python API Example

Here's how to format HTML with whitespace preservation in `<code>` and `<pre>` elements:

```python
from markuplift import Formatter
from markuplift.predicates import html_block_elements, html_inline_elements, tag_in

# Create formatter with whitespace handling
formatter = Formatter(
    block_when=html_block_elements(),
    inline_when=html_inline_elements(),
    preserve_whitespace_when=tag_in("pre", "code"),
    indent_size=2
)

# Messy input HTML
messy_html = """<div><h3>Documentation</h3><p>Here are some    spaced    examples:</p><ul><li>Installation: <code>   pip install markuplift   </code></li><li>Basic <em>configuration</em> and setup</li><li>Code example:<pre>    def format_xml():
        return "beautiful"
    </pre></li></ul></div>"""

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

**Input** (`article_example.html`):
```html
<article><h1>Using   Markuplift</h1><section><h2>Code    Formatting</h2><p>Here's how to    use   our   API   with   proper   spacing:</p><pre><code>from markuplift import Formatter
formatter = Formatter(
    preserve_whitespace=True
)</code></pre><p>The   <em>preserve_whitespace</em>   feature   keeps   code   formatting   intact   while   <strong>normalizing</strong>   text   content!</p></section></article>
```

```python
from markuplift import Formatter
from markuplift.predicates import html_block_elements, html_inline_elements, tag_in, any_of

formatter = Formatter(
    block_when=html_block_elements(),
    inline_when=html_inline_elements(),
    preserve_whitespace_when=tag_in("pre", "code"),
    normalize_whitespace_when=any_of(tag_in("p", "li", "h1", "h2", "h3"), html_inline_elements()),
    indent_size=2
)

# Format real-world messy HTML directly from file
formatted = formatter.format_file('article_example.html')
print(formatted)
```

**Output:**
```html
<article>
  <h1>Using Markuplift</h1>
  <section>
    <h2>Code Formatting</h2>
    <p>Here's how to use our API with proper spacing:</p>
    <pre><code>from markuplift import Formatter formatter = Formatter( preserve_whitespace=True )</code></pre>
    <p>The <em>preserve_whitespace</em> feature keeps code formatting intact while <strong>normalizing</strong> text content!</p>
  </section>
</article>
```

### Custom CSS Class Predicates

You can create custom predicates for advanced element matching:

```python
def has_css_class(class_name: str) -> ElementPredicateFactory:
    """Factory for predicate matching elements with a specific CSS class.

    This demonstrates the triple-nested function pattern used by MarkupLift
    for efficient document-specific predicate optimization.

    Args:
        class_name: The CSS class name to match (without spaces)

    Returns:
        ElementPredicateFactory that creates optimized predicates

    Raises:
        PredicateError: If class_name is empty or contains spaces

    Example:
        >>> formatter = Formatter(
        ...     preserve_whitespace_when=has_css_class("code-block")
        ... )
    """
    # Level 1: Configuration and validation
    if not class_name or not class_name.strip():
        raise PredicateError("CSS class name cannot be empty")
    if ' ' in class_name:
        raise PredicateError("CSS class name cannot contain spaces")

    clean_class = class_name.strip()

    def create_document_predicate(root) -> ElementPredicate:
        # Level 2: Document-specific preparation - find all matching elements once
        matching_elements = set()
        for element in root.iter():
            class_attr = element.get('class', '')
            if class_attr and clean_class in class_attr.split():
                matching_elements.add(element)

        def element_predicate(element) -> bool:
            # Level 3: Fast membership test
            return element in matching_elements
        return element_predicate
    return create_document_predicate
```

**Usage:**
```python
from markuplift import Formatter
from markuplift.predicates import html_block_elements, html_inline_elements, any_of

formatter = Formatter(
    block_when=html_block_elements(),
    inline_when=html_inline_elements(),
    preserve_whitespace_when=has_css_class("code-block"),
    normalize_whitespace_when=any_of(has_css_class("prose"), html_inline_elements()),
    indent_size=2
)

# Example HTML with CSS classes
html = """<div class="container"><p class="prose">Text content</p><pre class="code-block">preserved code</pre></div>"""
formatted = formatter.format_str(html)
print(formatted)
```

**Output:**
```html
<div class="container">
  <p class="prose">Text content</p>
  <pre class="code-block">preserved code</pre>
</div>
```

### Attribute Value Formatting

Markuplift can format complex attribute values like CSS styles:

**Input** (`attribute_formatting_example.html`):
```html
<div>
    <p style="color: red;">Simple (1 property)</p>
    <p style="color: blue; background: white;">Medium (2 properties)</p>
    <p style="color: green; background: black; margin: 10px; padding: 5px;">Complex (4 properties)</p>
</div>
```

```python
def num_css_properties(style_value: str) -> int:
    """Count the number of CSS properties in a style attribute value.

    Args:
        style_value: The CSS style attribute value

    Returns:
        Number of CSS properties found

    Example:
        >>> num_css_properties("color: red; background: blue")
        2
        >>> num_css_properties("color: red;")
        1
    """
    return len([prop.strip() for prop in style_value.split(';') if prop.strip()])

def css_multiline_formatter(value, formatter, level):
    """Format CSS as multiline when it has many properties.

    This formatter takes CSS style attributes and formats them with proper
    indentation when they contain multiple properties.

    Args:
        value: The CSS style attribute value to format
        formatter: The MarkupLift formatter instance (for accessing indent settings)
        level: The current indentation level in the document

    Returns:
        Formatted CSS string with proper indentation

    Example:
        Input:  "color: green; background: black; margin: 10px; padding: 5px"
        Output: "\\n    color: green;\\n    background: black;\\n    margin: 10px;\\n    padding: 5px\\n  "
    """
    properties = [prop.strip() for prop in value.split(';') if prop.strip()]
    base_indent = formatter.one_indent * level
    property_indent = formatter.one_indent * (level + 1)
    formatted_props = [f"{property_indent}{prop}" for prop in properties]
    return '\n' + ';\n'.join(formatted_props) + '\n' + base_indent

# Format HTML with complex CSS styles
formatter = Formatter(
    block_when=html_block_elements(),
    reformat_attribute_when={
        # Only format styles with 4+ CSS properties
        html_block_elements().with_attribute("style", lambda v: num_css_properties(v) >= 4): css_multiline_formatter
    }
)

# Format HTML file with attribute formatting
formatted = formatter.format_file('attribute_formatting_example.html')
print(formatted)
```

**Output:**
```html
<div>
  <p style="color: red;">Simple (1 property)</p>
  <p style="color: blue; background: white;">Medium (2 properties)</p>
  <p style="
    color: green;
    background: black;
    margin: 10px;
    padding: 5px
  ">Complex (4 properties)</p>
</div>
```

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