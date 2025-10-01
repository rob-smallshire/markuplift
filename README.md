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

- **Specialized formatters** - `Html5Formatter` for HTML with HTML5 defaults, `XmlFormatter` for strict XML compliance
- **Type-safe configuration** - Use `ElementType` enum for better type safety and IDE support
- **Configurable element classification** - Define block/inline elements using XPath expressions or Python predicates
- **Flexible whitespace control** - Normalize, preserve, or strip whitespace on a per-element basis
- **External formatter integration** - Pipe element text content through external tools (e.g., js-beautify, prettier)
- **Comprehensive format options** - Control indentation, attribute wrapping, self-closing tags, and more
- **CLI and Python API** - Use from command line or integrate into your Python applications

## Understanding Block vs Inline Elements

> **Important:** Markuplift's "block" and "inline" concepts are about **formatting and whitespace handling**, in the source, not CSS layout or browser rendering. These classifications determine how Markuplift adds newlines and indentation around elements.

### Block Elements
**Block elements** get their own lines with proper indentation. Typical examples include structural elements like `<p>`, `<div>`, `<ul>`, `<li>`, `<h1>`, etc.

### Inline Elements
**Inline elements** flow within text content without adding line breaks. Typical examples include text formatting elements like `<em>`, `<strong>`, `<code>`, `<a>`, etc.

### Example: Why This Matters

**Input (messy):**
```html
<p>This paragraph contains <em>emphasized text</em> and <strong>bold text</strong>.</p><ul><li>First item with <code>inline code</code></li><li>Second item</li></ul>
```

**With proper block/inline classification:**
```html
<p>This paragraph contains <em>emphasized text</em> and <strong>bold text</strong>.</p>
<ul>
  <li>First item with <code>inline code</code></li>
  <li>Second item</li>
</ul>
```

Notice how:
- **Block elements** (`<p>`, `<ul>`, `<li>`) get their own lines and indentation
- **Inline elements** (`<em>`, `<strong>`, `<code>`) stay within the text flow
- Whitespace is added **around** elements, not **within** their text content

**What would happen with wrong classification:**
```html
<!-- If <em> and <strong> were treated as block: -->
<p>This paragraph contains
  <em>emphasized text</em>
   and
  <strong>bold text</strong>
.</p>
<!-- Breaks the text flow! -->

<!-- If <ul> and <li> were treated as inline: -->
<p>This paragraph contains <em>emphasized text</em> and <strong>bold text</strong>.</p><ul><li>First item with <code>inline code</code></li><li>Second item</li></ul>
<!-- Poor readability! -->
```

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
<?xml version="1.0"?><configuration><database><host>localhost</host><port>
5432</port><name>myapp</name></database><features><feature name="logging"
enabled="true">   <level>INFO</level>  <file>/var/log/app.log</file>
</feature><feature name="caching" enabled="false"></feature><feature name=
"auth" enabled="true"><provider>oauth</provider><timeout>3600</timeout>
</feature></features></configuration>
```

**Command:**
```bash
$ markuplift format messy_config.xml
```

```xml
<configuration>
  <database>
    <host>localhost</host>
    <port>
5432</port>
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
<!DOCTYPE html>
<html><head><title>Blog Post</title></head><body><div><article><header>
<h1>Understanding     XML     Formatting</h1></header><section><p>XML
formatting is   important   for   readability.</p><div>
<code class="language-xml">&lt;root&gt;&lt;child&gt;content&lt;/child&gt;&lt;/root&gt;</code>
</div><p>Here's how    to   format   it   properly:</p></section></article>
</div></body></html>
```

**Command:**
```bash
$ markuplift format-html messy_article.html --block "//div | //section | //article"
```

```html
<!DOCTYPE html>
<html>
  <head>
    <title>Blog Post</title>
  </head>
  <body>
    <div>
      <article>
        <header>
          <h1>Understanding XML Formatting</h1>
        </header>
        <section>
          <p>XML formatting is important for readability.</p>
          <div><code class="language-xml">&lt;root&gt;&lt;child&gt;content&lt;/child&gt;&lt;/root&gt;</code></div>
          <p>Here's how to format it properly:</p>
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
<configuration>
  <database>
    <host>localhost</host>
    <port>
5432</port>
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

Here's how to format HTML with proper block/inline classification and whitespace preservation in `<code>` and `<pre>` elements:

```python
def format_documentation_example(input_file: Path):
    """Format HTML with proper block/inline classification and whitespace preservation.

    This is the main Python API example shown in the README.

    Args:
        input_file: Path to the HTML file to format

    Returns:
        str: The formatted HTML output
    """
    # Create HTML5 formatter with custom whitespace handling
    # Html5Formatter includes sensible HTML5 defaults:
    # - Block elements: <div>, <p>, <ul>, <li>, <h1>-<h6>, etc. get newlines + indentation
    # - Inline elements: <em>, <strong>, <code>, <a>, etc. flow within text
    formatter = Html5Formatter(
        preserve_whitespace_when=tag_in("pre", "code"),  # Keep original spacing inside these
        indent_size=2,
    )

    # Load and format HTML from file
    formatted = formatter.format_file(input_file)
    return formatted
```

**Output:**
```html
<!DOCTYPE html>
<html>
  <body>
    <div>
      <h3>Documentation</h3>
      <p>Here are some spaced examples:</p>
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
  </body>
</html>
```

### Real-World Example

Here's Markuplift formatting a complex article structure with mixed content:

**Input** (`article_example.html`):
```html
<article><h1>Using   Markuplift</h1><section><h2>Code    Formatting</h2>
<p>Here's how to    use   our   API   with   proper   spacing:</p><pre><code>from markuplift import Formatter
formatter = Formatter(
    preserve_whitespace=True
)</code></pre><p>The   <em>preserve_whitespace</em>   feature   keeps
code   formatting   intact   while   <strong>normalizing</strong>   text
content!</p></section></article>
```

```python
def format_article_example(input_file: Path):
    """Format complex article structure with mixed content.

    This is the real-world example shown in the README demonstrating
    Html5Formatter with custom whitespace handling.

    Args:
        input_file: Path to the HTML file to format

    Returns:
        str: The formatted HTML output
    """
    # Html5Formatter provides HTML5-optimized defaults
    formatter = Html5Formatter(
        preserve_whitespace_when=tag_in("pre", "code"),
        normalize_whitespace_when=any_of(tag_in("p", "li", "h1", "h2", "h3"), html_inline_elements()),
        indent_size=2,
    )

    # Format real-world messy HTML directly from file
    formatted = formatter.format_file(input_file)
    return formatted
```

**Output:**
```html
<!DOCTYPE html>
<html>
  <body>
    <article>
      <h1>Using Markuplift</h1>
      <section>
        <h2>Code Formatting</h2>
        <p>Here's how to use our API with proper spacing:</p>
        <pre><code>from markuplift import Formatter formatter = Formatter( preserve_whitespace=True )</code></pre>
        <p>The <em>preserve_whitespace</em> feature keeps code formatting intact while <strong>normalizing</strong> text content!</p>
      </section>
    </article>
  </body>
</html>
```

### Parameterized Custom Predicates

You can create predicates that accept parameters, making them reusable for different situations. Here are examples that show how to customize formatting based on programming languages and CSS classes:

```python
def elements_with_attribute_values(attribute_name: str, *values: str) -> ElementPredicateFactory:
    """Factory for predicate matching elements with specific attribute values.

    This creates a predicate that matches elements where the specified attribute
    contains any of the given values. Useful for formatting based on element
    roles, types, or semantic meaning.

    Args:
        attribute_name: Name of the attribute to check (e.g., 'class', 'role', 'type')
        *values: Attribute values to match against

    Returns:
        ElementPredicateFactory that creates optimized predicates

    Example:
        >>> # Format table cells differently based on their role
        >>> formatter = Html5Formatter(
        ...     block_when=elements_with_attribute_values('role', 'header', 'columnheader')
        ... )

        >>> # Special handling for form elements by type
        >>> formatter = Html5Formatter(
        ...     wrap_attributes_when=elements_with_attribute_values('type', 'email', 'password', 'url')
        ... )
    """

    def create_document_predicate(root) -> ElementPredicate:
        # Pre-scan document to find all matching elements
        matching_elements = set()

        for element in root.iter():
            attr_value = element.get(attribute_name, "")
            if attr_value:
                # Check if any of the target values appear in the attribute
                attr_words = attr_value.lower().split()
                if any(value.lower() in attr_words for value in values):
                    matching_elements.add(element)

        def element_predicate(element) -> bool:
            return element in matching_elements

        return element_predicate

    return create_document_predicate

def table_cells_in_columns(*column_types: str) -> ElementPredicateFactory:
    """Factory for predicate matching table cells in columns with specific semantic types.

    This matches <td> or <th> elements that are in table columns designated for
    specific types of data (like 'price', 'date', 'name', etc.). Column types
    are determined by class attributes on the <col>, <th>, or <td> elements.

    Args:
        *column_types: Column type names to match (e.g., 'price', 'currency', 'date', 'number')

    Returns:
        ElementPredicateFactory that creates optimized predicates

    Example:
        >>> # Right-align numeric and currency columns
        >>> formatter = Html5Formatter(
        ...     wrap_attributes_when=table_cells_in_columns('price', 'currency', 'number')
        ... )

        >>> # Preserve formatting in date and time columns
        >>> formatter = Html5Formatter(
        ...     preserve_whitespace_when=table_cells_in_columns('date', 'time', 'timestamp')
        ... )
    """

    def create_document_predicate(root) -> ElementPredicate:
        matching_elements = set()

        # Find all tables and analyze their column structure
        for table in root.iter("table"):
            column_classes = []

            # Method 1: Check <col> elements for column classes
            colgroup = table.find("colgroup")
            if colgroup is not None:
                for col in colgroup.findall("col"):
                    col_class = col.get("class", "")
                    column_classes.append(col_class.lower().split())

            # Method 2: Check header row for column classes
            if not column_classes:
                thead = table.find("thead")
                if thead is not None:
                    header_row = thead.find("tr")
                    if header_row is not None:
                        for th in header_row.findall("th"):
                            th_class = th.get("class", "")
                            column_classes.append(th_class.lower().split())

            # If we found column structure, match cells in target columns
            if column_classes:
                for row in table.iter("tr"):
                    cells = row.findall("td") + row.findall("th")
                    for col_index, cell in enumerate(cells):
                        if col_index < len(column_classes):
                            cell_classes = column_classes[col_index]
                            # Also check the cell's own class attribute
                            cell_own_classes = cell.get("class", "").lower().split()
                            all_classes = cell_classes + cell_own_classes

                            # Check if any column type matches
                            if any(col_type.lower() in all_classes for col_type in column_types):
                                matching_elements.add(cell)

        def element_predicate(element) -> bool:
            return element in matching_elements

        return element_predicate

    return create_document_predicate
```

**Usage:**
```python
def format_complex_predicates_example(input_file: Path):
    """Format HTML using parameterized predicates for content-aware formatting.

    This example shows how to use predicates with parameters to apply different
    formatting rules based on semantic meaning and document structure.

    Args:
        input_file: Path to the HTML file to format

    Returns:
        str: The formatted HTML output
    """
    # Create formatter with parameterized predicate-based rules
    formatter = Html5Formatter(
        # Treat navigation and sidebar elements as block elements
        block_when=elements_with_attribute_values("role", "navigation", "complementary"),
        # Apply special formatting to currency and numeric table columns
        wrap_attributes_when=table_cells_in_columns("price", "currency", "number"),
        # Standard Html5Formatter defaults for other elements
        indent_size=2,
    )

    # Format the document with semantic-aware predicate rules
    formatted = formatter.format_file(input_file)
    return formatted
```

**Input** (`complex_predicates_example.html`):
```html
<nav role="navigation"><ul><li><a href="/">Home</a></li><li><a href="/
products">Products</a></li></ul></nav><main><h1>Product Catalog</h1>
<table><colgroup><col class="name"><col class="price"><col class="currency">
<col class="stock"></colgroup><thead><tr><th>Product</th><th>Price</th><th>
Currency</th><th>Stock</th></tr></thead><tbody><tr><td>Widget A</td><td>
19.99</td><td>USD</td><td>150</td></tr><tr><td>Widget B</td><td>29.99</td>
<td>EUR</td><td>75</td></tr></tbody></table></main><aside role="
complementary"><h2>Special Offers</h2><p>Check out our latest deals!</p>
<table><thead><tr><th class="product">Item</th><th class="discount">
Discount</th><th class="date">Valid Until</th></tr></thead><tbody><tr><td>
Premium Widget</td><td>20%</td><td>2024-12-31</td></tr></tbody></table>
</aside>
```

**Output:**
```html
<!DOCTYPE html>
<html>
  <body>
    <nav role="navigation">
      <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/
products">Products</a></li>
      </ul>
    </nav>
    <main>
      <h1>Product Catalog</h1>
      <table>
        <colgroup>
          <col class="name">
          <col class="price">
          <col class="currency">
          <col class="stock">
        </colgroup>
        <thead>
          <tr>
            <th>Product</th>
            <th>Price</th>
            <th> Currency</th>
            <th>Stock</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Widget A</td>
            <td> 19.99</td>
            <td>USD</td>
            <td>150</td>
          </tr>
          <tr>
            <td>Widget B</td>
            <td>29.99</td>
            <td>EUR</td>
            <td>75</td>
          </tr>
        </tbody>
      </table>
    </main>
    <aside role="
complementary">
      <h2>Special Offers</h2>
      <p>Check out our latest deals!</p>
      <table>
        <thead>
          <tr>
            <th class="product">Item</th>
            <th class="discount"> Discount</th>
            <th class="date">Valid Until</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td> Premium Widget</td>
            <td>20%</td>
            <td>2024-12-31</td>
          </tr>
        </tbody>
      </table>
    </aside>
  </body>
</html>
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
    return len([prop.strip() for prop in style_value.split(";") if prop.strip()])

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
    properties = [prop.strip() for prop in value.split(";") if prop.strip()]
    base_indent = formatter.one_indent * level
    property_indent = formatter.one_indent * (level + 1)
    formatted_props = [f"{property_indent}{prop}" for prop in properties]
    return "\n" + ";\n".join(formatted_props) + "\n" + base_indent

def format_attribute_formatting_example(input_file):
    """Format HTML with complex CSS styles using Html5Formatter.

    This example demonstrates attribute value formatting where CSS styles
    with 4 or more properties are formatted across multiple lines for
    better readability.

    Args:
        input_file: Path to the HTML file to format

    Returns:
        str: The formatted HTML output
    """
    from markuplift import Html5Formatter
    from markuplift.predicates import html_block_elements

    # Format HTML with complex CSS styles using Html5Formatter
    formatter = Html5Formatter(
        reformat_attribute_when={
            # Only format styles with 4+ CSS properties
            html_block_elements().with_attribute("style", lambda v: num_css_properties(v) >= 4): css_multiline_formatter
        }
    )

    # Format HTML file with attribute formatting
    formatted = formatter.format_file(input_file)
    return formatted
```

**Output:**
```html
<!DOCTYPE html>
<html>
  <body>
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
  </body>
</html>
```

### XML Document Formatting

For XML documents, use `XmlFormatter` which provides XML-strict parsing and escaping:

```python
def format_xml_document_example(input_file: Path):
    """Format XML document with custom structure using XmlFormatter.

    This demonstrates XmlFormatter with XML-strict parsing and escaping,
    showing how to define custom XML element classifications.

    Args:
        input_file: Path to the XML file to format

    Returns:
        str: The formatted XML output
    """
    # Define custom XML structure with ElementType enum
    formatter = XmlFormatter(
        block_when=tag_in("document", "section", "paragraph", "metadata"),
        inline_when=tag_in("emphasis", "code", "link"),
        preserve_whitespace_when=tag_in("code-block", "verbatim"),
        default_type=ElementType.BLOCK,  # Use enum for type safety
        indent_size=2,
    )

    # Format the XML document
    formatted = formatter.format_file(input_file)
    return formatted
```

**Input** (`xml_document_example.xml`):
```xml
<document><metadata><title>API Reference</title><version>2.1</version></metadata>
<section><paragraph>This API provides <emphasis>robust</emphasis> data
processing with <code>xml.parse()</code> methods.</paragraph>
<code-block>
import xml.etree.ElementTree as ET
root = ET.parse('data.xml').getroot()
</code-block></section></document>
```

**Output:**
```xml
<document>
  <metadata>
    <title>API Reference</title>
    <version>2.1</version>
  </metadata>
  <section>
    <paragraph>This API provides <emphasis>robust</emphasis> data
processing with <code>xml.parse()</code> methods.</paragraph>
    <code-block>
import xml.etree.ElementTree as ET
root = ET.parse('data.xml').getroot()
</code-block>
  </section>
</document>
```

## Choosing the Right Formatter

- **`Html5Formatter`** - For HTML documents. Includes sensible HTML5 defaults for block/inline elements, HTML5-compliant parsing, and HTML-friendly escaping
- **`XmlFormatter`** - For XML documents. Provides strict XML compliance, XML-compliant escaping, and no assumptions about element types
- **`Formatter`** - For advanced use cases requiring full control over parsing and escaping strategies

## Use Cases

Markuplift is perfect for:

- **Web development** - Format HTML templates and components with `Html5Formatter` for consistent styling and HTML5 compliance
- **API documentation** - Use `XmlFormatter` for XML API specs and configuration files with strict validation
- **Content management** - Standardize markup in CMS systems with custom element classification rules
- **Code generation** - Format dynamically generated XML/HTML with precise control using `ElementType` enums
- **CI/CD pipelines** - Ensure consistent markup formatting across your codebase with CLI integration
- **Legacy system migration** - Clean up and standardize markup from legacy systems with flexible predicate rules
- **Static site generation** - Format template files and generated content with specialized formatters
- **Diffing and version control** - Improve readability of markup changes with consistent formatting

## License

Markuplift is released under the [MIT License](https://github.com/rob-smallshire/markuplift/blob/master/LICENSE).

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Setting up the development environment
- Running tests and linting
- Submitting pull requests
- Reporting issues