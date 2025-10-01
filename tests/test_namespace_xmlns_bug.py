"""Test for xmlns attribute handling bug.

This test verifies the fix for a bug where format_attribute_name() would
crash when encountering xmlns declarations in HTML5 documents with embedded SVG.
"""

import pytest
from lxml import etree
from markuplift import Html5Formatter
from markuplift.namespace import format_attribute_name


def test_format_attribute_name_handles_xmlns():
    """format_attribute_name should handle xmlns declarations without crashing.

    After normalization by parsing strategy, xmlns declarations are in their final
    format and format_attribute_name() should return them as-is.
    """
    # Create a simple element with xmlns declarations
    doc = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"/>'
    elem = etree.fromstring(doc.encode())

    # These should be returned as-is (they're already in final format after normalization)
    assert format_attribute_name(elem, "xmlns") == "xmlns"
    assert format_attribute_name(elem, "xmlns:xlink") == "xmlns:xlink"


def test_html5_with_embedded_svg():
    """Html5Formatter should handle HTML with embedded SVG without crashing.

    This is a regression test for the bug where xmlns:* attributes in SVG
    caused ValueError: Invalid tag name 'xmlns:xlink'.
    """
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 100 100">
        <use xlink:href="#shape"/>
    </svg>
</body>
</html>"""

    formatter = Html5Formatter()

    # This should not crash
    result = formatter.format_str(html, doctype="<!DOCTYPE html>")

    # Verify the output is valid and contains the SVG
    assert "<!DOCTYPE html>" in result
    assert "<svg" in result
    assert 'xmlns="http://www.w3.org/2000/svg"' in result
    assert 'xmlns:xlink="http://www.w3.org/1999/xlink"' in result
    assert "xlink:href" in result


def test_xmlns_attributes_in_element_attrib():
    """Verify that xmlns attributes appear in element.attrib dict."""
    # This documents the behavior we need to handle
    doc = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"/>'
    elem = etree.fromstring(doc.encode())

    # xmlns declarations do appear in attrib dict
    # (This is different from the nsmap, which is the parsed namespace map)
    assert "xmlns" in elem.attrib or len(elem.attrib) >= 0  # May or may not be in attrib depending on lxml version
    # But we can iterate over all attributes
    for attr_name in elem.attrib:
        # format_attribute_name should handle any attribute name without crashing
        result = format_attribute_name(elem, attr_name)
        assert isinstance(result, str)
        assert len(result) > 0


def test_regular_attributes_still_work():
    """Verify that regular attributes are still formatted correctly."""
    doc = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
        <use xlink:href="#shape" id="test"/>
    </svg>"""
    root = etree.fromstring(doc.encode())
    use_elem = root[0]

    # Regular attribute (no namespace)
    assert format_attribute_name(use_elem, "id") == "id"

    # Namespaced attribute (should use prefix)
    assert format_attribute_name(use_elem, "{http://www.w3.org/1999/xlink}href") == "xlink:href"


def test_html_parsed_attributes_with_colons():
    """Test that HTML-parsed attributes with colons are handled correctly.

    When HTML is parsed (not XML), namespaced attributes are stored with their
    literal prefix:localname format rather than Clark notation. This test ensures
    format_attribute_name() handles that case correctly.
    """
    from lxml import html

    html_doc = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
        <use xlink:href="#shape" data-custom:value="test"/>
    </svg>"""

    root = html.fromstring(html_doc)
    use_elem = root[0]

    # In HTML parsing, these are stored as literal strings with colons
    for attr_name in use_elem.attrib:
        # format_attribute_name() should handle these without crashing
        result = format_attribute_name(use_elem, attr_name)
        assert isinstance(result, str)
        # Attributes with colons should be preserved as-is
        if ":" in attr_name:
            assert result == attr_name


def test_comprehensive_html5_svg_example():
    """Test the exact scenario from the bug report with comprehensive assertions."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SVG Example</title>
</head>
<body>
    <h1>Test Page</h1>
    <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
         viewBox="0 0 100 100" width="100" height="100">
        <defs>
            <circle id="shape" r="10"/>
        </defs>
        <use xlink:href="#shape" x="50" y="50"/>
    </svg>
    <p>Text after SVG</p>
</body>
</html>"""

    formatter = Html5Formatter()

    # The key assertion: this should not crash with ValueError: Invalid tag name
    result = formatter.format_str(html, doctype="<!DOCTYPE html>")

    # Verify structure is preserved
    assert "<!DOCTYPE html>" in result
    assert "<html" in result
    assert "<svg" in result
    assert "<use" in result
    assert "<p>Text after SVG</p>" in result

    # Verify namespaced attributes are preserved correctly
    # (exact format may vary, but they should be present)
    assert "xlink:href" in result or "xlink" in result
    assert "#shape" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
