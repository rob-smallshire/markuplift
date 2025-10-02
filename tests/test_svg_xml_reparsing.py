"""Integration tests for SVG XML reparsing in HTML5 documents.

Tests that Html5Formatter with parse_as_xml_when can preserve case-sensitive
SVG elements like <textPath>, <linearGradient>, etc.
"""

import pytest
from lxml import etree
from markuplift import Html5Formatter, tag_in


def test_svg_textpath_case_preserved():
    """Test that textPath case is preserved when SVG is reparsed as XML."""
    html_source = """<!DOCTYPE html>
<html>
<body>
    <svg xmlns="http://www.w3.org/2000/svg">
        <textPath href="#path">Text on path</textPath>
    </svg>
</body>
</html>"""

    formatter = Html5Formatter(
        parse_as_xml_when=tag_in("svg"),
    )

    result = formatter.format_str(html_source)

    # Case should be preserved in output
    assert "<textPath" in result
    assert "<textpath" not in result


def test_svg_gradient_elements_case_preserved():
    """Test that linearGradient and radialGradient case is preserved."""
    html_source = """<!DOCTYPE html>
<html>
<body>
    <svg xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="grad1">
                <stop offset="0%"/>
            </linearGradient>
            <radialGradient id="grad2">
                <stop offset="100%"/>
            </radialGradient>
        </defs>
    </svg>
</body>
</html>"""

    formatter = Html5Formatter(
        parse_as_xml_when=tag_in("svg"),
    )

    result = formatter.format_str(html_source)

    # Case should be preserved in output
    assert "linearGradient" in result
    assert "radialGradient" in result
    assert "lineargradient" not in result
    assert "radialgradient" not in result


def test_svg_with_nested_case_sensitive_elements():
    """Test complex SVG with multiple case-sensitive elements."""
    html_source = """<!DOCTYPE html>
<html>
<body>
    <div>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100">
            <defs>
                <path id="curvePath" d="M 10,50 Q 50,10 100,50"/>
                <linearGradient id="myGradient">
                    <stop offset="0%" stop-color="red"/>
                    <stop offset="100%" stop-color="blue"/>
                </linearGradient>
            </defs>
            <text>
                <textPath href="#curvePath">
                    <tspan>Curved text</tspan>
                </textPath>
            </text>
            <rect fill="url(#myGradient)" width="100" height="50"/>
        </svg>
    </div>
</body>
</html>"""

    formatter = Html5Formatter(
        parse_as_xml_when=tag_in("svg"),
        block_when=tag_in("svg", "defs", "text", "rect", "path"),
    )

    result = formatter.format_str(html_source)

    # All case-sensitive elements should be preserved
    assert "linearGradient" in result
    assert "textPath" in result
    assert "tspan" in result  # lowercase, but should still work
    assert "stop-color" in result  # attribute names


def test_multiple_svg_elements():
    """Test multiple SVG elements in same document."""
    html_source = """<!DOCTYPE html>
<html>
<body>
    <svg xmlns="http://www.w3.org/2000/svg">
        <textPath>First</textPath>
    </svg>
    <p>Some text</p>
    <svg xmlns="http://www.w3.org/2000/svg">
        <linearGradient id="g1"/>
    </svg>
</body>
</html>"""

    formatter = Html5Formatter(
        parse_as_xml_when=tag_in("svg"),
    )

    result = formatter.format_str(html_source)

    # Both SVG elements should have case preserved
    assert result.count("textPath") == 2  # Opening and closing
    assert result.count("linearGradient") == 2  # Opening and closing (HTML serialization doesn't use self-closing)


def test_svg_without_reparsing():
    """Test that without parse_as_xml_when, case is lost (baseline)."""
    html_source = """<!DOCTYPE html>
<html>
<body>
    <svg xmlns="http://www.w3.org/2000/svg">
        <textPath>Text</textPath>
    </svg>
</body>
</html>"""

    # No parse_as_xml_when - HTML parser will lowercase everything
    formatter = Html5Formatter()

    result = formatter.format_str(html_source)

    # Case should be lost
    assert "textpath" in result
    assert "textPath" not in result


def test_svg_with_comments_and_cdata():
    """Test SVG with comments."""
    html_source = """<!DOCTYPE html>
<html>
<body>
    <!-- Comment before SVG -->
    <svg xmlns="http://www.w3.org/2000/svg">
        <!-- Comment inside SVG -->
        <textPath>Text</textPath>
    </svg>
</body>
</html>"""

    formatter = Html5Formatter(
        parse_as_xml_when=tag_in("svg"),
    )

    result = formatter.format_str(html_source)

    # Comments and case should be preserved
    assert "<!-- Comment before SVG -->" in result
    assert "<!-- Comment inside SVG -->" in result
    assert "textPath" in result


def test_svg_with_utf8_content():
    """Test SVG with UTF-8 multibyte characters."""
    html_source = """<!DOCTYPE html>
<html>
<body>
    <p>Text with special chars: café</p>
    <svg xmlns="http://www.w3.org/2000/svg">
        <textPath>Unicode: café ☕</textPath>
    </svg>
</body>
</html>"""

    formatter = Html5Formatter(
        parse_as_xml_when=tag_in("svg"),
    )

    result = formatter.format_str(html_source)

    # Case and UTF-8 should be preserved
    assert "textPath" in result
    assert "café" in result
    assert "☕" in result


def test_svg_reparsing_with_format_bytes():
    """Test that format_bytes also supports XML reparsing."""
    html_source = b"""<!DOCTYPE html>
<html>
<body>
    <svg xmlns="http://www.w3.org/2000/svg">
        <textPath>Text</textPath>
    </svg>
</body>
</html>"""

    formatter = Html5Formatter(
        parse_as_xml_when=tag_in("svg"),
    )

    result = formatter.format_bytes(html_source)

    # Case should be preserved
    assert "textPath" in result


def test_svg_reparsing_with_format_file(tmp_path):
    """Test that format_file also supports XML reparsing."""
    html_source = """<!DOCTYPE html>
<html>
<body>
    <svg xmlns="http://www.w3.org/2000/svg">
        <textPath>Text</textPath>
    </svg>
</body>
</html>"""

    # Write to temp file
    test_file = tmp_path / "test.html"
    test_file.write_text(html_source)

    formatter = Html5Formatter(
        parse_as_xml_when=tag_in("svg"),
    )

    result = formatter.format_file(str(test_file))

    # Case should be preserved
    assert "textPath" in result


def test_svg_reparsing_preserves_attributes():
    """Test that XML reparsing preserves all attributes."""
    html_source = """<!DOCTYPE html>
<html>
<body>
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
        <textPath href="#path" startOffset="25%" method="align" spacing="auto">Text</textPath>
    </svg>
</body>
</html>"""

    formatter = Html5Formatter(
        parse_as_xml_when=tag_in("svg"),
    )

    result = formatter.format_str(html_source)

    # All attributes should be preserved
    assert 'xmlns="http://www.w3.org/2000/svg"' in result
    assert 'viewBox="0 0 100 100"' in result
    assert 'href="#path"' in result
    assert 'startOffset="25%"' in result
    assert "textPath" in result


def test_svg_with_invalid_xml_falls_back():
    """Test that invalid XML in SVG subtree doesn't crash (graceful fallback)."""
    html_source = """<!DOCTYPE html>
<html>
<body>
    <svg xmlns="http://www.w3.org/2000/svg">
        <textPath>Unclosed tag
    </svg>
</body>
</html>"""

    formatter = Html5Formatter(
        parse_as_xml_when=tag_in("svg"),
    )

    # Should not raise an error
    result = formatter.format_str(html_source)

    # Should still produce output (with lowercased SVG since reparsing failed)
    assert "<svg" in result
    assert "</svg>" in result


def test_format_tree_skips_xml_reparsing():
    """Test that format_tree doesn't attempt XML reparsing (no source available)."""
    html_source = """<!DOCTYPE html>
<html>
<body>
    <svg xmlns="http://www.w3.org/2000/svg">
        <textPath>Text</textPath>
    </svg>
</body>
</html>"""

    # Parse with HTML parser (case will be lost)
    from lxml import html as lxml_html, etree
    element = lxml_html.fromstring(html_source)
    tree = etree.ElementTree(element)

    formatter = Html5Formatter(
        parse_as_xml_when=tag_in("svg"),
    )

    result = formatter.format_tree(tree)

    # Case will be lost because we can't reparse without source
    assert "textpath" in result
    assert "textPath" not in result


def test_svg_namespace_preserved_after_reparsing():
    """Test that SVG namespace is preserved after reparsing."""
    html_source = """<!DOCTYPE html>
<html>
<body>
    <svg xmlns="http://www.w3.org/2000/svg">
        <textPath>Text</textPath>
    </svg>
</body>
</html>"""

    formatter = Html5Formatter(
        parse_as_xml_when=tag_in("svg"),
    )

    result = formatter.format_str(html_source)

    # Namespace declaration should be preserved in output
    assert 'xmlns="http://www.w3.org/2000/svg"' in result

    # Case should be preserved
    assert "textPath" in result

    # When we parse the formatted output with HTML parser, the xmlns attribute is preserved
    from lxml import html as lxml_html
    result_tree = lxml_html.fromstring(result)
    svg_elem = result_tree.find(".//svg")
    assert svg_elem is not None
    assert svg_elem.get("xmlns") == "http://www.w3.org/2000/svg"
