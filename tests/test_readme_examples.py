"""Tests for examples shown in README.md.

This ensures that all examples in the README are accurate and working.
"""

from markuplift import Formatter
from markuplift.predicates import html_block_elements, html_inline_elements


class TestReadmeExamples:
    """Test all examples from README.md to ensure accuracy."""

    def test_python_api_nested_list_example(self):
        """Test the Python API nested list example from README."""
        # This is the exact example from the README
        formatter = Formatter(
            block_predicate_factory=html_block_elements(),
            inline_predicate_factory=html_inline_elements(),
            indent_size=2
        )

        # Format complex nested HTML (minified input)
        messy_html = '<ul><li>Getting Started<ul><li>Installation via <code>pip install markuplift</code></li><li>Basic <em>configuration</em> and setup</li></ul></li><li>Advanced Features<ul><li>Custom <strong>predicates</strong> and XPath</li><li>External formatter <code>integration</code></li></ul></li></ul>'
        formatted = formatter.format_str(messy_html)

        expected_output = """<ul>
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
</ul>"""

        assert formatted.strip() == expected_output.strip()

    def test_real_world_article_example(self):
        """Test the real-world article example from README."""
        # Real-world messy HTML (imagine this came from a CMS or generator)
        messy_html = '<article><h1>Using Markuplift</h1><section><h2>Introduction</h2><p>Markuplift is a <em>powerful</em> formatter for <strong>XML and HTML</strong>.</p><p>Key features include:</p><ul><li>Configurable <code>block</code> and <code>inline</code> elements</li><li>XPath-based element selection</li><li>Custom text formatters for <pre><code>code blocks</code></pre></li></ul></section></article>'

        formatter = Formatter(
            block_predicate_factory=html_block_elements(),
            inline_predicate_factory=html_inline_elements(),
            indent_size=2
        )

        formatted = formatter.format_str(messy_html)

        expected_output = """<article>
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
</article>"""

        assert formatted.strip() == expected_output.strip()

    def test_advanced_form_example(self):
        """Test the advanced HTML form example from README."""
        # HTML form structure (typical from form builders)
        messy_form = '<form><fieldset><legend>User Information</legend><div><label>Name: <input type="text" name="name" required="required"/></label></div><div><label>Email: <input type="email" name="email"/></label></div><div><label><input type="checkbox" name="subscribe"/> Subscribe to <em>newsletter</em></label></div></fieldset><button type="submit">Submit <strong>Form</strong></button></form>'

        formatter = Formatter(
            block_predicate_factory=html_block_elements(),
            inline_predicate_factory=html_inline_elements(),
            indent_size=2
        )

        formatted = formatter.format_str(messy_form)

        expected_output = """<form>
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
</form>"""

        assert formatted.strip() == expected_output.strip()

    def test_block_inline_classification(self):
        """Test that our examples correctly demonstrate block vs inline element handling."""
        formatter = Formatter(
            block_predicate_factory=html_block_elements(),
            inline_predicate_factory=html_inline_elements(),
            indent_size=2
        )

        # Test specific element classification used in our examples
        test_html = '<ul><li>Text with <em>inline</em> and <strong>more inline</strong> <code>code</code></li></ul>'
        formatted = formatter.format_str(test_html)

        # ul and li should be block (indented), em/strong/code should be inline (same line)
        expected = """<ul>
  <li>Text with <em>inline</em> and <strong>more inline</strong> <code>code</code></li>
</ul>"""

        assert formatted.strip() == expected.strip()

    def test_mixed_content_in_lists(self):
        """Test the specific case mentioned: li with both text and sublist."""
        formatter = Formatter(
            block_predicate_factory=html_block_elements(),
            inline_predicate_factory=html_inline_elements(),
            indent_size=2
        )

        # This tests the exact scenario the user mentioned
        test_html = '<ol><li>Item with text <ul><li>Subitem</li></ul></li></ol>'
        formatted = formatter.format_str(test_html)

        expected = """<ol>
  <li>Item with text
    <ul>
      <li>Subitem</li>
    </ul>
  </li>
</ol>"""

        assert formatted.strip() == expected.strip()