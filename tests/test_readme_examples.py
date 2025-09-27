"""Tests for examples shown in README.md.

This ensures that all examples in the README are accurate and working.
"""

from approvaltests import verify
from markuplift import Formatter
from markuplift.predicates import html_block_elements, html_inline_elements, tag_in, any_of
from examples.css_class_predicates import has_css_class
from examples.attribute_formatters import num_css_properties, css_multiline_formatter


class TestReadmeExamples:
    """Test all examples from README.md to ensure accuracy."""

    def test_python_api_nested_list_example(self, test_data_path):
        """Test the Python API example with whitespace preservation from README."""
        # This is the exact example from the README
        formatter = Formatter(
            block_when=html_block_elements(),
            inline_when=html_inline_elements(),
            preserve_whitespace_when=tag_in("pre", "code"),
            indent_size=2
        )

        # Load input from data file
        html_file = test_data_path("readme_examples/documentation_example.html")
        with open(html_file) as f:
            messy_html = f.read()

        formatted = formatter.format_str(messy_html)
        verify(formatted)

    def test_real_world_article_example(self, test_data_path):
        """Test the real-world article example with normalize and preserve whitespace from README."""
        formatter = Formatter(
            block_when=html_block_elements(),
            inline_when=html_inline_elements(),
            preserve_whitespace_when=tag_in("pre", "code"),
            normalize_whitespace_when=any_of(tag_in("p", "li", "h1", "h2", "h3"), html_inline_elements()),
            indent_size=2
        )

        # Load input from data file
        html_file = test_data_path("readme_examples/article_example.html")
        with open(html_file) as f:
            messy_html = f.read()

        formatted = formatter.format_str(messy_html)
        verify(formatted)

    def test_advanced_form_example(self, test_data_path):
        """Test the advanced example with comprehensive whitespace control from README."""
        formatter = Formatter(
            block_when=html_block_elements(),
            inline_when=html_inline_elements(),
            preserve_whitespace_when=tag_in("pre", "code", "textarea"),
            normalize_whitespace_when=any_of(tag_in("p", "li", "h1", "h2", "h3"), html_inline_elements()),
            indent_size=2
        )

        # Load input from data file
        html_file = test_data_path("readme_examples/form_example.html")
        with open(html_file) as f:
            messy_html = f.read()

        formatted = formatter.format_str(messy_html)
        verify(formatted)

    def test_block_inline_classification(self):
        """Test that our examples correctly demonstrate block vs inline element handling."""
        formatter = Formatter(
            block_when=html_block_elements(),
            inline_when=html_inline_elements(),
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
            block_when=html_block_elements(),
            inline_when=html_inline_elements(),
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

    def test_custom_css_class_predicate_example(self, test_data_path):
        """Test the custom CSS class predicate example from README."""
        # Test the exact usage example from README
        formatter = Formatter(
            block_when=html_block_elements(),
            inline_when=html_inline_elements(),
            preserve_whitespace_when=has_css_class("code-block"),
            normalize_whitespace_when=any_of(has_css_class("prose"), html_inline_elements()),
            indent_size=2
        )

        # Load input from data file
        html_file = test_data_path("readme_examples/css_class_example.html")
        with open(html_file) as f:
            html = f.read()

        formatted = formatter.format_str(html)
        verify(formatted)

    def test_custom_predicate_validation(self):
        """Test validation in the custom CSS class predicate example."""
        from markuplift.predicates import PredicateError
        import pytest

        # Test empty class name validation
        with pytest.raises(PredicateError, match="CSS class name cannot be empty"):
            has_css_class("")

        with pytest.raises(PredicateError, match="CSS class name cannot be empty"):
            has_css_class("   ")

        # Test spaces in class name validation
        with pytest.raises(PredicateError, match="CSS class name cannot contain spaces"):
            has_css_class("class with spaces")

    def test_attribute_formatting_example(self, test_data_path):
        """Test the attribute formatting example from README."""
        # Format HTML with complex CSS styles
        formatter = Formatter(
            block_when=html_block_elements(),
            reformat_attribute_when={
                # Only format styles with 4+ CSS properties using function matcher
                html_block_elements().with_attribute("style", lambda v: num_css_properties(v) >= 4): css_multiline_formatter
            }
        )

        # Load input from data file
        html_file = test_data_path("readme_examples/attribute_formatting_example.html")
        with open(html_file) as f:
            html = f.read()

        formatted = formatter.format_str(html.strip())
        verify(formatted)