"""Tests for Html5TagScanner."""

from pathlib import Path

import pytest

from markuplift.source_locator import Html5TagScanner, XmlTagScanner, SimpleTagScanner


class TestHtml5TagScanner:
    """Test Html5TagScanner with HTML5-specific syntax."""

    def test_simple_html5_document(self):
        """Test scanning a simple HTML5 document with void elements."""
        html = b"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>Title</h1>
</body>
</html>"""

        scanner = Html5TagScanner(html)

        # Find the html element (root)
        html_range = scanner.find_element_range([0])
        assert html_range is not None
        start, end = html_range
        assert html[start:end].startswith(b'<html>')
        assert html[start:end].endswith(b'</html>')

    def test_nested_svg_in_html(self):
        """Test finding SVG element nested in HTML."""
        html = b"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <div>
        <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
            <rect x="0" y="0" width="50" height="50"/>
        </svg>
    </div>
</body>
</html>"""

        scanner = Html5TagScanner(html)

        # Path to svg: html[0] -> body[1] -> div[0] -> svg[0]
        svg_range = scanner.find_element_range([0, 1, 0, 0])
        assert svg_range is not None
        start, end = svg_range
        svg_content = html[start:end]
        assert svg_content.startswith(b'<svg')
        assert svg_content.endswith(b'</svg>')
        assert b'xmlns="http://www.w3.org/2000/svg"' in svg_content

    def test_html_with_svg_namespaced_attributes(self):
        """Test the actual problematic HTML file with namespaced SVG attributes."""
        test_file = Path(__file__).parent / "data" / "html_with_svg.html"
        html_bytes = test_file.read_bytes()

        scanner = Html5TagScanner(html_bytes)

        # Find the html element
        html_range = scanner.find_element_range([0])
        assert html_range is not None

        # Find the body element: html[0] -> body[1]
        body_range = scanner.find_element_range([0, 1])
        assert body_range is not None

        # Find the svg element: html[0] -> body[1] -> article[1] -> section[0] -> svg[0]
        # Note: article is the second child of body (index 1), not first, because there's a div before it
        svg_range = scanner.find_element_range([0, 1, 1, 0, 0])
        assert svg_range is not None
        start, end = svg_range
        svg_content = html_bytes[start:end]

        # Verify we got the SVG element
        assert svg_content.startswith(b'<svg')
        assert svg_content.endswith(b'</svg>')

        # Verify it contains the namespaced attributes
        assert b'xmlns:bx="https://boxy-svg.com"' in svg_content
        assert b'<bx:grid' in svg_content
        assert b'bx:pinned="true"' in svg_content

    def test_xml_scanner_fails_on_html5_syntax(self):
        """Verify that XmlTagScanner fails on HTML5 void elements."""
        html = b"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <h1>Title</h1>
</body>
</html>"""

        scanner = XmlTagScanner(html)

        # Should return None because it can't parse HTML5 syntax
        result = scanner.find_element_range([0])
        assert result is None

    def test_html5_scanner_handles_void_elements(self):
        """Test that Html5TagScanner correctly handles various void elements."""
        html = b"""<!DOCTYPE html>
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
</body>
</html>"""

        scanner = Html5TagScanner(html)

        # Find body element: html[0] -> body[1]
        body_range = scanner.find_element_range([0, 1])
        assert body_range is not None
        start, end = body_range
        body_content = html[start:end]
        assert body_content.startswith(b'<body>')
        assert body_content.endswith(b'</body>')

    def test_backward_compatibility_alias(self):
        """Test that SimpleTagScanner is an alias for XmlTagScanner."""
        assert SimpleTagScanner is XmlTagScanner

        # Test that it works for valid XML
        xml = b"""<root><child>text</child></root>"""
        scanner = SimpleTagScanner(xml)
        root_range = scanner.find_element_range([0])
        assert root_range is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
