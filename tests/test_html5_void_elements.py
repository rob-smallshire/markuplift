"""Tests for HTML5 void element rendering.

This module comprehensively tests that Html5Formatter correctly handles HTML5 void
elements (single tag, no slash) versus non-void empty elements (explicit tags).
"""

from inspect import cleandoc
import pytest

from markuplift import Html5Formatter
from markuplift.predicates import html_block_elements


class TestHtml5VoidElements:
    """Tests for HTML5 void element rendering (single tag, no trailing slash)."""

    # All 13 HTML5 void elements
    VOID_ELEMENTS = ["area", "base", "br", "col", "embed", "hr", "img",
                     "input", "link", "meta", "source", "track", "wbr"]

    def test_void_elements_no_trailing_slash(self):
        """All void elements render as <tag> without trailing slash."""
        formatter = Html5Formatter()

        for tag in self.VOID_ELEMENTS:
            html = f"<html><body><{tag}></{tag}></body></html>"
            result = formatter.format_str(html)

            # Should have single tag without slash
            assert f"<{tag}>" in result
            # Should NOT have slash before closing angle bracket
            assert f"<{tag} />" not in result and f"<{tag}/>" not in result

    def test_void_elements_no_end_tag(self):
        """Void elements never have closing tags."""
        formatter = Html5Formatter()

        for tag in self.VOID_ELEMENTS:
            html = f"<html><body><{tag}></{tag}></body></html>"
            result = formatter.format_str(html)

            # Should NOT have closing tag
            assert f"</{tag}>" not in result

    def test_void_elements_with_attributes(self):
        """Void elements with attributes still render without slash."""
        formatter = Html5Formatter()

        test_cases = [
            ('<img src="test.jpg" alt="Test">', '<img'),
            ('<input type="text" name="username">', '<input'),
            ('<link rel="stylesheet" href="style.css">', '<link'),
            ('<meta charset="UTF-8">', '<meta charset="UTF-8">'),
        ]

        for input_html, tag_start in test_cases:
            html = f"<html><head>{input_html}</head></html>"
            result = formatter.format_str(html)
            assert tag_start in result
            # Ensure no trailing slash
            assert " />" not in result

    def test_br_element(self):
        """Test specific br element rendering."""
        formatter = Html5Formatter()

        html = "<div>Line 1<br>Line 2<br>Line 3</div>"
        result = formatter.format_str(html)

        # Count br tags - should appear exactly twice
        assert result.count("<br>") == 2
        # Should have NO closing br tags
        assert "</br>" not in result
        # Should have NO slashes
        assert "<br />" not in result and "<br/>" not in result

    def test_hr_element(self):
        """Test specific hr element rendering."""
        formatter = Html5Formatter()

        html = "<div><p>Section 1</p><hr><p>Section 2</p></div>"
        result = formatter.format_str(html)

        assert "<hr>" in result
        assert "</hr>" not in result
        assert "<hr />" not in result

    def test_img_element(self):
        """Test specific img element rendering."""
        formatter = Html5Formatter()

        html = '<div><img src="photo.jpg" alt="Photo"></div>'
        result = formatter.format_str(html)

        assert '<img src="photo.jpg" alt="Photo">' in result
        assert "</img>" not in result

    def test_input_element(self):
        """Test specific input element rendering."""
        formatter = Html5Formatter()

        html = '<form><input type="text" name="field"></form>'
        result = formatter.format_str(html)

        # Input tag should be present (attributes may be reordered)
        assert '<input' in result
        assert 'name="field"' in result
        assert 'type="text"' in result
        assert "</input>" not in result

    def test_multiple_void_elements_together(self):
        """Test document with multiple different void elements."""
        formatter = Html5Formatter()

        html = cleandoc("""
            <html>
            <head>
                <meta charset="UTF-8">
                <link rel="stylesheet" href="style.css">
            </head>
            <body>
                <img src="logo.png" alt="Logo">
                <hr>
                <input type="submit" value="Submit">
                <br>
            </body>
            </html>
        """)

        result = formatter.format_str(html)

        # Check all void elements present without slashes
        assert '<meta charset="UTF-8">' in result
        assert "<link" in result and " />" not in result
        assert "<img" in result and "</img>" not in result
        assert "<hr>" in result and "</hr>" not in result
        assert "<input" in result and "</input>" not in result
        assert "<br>" in result and "</br>" not in result


class TestHtml5NonVoidEmptyElements:
    """Tests for non-void empty elements (must use explicit start and end tags)."""

    def test_empty_script_explicit_tags(self):
        """Empty script element uses <script></script>."""
        formatter = Html5Formatter()

        html = "<html><body><script></script></body></html>"
        result = formatter.format_str(html)

        assert "<script></script>" in result
        assert "<script />" not in result

    def test_empty_style_explicit_tags(self):
        """Empty style element uses <style></style>."""
        formatter = Html5Formatter()

        html = "<html><head><style></style></head></html>"
        result = formatter.format_str(html)

        assert "<style></style>" in result
        assert "<style />" not in result

    def test_empty_div_explicit_tags(self):
        """Empty div element uses <div></div>."""
        formatter = Html5Formatter()

        html = "<html><body><div></div></body></html>"
        result = formatter.format_str(html)

        assert "<div></div>" in result
        assert "<div />" not in result

    def test_empty_span_explicit_tags(self):
        """Empty span element uses <span></span>."""
        formatter = Html5Formatter()

        html = "<html><body><span></span></body></html>"
        result = formatter.format_str(html)

        assert "<span></span>" in result
        assert "<span />" not in result

    def test_empty_p_explicit_tags(self):
        """Empty p element uses <p></p>."""
        formatter = Html5Formatter()

        html = "<html><body><p></p></body></html>"
        result = formatter.format_str(html)

        assert "<p></p>" in result
        assert "<p />" not in result

    def test_empty_title_explicit_tags(self):
        """Empty title element uses <title></title>."""
        formatter = Html5Formatter()

        html = "<html><head><title></title></head></html>"
        result = formatter.format_str(html)

        assert "<title></title>" in result
        assert "<title />" not in result

    def test_empty_textarea_explicit_tags(self):
        """Empty textarea element uses <textarea></textarea>."""
        formatter = Html5Formatter()

        html = '<html><body><textarea name="comment"></textarea></body></html>'
        result = formatter.format_str(html)

        assert '<textarea name="comment"></textarea>' in result
        assert "<textarea" in result and " />" not in result

    def test_empty_iframe_explicit_tags(self):
        """Empty iframe element uses <iframe></iframe>."""
        formatter = Html5Formatter()

        html = '<html><body><iframe src="page.html"></iframe></body></html>'
        result = formatter.format_str(html)

        assert '<iframe src="page.html"></iframe>' in result
        assert "<iframe" in result and " />" not in result

    def test_multiple_empty_non_void_elements(self):
        """Test multiple empty non-void elements together."""
        formatter = Html5Formatter()

        html = cleandoc("""
            <html>
            <head>
                <title></title>
                <style></style>
                <script></script>
            </head>
            <body>
                <div></div>
                <span></span>
                <p></p>
            </body>
            </html>
        """)

        result = formatter.format_str(html)

        # All should have explicit tags
        assert "<title></title>" in result
        assert "<style></style>" in result
        assert "<script></script>" in result
        assert "<div></div>" in result
        assert "<span></span>" in result
        assert "<p></p>" in result

        # None should have self-closing syntax
        assert " />" not in result


class TestHtml5MixedEmptyElements:
    """Tests for documents with both void and non-void empty elements."""

    def test_void_and_non_void_together(self):
        """Document with both void and non-void empty elements."""
        formatter = Html5Formatter()

        html = cleandoc("""
            <html>
            <body>
                <div></div>
                <br>
                <span></span>
                <hr>
                <script></script>
                <img src="test.jpg">
            </body>
            </html>
        """)

        result = formatter.format_str(html)

        # Non-void empty elements
        assert "<div></div>" in result
        assert "<span></span>" in result
        assert "<script></script>" in result

        # Void elements
        assert "<br>" in result and "</br>" not in result
        assert "<hr>" in result and "</hr>" not in result
        assert '<img src="test.jpg">' in result and "</img>" not in result

    def test_nested_structure_with_mixed_empty_elements(self):
        """Test nested structure with various empty element types."""
        formatter = Html5Formatter()

        html = cleandoc("""
            <html>
            <body>
                <div>
                    <p>Text with <br> break</p>
                    <div></div>
                    <img src="photo.jpg">
                </div>
                <section>
                    <hr>
                    <script></script>
                </section>
            </body>
            </html>
        """)

        result = formatter.format_str(html)

        # Verify void elements
        assert "<br>" in result
        assert "<img" in result
        assert "<hr>" in result

        # Verify non-void empty elements
        assert "<div></div>" in result
        assert "<script></script>" in result

    def test_empty_elements_created_by_whitespace_stripping(self):
        """Test elements that become empty after whitespace stripping."""
        formatter = Html5Formatter()

        # Elements with only whitespace
        html = cleandoc("""
            <html>
            <body>
                <div>   </div>
                <p>     </p>
                <span>  </span>
            </body>
            </html>
        """)

        result = formatter.format_str(html)

        # After stripping, these become empty but should still have explicit tags
        assert "<div></div>" in result or "<div>\n  </div>" in result  # depends on whitespace settings
        assert "<p></p>" in result or "<p>\n  </p>" in result
        assert "<span></span>" in result or "<span> </span>" in result  # normalized to single space
