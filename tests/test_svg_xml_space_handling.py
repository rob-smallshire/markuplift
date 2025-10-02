"""Tests for xml:space attribute handling in SVG reparsing.

This module tests how the formatter handles xml:space="preserve" on SVG elements
when using parse_as_xml_when for XML reparsing. The xml:space attribute is an
XML specification directive that controls whitespace handling.
"""

from pathlib import Path

import pytest

from markuplift.html5_formatter import Html5Formatter
from markuplift.predicates import tag_in


class TestSVGXmlSpaceHandling:
    """Test xml:space attribute handling in SVG elements."""

    def test_svg_without_xml_space_gets_reformatted(self):
        """SVG without xml:space="preserve" should be reformatted with proper indentation."""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <article>
      <section>
        <svg xmlns="http://www.w3.org/2000/svg" xmlns:bx="https://example.com">
  <defs>
  <bx:custom x="0" y="0"/>
  <linearGradient id="grad1">
    <stop offset="0%"/>
  </linearGradient>
</defs>
  <rect x="0" y="0"/>
</svg>
      </section>
    </article>
</body>
</html>"""

        formatter = Html5Formatter(parse_as_xml_when=tag_in('svg'))
        formatted = formatter.format_str(html)

        # SVG and descendants should be properly indented
        lines = formatted.split('\n')

        # Find SVG line
        svg_line_idx = next(i for i, line in enumerate(lines) if '<svg' in line)

        # Check indentation levels (2 spaces per level)
        svg_line = lines[svg_line_idx]
        assert svg_line.startswith(' ' * 8)  # depth 4: html->body->article->section->svg

        # Find defs line (first child of svg)
        defs_line_idx = next(i for i, line in enumerate(lines[svg_line_idx:], svg_line_idx) if '<defs' in line)
        defs_line = lines[defs_line_idx]
        assert defs_line.startswith(' ' * 10)  # depth 5: svg->defs

        # Find bx:custom line (child of defs)
        custom_line_idx = next(i for i, line in enumerate(lines[defs_line_idx:], defs_line_idx) if '<bx:custom' in line)
        custom_line = lines[custom_line_idx]
        assert custom_line.startswith(' ' * 12)  # depth 6: defs->bx:custom

        # Find linearGradient line (child of defs)
        grad_line_idx = next(i for i, line in enumerate(lines[defs_line_idx:], defs_line_idx) if '<linearGradient' in line)
        grad_line = lines[grad_line_idx]
        assert grad_line.startswith(' ' * 12)  # depth 6: defs->linearGradient

        # Find stop line (child of linearGradient)
        stop_line_idx = next(i for i, line in enumerate(lines[grad_line_idx:], grad_line_idx) if '<stop' in line)
        stop_line = lines[stop_line_idx]
        assert stop_line.startswith(' ' * 14)  # depth 7: linearGradient->stop

    def test_svg_with_xml_space_preserve_keeps_original_whitespace(self):
        """SVG with xml:space="preserve" should preserve original whitespace formatting."""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <article>
      <section>
        <svg xmlns="http://www.w3.org/2000/svg" xmlns:bx="https://example.com" xml:space="preserve">
  <defs>
  <bx:custom x="0" y="0"/>
  <linearGradient id="grad1">
    <stop offset="0%"/>
  </linearGradient>
</defs>
  <rect x="0" y="0"/>
</svg>
      </section>
    </article>
</body>
</html>"""

        formatter = Html5Formatter(parse_as_xml_when=tag_in('svg'))
        formatted = formatter.format_str(html)

        lines = formatted.split('\n')

        # Find SVG line - should be properly indented in HTML context
        svg_line_idx = next(i for i, line in enumerate(lines) if '<svg' in line)
        svg_line = lines[svg_line_idx]
        assert svg_line.startswith(' ' * 8)  # SVG itself is indented in HTML context
        assert 'xml:space="preserve"' in svg_line

        # But descendants should preserve their ORIGINAL whitespace (minimal)
        # Find defs line
        defs_line_idx = next(i for i, line in enumerate(lines[svg_line_idx:], svg_line_idx) if '<defs' in line)
        defs_line = lines[defs_line_idx]
        # Original has 2 spaces before <defs>, should be preserved
        assert defs_line.startswith('  <defs')
        assert not defs_line.startswith(' ' * 10)  # NOT reformatted to depth 5

        # Find bx:custom line
        custom_line_idx = next(i for i, line in enumerate(lines[defs_line_idx:], defs_line_idx) if '<bx:custom' in line)
        custom_line = lines[custom_line_idx]
        # Original has 2 spaces before <bx:custom>, should be preserved
        assert custom_line.startswith('  <bx:custom')
        assert not custom_line.startswith(' ' * 12)  # NOT reformatted to depth 6

    def test_real_world_svg_file_without_xml_space(self):
        """Test with actual html_with_svg.html file (no xml:space)."""
        test_file = Path(__file__).parent / "data" / "html_with_svg.html"

        # Verify the file doesn't have xml:space="preserve"
        html_source = test_file.read_text()
        assert 'xml:space="preserve"' not in html_source

        formatter = Html5Formatter(parse_as_xml_when=tag_in('svg'))
        formatted = formatter.format_str(html_source)

        lines = formatted.split('\n')

        # Find SVG element
        svg_line_idx = next(i for i, line in enumerate(lines) if '<svg' in line)
        svg_line = lines[svg_line_idx]
        svg_indent = len(svg_line) - len(svg_line.lstrip())

        # Find first child of SVG (should be <defs>)
        defs_line_idx = next(i for i, line in enumerate(lines[svg_line_idx:], svg_line_idx)
                            if line.strip().startswith('<defs'))
        defs_line = lines[defs_line_idx]
        defs_indent = len(defs_line) - len(defs_line.lstrip())

        # defs should be indented 2 spaces more than svg
        assert defs_indent == svg_indent + 2

        # Find a child of defs
        grad_line_idx = next(i for i, line in enumerate(lines[defs_line_idx:], defs_line_idx)
                            if '<linearGradient' in line or '<bx:grid' in line)
        grad_line = lines[grad_line_idx]
        grad_indent = len(grad_line) - len(grad_line.lstrip())

        # Child of defs should be indented 2 spaces more than defs
        assert grad_indent == defs_indent + 2

    def test_xml_space_preserve_attribute_is_retained(self):
        """Verify that xml:space="preserve" attribute is retained in output."""
        html = """<!DOCTYPE html>
<html>
<body>
    <svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve">
  <rect x="0"/>
</svg>
</body>
</html>"""

        formatter = Html5Formatter(parse_as_xml_when=tag_in('svg'))
        formatted = formatter.format_str(html)

        # The xml:space attribute should be preserved
        assert 'xml:space="preserve"' in formatted

    def test_xml_space_default_allows_reformatting(self):
        """SVG with xml:space="default" should allow reformatting."""
        html = """<!DOCTYPE html>
<html>
<body>
    <svg xmlns="http://www.w3.org/2000/svg" xml:space="default">
  <defs>
  <rect x="0"/>
</defs>
</svg>
</body>
</html>"""

        formatter = Html5Formatter(parse_as_xml_when=tag_in('svg'))
        formatted = formatter.format_str(html)

        lines = formatted.split('\n')

        # Find defs line
        defs_line_idx = next(i for i, line in enumerate(lines) if '<defs' in line)
        defs_line = lines[defs_line_idx]

        # With xml:space="default", content should be reformatted
        # defs should be properly indented (not at column 2)
        defs_indent = len(defs_line) - len(defs_line.lstrip())
        assert defs_indent > 2  # Should be reformatted, not preserving original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
