"""Tests for XmlFormatter convenience class.

This ensures that the XmlFormatter works correctly and provides
XML-strict parsing and escaping behavior.
"""

import pytest
from io import BytesIO
from markuplift import XmlFormatter, Formatter
from markuplift.predicates import tag_in
from markuplift.escaping import XmlEscapingStrategy
from markuplift.parsing import XmlParsingStrategy
from examples.attribute_formatters import num_css_properties, css_multiline_formatter


class TestXmlFormatter:
    """Test XmlFormatter convenience class."""

    def test_xml_formatter_uses_xml_strategies(self):
        """Test that XmlFormatter uses XML-specific strategies."""
        formatter = XmlFormatter()

        # Access the internal formatter to check strategies
        internal_formatter = formatter._formatter
        assert isinstance(internal_formatter._escaping_strategy, XmlEscapingStrategy)
        assert isinstance(internal_formatter._parsing_strategy, XmlParsingStrategy)

    def test_xml_formatter_attribute_escaping(self):
        """Test that XmlFormatter uses XML-strict attribute escaping."""
        formatter = XmlFormatter(
            reformat_attribute_when={
                tag_in("p").with_attribute("style", lambda v: num_css_properties(v) >= 4): css_multiline_formatter
            }
        )

        xml = '<p style="color: green; background: black; margin: 10px; padding: 5px;">Complex</p>'
        result = formatter.format_str(xml)

        # Should contain &#10; entities, not literal newlines
        assert '&#10;' in result
        assert '\n  color: green;' not in result

    def test_xml_formatter_strict_parsing(self):
        """Test that XmlFormatter requires well-formed XML."""
        formatter = XmlFormatter()

        # Well-formed XML should work
        xml = '<root><child>content</child></root>'
        result = formatter.format_str(xml)
        assert '<root>' in result

        # Malformed XML should raise an exception
        malformed_xml = '<root><child>content</root>'  # Missing closing tag
        with pytest.raises(Exception):  # Will be XMLSyntaxError from lxml
            formatter.format_str(malformed_xml)

    def test_xml_formatter_no_doctype_addition(self):
        """Test that XmlFormatter doesn't add DOCTYPE declarations."""
        formatter = XmlFormatter()

        xml = '<root>content</root>'
        result = formatter.format_str(xml)

        # XML parser should not add DOCTYPE
        assert 'DOCTYPE' not in result

    def test_xml_formatter_delegation(self):
        """Test that XmlFormatter properly delegates all methods."""
        formatter = XmlFormatter(block_when=tag_in("div"))

        # Test all public methods exist and work
        xml = '<div>test</div>'

        # format_str
        str_result = formatter.format_str(xml)
        assert '<div>' in str_result

        # format_bytes
        bytes_result = formatter.format_bytes(xml.encode())
        assert '<div>' in bytes_result

        # format_tree (need to create a tree first)
        from lxml import etree
        tree = etree.parse(BytesIO(xml.encode()))
        tree_result = formatter.format_tree(tree)
        assert '<div>' in tree_result

    def test_xml_formatter_vs_regular_formatter(self):
        """Test that XmlFormatter behaves identically to regular Formatter."""
        xml_formatter = XmlFormatter(
            reformat_attribute_when={
                tag_in("p").with_attribute("style", lambda v: num_css_properties(v) >= 4): css_multiline_formatter
            }
        )

        regular_formatter = Formatter(
            reformat_attribute_when={
                tag_in("p").with_attribute("style", lambda v: num_css_properties(v) >= 4): css_multiline_formatter
            }
        )

        test_xml = '<p style="color: green; background: black; margin: 10px; padding: 5px;">Test</p>'

        xml_result = xml_formatter.format_str(test_xml)
        regular_result = regular_formatter.format_str(test_xml)

        # Both should produce identical results (XML escaping by default)
        assert xml_result == regular_result
        assert '&#10;' in xml_result
        assert '\n  color: green;' not in xml_result

    def test_xml_formatter_backward_compatibility(self):
        """Test that existing Formatter behavior is preserved."""
        old_formatter = Formatter()
        xml_formatter = XmlFormatter()

        # These should produce identical results for well-formed XML
        xml = '<root><child attr="value">content</child></root>'

        old_result = old_formatter.format_str(xml)
        xml_result = xml_formatter.format_str(xml)

        assert old_result == xml_result

    def test_xml_formatter_strict_error_handling(self):
        """Test that XmlFormatter properly handles XML parsing errors."""
        formatter = XmlFormatter()

        # Test various malformed XML cases
        test_cases = [
            '<root><unclosed>',  # Unclosed tag
            '<root><child></root>',  # Mismatched tags
            '<root>text & more</root>',  # Unescaped ampersand
            '<root><child attr="unclosed>content</child></root>',  # Unclosed attribute
        ]

        for malformed_xml in test_cases:
            with pytest.raises(Exception):  # XMLSyntaxError from lxml
                formatter.format_str(malformed_xml)

    def test_xml_formatter_with_xml_declaration(self):
        """Test that XmlFormatter handles XML declarations properly."""
        formatter = XmlFormatter()

        xml = '<root>content</root>'

        # Test without XML declaration
        result_no_decl = formatter.format_str(xml)
        assert '<?xml' not in result_no_decl

        # Test with XML declaration
        result_with_decl = formatter.format_str(xml, xml_declaration=True)
        assert '<?xml version="1.0"' in result_with_decl

        # Test with explicit False
        result_explicit_false = formatter.format_str(xml, xml_declaration=False)
        assert '<?xml' not in result_explicit_false

    def test_xml_formatter_namespace_handling(self):
        """Test that XmlFormatter handles XML namespaces properly."""
        formatter = XmlFormatter()

        xml_with_ns = '''<root xmlns:ns="http://example.com">
            <ns:child>content</ns:child>
        </root>'''

        result = formatter.format_str(xml_with_ns)
        # lxml expands namespaces, so we look for the expanded form
        assert 'http://example.com' in result
        assert 'child>content' in result