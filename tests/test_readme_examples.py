"""Tests for examples shown in README.md.

This ensures that all examples in the README are accurate and working.
"""

from inspect import cleandoc

from approvaltests import verify
from markuplift import Formatter
from markuplift.predicates import html_block_elements, html_inline_elements, tag_in, any_of
from examples.attribute_formatters import format_attribute_formatting_example
from examples.python_api_basic import format_documentation_example
from examples.real_world_article import format_article_example
from examples.complex_predicates import elements_with_attribute_values, table_cells_in_columns
from examples.complex_predicates_usage import format_complex_predicates_example
from examples.xml_document_formatting import format_xml_document_example


class TestReadmeExamples:
    """Test all examples from README.md to ensure accuracy."""

    def test_python_api_nested_list_example(self, test_data_path):
        """Test the Python API example with whitespace preservation from README."""
        # Execute the actual example function from the examples module
        input_file = test_data_path("readme_examples/documentation_example.html")
        formatted = format_documentation_example(input_file)
        verify(formatted)

    def test_real_world_article_example(self, test_data_path):
        """Test the real-world article example with normalize and preserve whitespace from README."""
        # Execute the actual example function from the examples module
        input_file = test_data_path("readme_examples/article_example.html")
        formatted = format_article_example(input_file)
        verify(formatted)

    def test_advanced_form_example(self, test_data_path):
        """Test the advanced example with comprehensive whitespace control from README."""
        formatter = Formatter(
            block_when=html_block_elements(),
            inline_when=html_inline_elements(),
            preserve_whitespace_when=tag_in("pre", "code", "textarea"),
            normalize_whitespace_when=any_of(tag_in("p", "li", "h1", "h2", "h3"), html_inline_elements()),
            indent_size=2,
        )

        # Load input from data file
        html_file = test_data_path("readme_examples/form_example.html")
        with open(html_file) as f:
            messy_html = f.read()

        formatted = formatter.format_str(messy_html)
        verify(formatted)

    def test_block_inline_classification(self):
        """Test that our examples correctly demonstrate block vs inline element handling."""
        formatter = Formatter(block_when=html_block_elements(), inline_when=html_inline_elements(), indent_size=2)

        # Test specific element classification used in our examples
        test_html = "<ul><li>Text with <em>inline</em> and <strong>more inline</strong> <code>code</code></li></ul>"
        formatted = formatter.format_str(test_html)

        # ul and li should be block (indented), em/strong/code should be inline (same line)
        expected = cleandoc("""
            <ul>
              <li>Text with <em>inline</em> and <strong>more inline</strong> <code>code</code></li>
            </ul>
        """)

        assert formatted.strip() == expected.strip()

    def test_mixed_content_in_lists(self):
        """Test the specific case mentioned: li with both text and sublist."""
        formatter = Formatter(block_when=html_block_elements(), inline_when=html_inline_elements(), indent_size=2)

        # This tests the exact scenario the user mentioned
        test_html = "<ol><li>Item with text <ul><li>Subitem</li></ul></li></ol>"
        formatted = formatter.format_str(test_html)

        expected = cleandoc("""
            <ol>
              <li>Item with text
                <ul>
                  <li>Subitem</li>
                </ul>
              </li>
            </ol>
        """)

        assert formatted.strip() == expected.strip()

    def test_complex_predicates_example(self, test_data_path):
        """Test the complex predicates example from README."""
        # Execute the actual example function from the examples module
        input_file = test_data_path("readme_examples/complex_predicates_example.html")
        formatted = format_complex_predicates_example(input_file)
        verify(formatted)

    def test_xml_document_formatting_example(self, test_data_path):
        """Test the XML document formatting example from README."""
        # Execute the actual example function from the examples module
        input_file = test_data_path("readme_examples/xml_document_example.xml")
        formatted = format_xml_document_example(input_file)
        verify(formatted)

    def test_complex_predicate_functionality(self):
        """Test that parameterized predicates work correctly with document structure."""
        # Test that the parameterized predicates can be created without errors
        attr_predicate_factory = elements_with_attribute_values("role", "navigation", "complementary")
        table_predicate_factory = table_cells_in_columns("price", "currency")

        # These should be callable and return functions
        assert callable(attr_predicate_factory)
        assert callable(table_predicate_factory)

        # Test with a simple document structure
        from lxml import etree
        from io import StringIO

        simple_doc = """<html><body>
            <nav role="navigation">
                <ul><li><a href="/">Home</a></li></ul>
            </nav>
            <table>
                <colgroup>
                    <col class="name" />
                    <col class="price" />
                </colgroup>
                <tr><td>Product</td><td>$19.99</td></tr>
            </table>
        </body></html>"""

        tree = etree.parse(StringIO(simple_doc))
        root = tree.getroot()

        # Create predicates for this document
        attr_predicate = attr_predicate_factory(root)
        table_predicate = table_predicate_factory(root)

        assert callable(attr_predicate)
        assert callable(table_predicate)

    def test_attribute_formatting_example(self, test_data_path):
        """Test the attribute formatting example from README."""
        # Execute the actual example function from the examples module
        input_file = test_data_path("readme_examples/attribute_formatting_example.html")
        formatted = format_attribute_formatting_example(input_file)
        verify(formatted)
