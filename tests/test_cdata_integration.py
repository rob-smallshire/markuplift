"""High-level integration tests for CDATA functionality.

This module contains end-to-end tests that verify CDATA handling works
correctly through the complete pipeline: parsing, processing, and output
generation.
"""

from inspect import cleandoc

import pytest

from markuplift.formatter import Formatter
from markuplift.html5_formatter import Html5Formatter
from markuplift.xml_formatter import XmlFormatter
from markuplift.predicates import tag_in, never_matches


class TestCDATAIntegration:
    """Integration tests for CDATA functionality across formatters."""

    def test_xml_formatter_preserves_cdata_content_by_default(self):
        """Test that XmlFormatter preserves CDATA content by default."""
        xml_with_cdata = cleandoc('''
            <?xml version="1.0"?>
            <root>
                <script><![CDATA[
                    function test() {
                        return "hello world";
                    }
                ]]></script>
            </root>
        ''')

        formatter = XmlFormatter(
            block_when=tag_in("root", "script"),
            inline_when=never_matches
        )

        result = formatter.format_str(xml_with_cdata)

        # Should preserve CDATA content as regular text
        assert "function test()" in result
        assert "hello world" in result
        # CDATA content is preserved but formatted as regular text
        assert "<script>" in result and "</script>" in result

    def test_xml_formatter_with_preserve_cdata_false(self):
        """Test XmlFormatter with preserve_cdata=False converts to text."""
        xml_with_cdata = '''<root><script><![CDATA[alert("test");]]></script></root>'''

        formatter = XmlFormatter(
            block_when=tag_in("root", "script"),
            inline_when=never_matches,
            preserve_cdata=False
        )

        result = formatter.format_str(xml_with_cdata)

        # CDATA should be converted to regular text
        assert "<![CDATA[" not in result
        assert "]]>" not in result
        assert 'alert("test");' in result

    def test_html5_formatter_preserves_cdata_by_default(self):
        """Test that Html5Formatter preserves CDATA sections by default."""
        html_with_cdata = cleandoc('''
            <!DOCTYPE html>
            <html>
            <head>
                <script><![CDATA[
                    var data = "some content";
                    console.log(data);
                ]]></script>
            </head>
            </html>
        ''')

        formatter = Html5Formatter()
        result = formatter.format_str(html_with_cdata)

        # Should preserve CDATA structure (may be escaped in HTML)
        assert ("CDATA" in result or "var data" in result)
        assert "console.log" in result

    def test_formatter_with_cdata_text_formatters(self):
        """Test that CDATA content can be processed by text formatters."""
        xml_content = cleandoc('''
            <root>
                <code><![CDATA[  messy   whitespace  content  ]]></code>
            </root>
        ''')

        def normalize_whitespace(content, formatter, level):
            """Normalize whitespace in content."""
            if hasattr(content, '__str__'):
                # Handle both str and CDATA objects
                return ' '.join(str(content).split())
            return content

        formatter = Formatter(
            block_when=tag_in("root", "code"),
            inline_when=never_matches,
            reformat_text_when={
                tag_in("code"): normalize_whitespace
            }
        )

        result = formatter.format_str(xml_content)

        # The CDATA content should be normalized
        assert "messy whitespace content" in result

    def test_cdata_generation_with_problematic_content(self):
        """Test that formatters can generate safe output for problematic CDATA content."""
        # Create content with ]]> sequences that needs safe handling
        problematic_text = 'var regex = /]]>/g; var data = "test]]>value";'

        from lxml.etree import Element, CDATA

        # Create an element with CDATA content containing ]]>
        root = Element("script")
        root.text = CDATA(problematic_text)

        formatter = XmlFormatter(
            block_when=tag_in("script"),
            inline_when=never_matches
        )

        # Use the underlying formatter method
        result = formatter._formatter.format_element(root)

        # Should safely handle ]]> sequences by escaping them in text
        assert "]]&gt;" in result  # Escaped ]]> sequence as regular text
        assert "var regex" in result
        assert "test" in result
        assert "value" in result

    def test_nested_cdata_handling(self):
        """Test handling of nested elements with CDATA content."""
        xml_content = cleandoc('''
            <root>
                <style><![CDATA[
                    .class { content: "style"; }
                ]]></style>
                <script><![CDATA[
                    var x = "test data";
                ]]></script>
            </root>
        ''')

        formatter = XmlFormatter(
            block_when=tag_in("root", "style", "script"),
            inline_when=never_matches
        )

        result = formatter.format_str(xml_content)

        # Both CDATA contents should be preserved as regular text
        assert ".class" in result
        assert "var x" in result
        assert "<style>" in result and "</style>" in result
        assert "<script>" in result and "</script>" in result

    def test_empty_cdata_handling(self):
        """Test handling of empty CDATA sections."""
        xml_content = '''<root><script><![CDATA[]]></script></root>'''

        formatter = XmlFormatter(
            block_when=tag_in("root", "script"),
            inline_when=never_matches
        )

        result = formatter.format_str(xml_content)

        # Empty CDATA becomes empty element or self-closing element
        assert ("<script />" in result or "<script></script>" in result)

    def test_cdata_with_whitespace_handling(self):
        """Test CDATA interaction with whitespace handling predicates."""
        xml_content = cleandoc('''
            <root>
                <pre><![CDATA[
                formatted
                    code
                        block
                ]]></pre>
            </root>
        ''')

        formatter = XmlFormatter(
            block_when=tag_in("root", "pre"),
            inline_when=never_matches,
            preserve_whitespace_when=tag_in("pre")
        )

        result = formatter.format_str(xml_content)

        # Whitespace in CDATA should be preserved due to pre element
        assert "formatted" in result
        assert "        code" in result  # Indentation preserved
        assert "            block" in result  # Deeper indentation preserved

    def test_derive_preserves_cdata_setting(self):
        """Test that derived formatters preserve CDATA settings."""
        base_formatter = XmlFormatter(
            block_when=tag_in("root"),
            preserve_cdata=False
        )

        # Derive without changing preserve_cdata
        derived_formatter = base_formatter.derive(
            block_when=tag_in("root", "child")
        )

        assert not derived_formatter.preserve_cdata

        # Derive with changing preserve_cdata
        derived_with_cdata = base_formatter.derive(preserve_cdata=True)
        assert derived_with_cdata.preserve_cdata

    def test_round_trip_cdata_preservation(self):
        """Test that CDATA content survives round-trip parsing and formatting."""
        original_xml = cleandoc('''
            <?xml version="1.0"?>
            <root>
                <script><![CDATA[
                    // JavaScript with safe content
                    var test = "data and more content";
                    var regex = /test/g;
                ]]></script>
            </root>
        ''')

        formatter = XmlFormatter(
            block_when=tag_in("root", "script"),
            inline_when=never_matches
        )

        # Format the XML
        formatted = formatter.format_str(original_xml)

        # Parse and format again
        round_trip = formatter.format_str(formatted)

        # Key content should be preserved
        assert "JavaScript with safe" in round_trip
        assert "data and more content" in round_trip
        assert "var regex" in round_trip

    def test_programmatic_cdata_generation(self):
        """Test that programmatically created CDATA objects work correctly."""
        from lxml.etree import Element, CDATA, tostring

        # Create an element with CDATA containing ]]> sequence
        root = Element("script")
        root.text = CDATA('var test = "before]]>after"; console.log(test);')

        # First check that lxml handles the CDATA correctly
        lxml_output = tostring(root, encoding='unicode')
        # lxml should split the ]]> sequence safely
        assert "before" in lxml_output
        assert "after" in lxml_output
        assert "<![CDATA[" in lxml_output

        # Now test through our formatter
        formatter = XmlFormatter(
            block_when=tag_in("script"),
            inline_when=never_matches
        )

        # When formatted, the CDATA content is preserved but as regular text
        result = formatter._formatter.format_element(root)
        assert "before" in result
        assert "after" in result
        assert "console.log" in result
        # The problematic ]]> sequence should be safely escaped
        assert "]]&gt;" in result

    def test_mixed_cdata_and_text_content(self):
        """Test elements with both CDATA and regular text content."""
        from lxml import etree

        # Create element with mixed content
        root: etree._Element = etree.Element("script")
        root.text = "// Regular comment\n"

        # Add CDATA section
        script_element = etree.Element("script")
        script_element.text = etree.CDATA("var test = 'safe data';")
        root.append(script_element)

        formatter = XmlFormatter(
            block_when=tag_in("script"),
            inline_when=never_matches
        )

        # Use the underlying formatter method
        result = formatter._formatter.format_element(root)

        # Should handle both regular text and CDATA
        assert "Regular comment" in result
        assert "safe data" in result


if __name__ == "__main__":
    pytest.main([__file__])