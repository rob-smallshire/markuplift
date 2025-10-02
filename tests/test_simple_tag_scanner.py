"""Tests for SimpleTagScanner source location functionality."""

import pytest
from markuplift.source_locator import SimpleTagScanner


def test_find_simple_element():
    """Scanner finds a simple element at the root."""
    source = b'<root><child>content</child></root>'
    scanner = SimpleTagScanner(source)

    # Root element is at path [0]
    result = scanner.find_element_range([0])
    assert result == (0, len(source))


def test_find_nested_element():
    """Scanner finds nested elements using child indices."""
    source = b'<root><first>1</first><second><nested>content</nested></second></root>'
    scanner = SimpleTagScanner(source)

    # root → second child → first child
    result = scanner.find_element_range([0, 1, 0])
    assert result is not None
    start, end = result
    extracted = source[start:end]
    assert extracted == b'<nested>content</nested>'


def test_find_element_with_attributes():
    """Scanner handles elements with attributes."""
    source = b'<root><div class="test" id="main">content</div></root>'
    scanner = SimpleTagScanner(source)

    result = scanner.find_element_range([0, 0])
    assert result is not None
    start, end = result
    extracted = source[start:end]
    assert extracted == b'<div class="test" id="main">content</div>'


def test_self_closing_element():
    """Scanner finds self-closing elements."""
    source = b'<root><img src="test.jpg"/><p>text</p></root>'
    scanner = SimpleTagScanner(source)

    # First child is self-closing img
    result = scanner.find_element_range([0, 0])
    assert result is not None
    start, end = result
    extracted = source[start:end]
    assert extracted == b'<img src="test.jpg"/>'


def test_skip_comments():
    """Scanner skips HTML comments."""
    source = b'<root><!-- comment --><child>content</child></root>'
    scanner = SimpleTagScanner(source)

    # First child is <child>, comment is skipped
    result = scanner.find_element_range([0, 0])
    assert result is not None
    start, end = result
    extracted = source[start:end]
    assert extracted == b'<child>content</child>'


def test_skip_cdata():
    """Scanner skips CDATA sections."""
    source = b'<root><![CDATA[some data]]><child>content</child></root>'
    scanner = SimpleTagScanner(source)

    # First child is <child>, CDATA is skipped
    result = scanner.find_element_range([0, 0])
    assert result is not None
    start, end = result
    extracted = source[start:end]
    assert extracted == b'<child>content</child>'


def test_skip_processing_instructions():
    """Scanner skips processing instructions."""
    source = b'<root><?xml-stylesheet type="text/xsl" href="style.xsl"?><child>content</child></root>'
    scanner = SimpleTagScanner(source)

    # First child is <child>, PI is skipped
    result = scanner.find_element_range([0, 0])
    assert result is not None
    start, end = result
    extracted = source[start:end]
    assert extracted == b'<child>content</child>'


def test_multiple_siblings():
    """Scanner correctly tracks child indices for multiple siblings."""
    source = b'<root><a>1</a><b>2</b><c>3</c></root>'
    scanner = SimpleTagScanner(source)

    # First child
    result = scanner.find_element_range([0, 0])
    assert result is not None
    assert source[result[0]:result[1]] == b'<a>1</a>'

    # Second child
    result = scanner.find_element_range([0, 1])
    assert result is not None
    assert source[result[0]:result[1]] == b'<b>2</b>'

    # Third child
    result = scanner.find_element_range([0, 2])
    assert result is not None
    assert source[result[0]:result[1]] == b'<c>3</c>'


def test_deeply_nested_structure():
    """Scanner handles deeply nested elements."""
    source = b'<root><a><b><c><d>deep</d></c></b></a></root>'
    scanner = SimpleTagScanner(source)

    # Path to deeply nested <d>
    result = scanner.find_element_range([0, 0, 0, 0, 0])
    assert result is not None
    start, end = result
    extracted = source[start:end]
    assert extracted == b'<d>deep</d>'


def test_svg_in_html():
    """Scanner finds SVG element in HTML document."""
    source = b'''<!DOCTYPE html>
<html>
<body>
    <p>Before</p>
    <svg xmlns="http://www.w3.org/2000/svg">
        <textPath>Content</textPath>
    </svg>
</body>
</html>'''
    scanner = SimpleTagScanner(source)

    # Path: html[0] → body[0] (first child of html) → svg[1] (second child of body, after <p>)
    result = scanner.find_element_range([0, 0, 1])
    assert result is not None
    start, end = result
    extracted = source[start:end]
    assert b'<svg' in extracted
    assert b'</svg>' in extracted
    assert b'<textPath>' in extracted


def test_element_not_found():
    """Scanner returns None when path doesn't exist."""
    source = b'<root><child>content</child></root>'
    scanner = SimpleTagScanner(source)

    # Path too deep
    result = scanner.find_element_range([0, 0, 0])
    assert result is None

    # Index out of range
    result = scanner.find_element_range([0, 5])
    assert result is None


def test_empty_element():
    """Scanner handles empty elements with explicit closing tags."""
    source = b'<root><empty></empty><p>text</p></root>'
    scanner = SimpleTagScanner(source)

    result = scanner.find_element_range([0, 0])
    assert result is not None
    start, end = result
    extracted = source[start:end]
    assert extracted == b'<empty></empty>'


def test_attributes_with_angle_brackets():
    """Scanner handles attributes containing angle bracket characters."""
    source = b'<root><div data-expr="x > y"><span>content</span></div></root>'
    scanner = SimpleTagScanner(source)

    result = scanner.find_element_range([0, 0, 0])
    assert result is not None
    start, end = result
    extracted = source[start:end]
    assert extracted == b'<span>content</span>'


def test_utf8_multibyte_characters():
    """Scanner handles UTF-8 multibyte characters correctly using byte offsets."""
    # Emoji is 4 bytes in UTF-8
    source = '<root><p>🎉</p><svg>content</svg></root>'.encode('utf-8')
    scanner = SimpleTagScanner(source)

    # Path to <svg> (second child of root, after <p>)
    result = scanner.find_element_range([0, 1])
    assert result is not None
    start, end = result
    extracted = source[start:end]
    assert extracted == b'<svg>content</svg>'

    # Verify byte offset is correct (emoji is 4 bytes, not 1 char)
    # <root><p>🎉</p> is 6 + 3 + 4 (emoji) + 4 = 17 bytes before <svg>
    assert start >= 17  # Account for multibyte emoji
