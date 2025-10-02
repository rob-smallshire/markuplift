"""Integration test for SVG reparsing in HTML documents.

This test verifies the complete fix for the issue where Html5Formatter would fail
on HTML documents containing SVG elements with namespaced attributes (like bx:grid).

The issue was that:
1. HTML parsers strip namespaces, making attributes like 'bx:grid' into literal strings
2. When trying to format these, etree.QName() would fail with "Invalid tag name"
3. The solution is to reparse SVG elements as XML using parse_as_xml_when
4. But the original SimpleTagScanner used expat, which can't parse HTML5 syntax

This test verifies that the new Html5TagScanner correctly:
- Handles HTML5 void elements (meta, link, etc.)
- Handles self-closing SVG elements (rect, path, etc.)
- Locates SVG elements in HTML documents
- Allows SVG reparsing with namespace preservation
"""

from pathlib import Path

import pytest

from markuplift.html5_formatter import Html5Formatter
from markuplift.predicates import tag_in


class TestSVGReparsingIntegration:
    """Test SVG reparsing in HTML documents."""

    def test_html_with_svg_namespaced_attributes(self):
        """Test the complete user scenario that was failing."""
        # This is the actual HTML file that was causing the issue
        test_file = Path(__file__).parent / "data" / "html_with_svg.html"
        html_source = test_file.read_text()

        # Create formatter configured to reparse SVG as XML
        formatter = Html5Formatter(parse_as_xml_when=tag_in("svg"))

        # This should now work without errors
        formatted = formatter.format_str(html_source)

        # Verify namespaced attributes are preserved
        assert 'xmlns:bx="https://boxy-svg.com"' in formatted
        assert "<bx:grid" in formatted
        assert 'bx:pinned="true"' in formatted

    def test_simple_svg_in_html(self):
        """Test a simpler case with SVG in HTML."""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SVG Test</title>
</head>
<body>
    <svg xmlns="http://www.w3.org/2000/svg" xmlns:custom="https://example.com">
        <custom:element attr="value"/>
        <rect x="0" y="0" width="100" height="100"/>
    </svg>
</body>
</html>"""

        formatter = Html5Formatter(parse_as_xml_when=tag_in("svg"))
        formatted = formatter.format_str(html)

        # Verify namespaced elements are preserved
        assert 'xmlns:custom="https://example.com"' in formatted
        assert "<custom:element" in formatted

    def test_html5_void_elements_dont_break_scanner(self):
        """Test that HTML5 void elements don't prevent SVG scanning."""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width">
    <link rel="stylesheet" href="style.css">
    <link rel="icon" href="favicon.ico">
</head>
<body>
    <img src="image.jpg" alt="test">
    <br>
    <hr>
    <input type="text" name="test">
    <svg xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0"/>
    </svg>
</body>
</html>"""

        formatter = Html5Formatter(parse_as_xml_when=tag_in("svg"))
        formatted = formatter.format_str(html)

        # Should format without errors
        assert "<svg" in formatted
        assert "<rect" in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
