"""Tests for Html5Formatter convenience class.

This ensures that the Html5Formatter works correctly and provides
HTML5-friendly parsing and escaping behavior.
"""

from markuplift import Html5Formatter, Formatter, ElementType
from markuplift.predicates import html_block_elements, tag_in
from markuplift.escaping import HtmlEscapingStrategy
from markuplift.parsing import HtmlParsingStrategy
from examples.attribute_formatters import num_css_properties, css_multiline_formatter


class TestHtml5Formatter:
    """Test Html5Formatter convenience class."""

    def test_html5_formatter_uses_html_strategies(self):
        """Test that Html5Formatter uses HTML-specific strategies."""
        formatter = Html5Formatter()

        # Access the internal formatter to check strategies
        internal_formatter = formatter._formatter
        assert isinstance(internal_formatter._escaping_strategy, HtmlEscapingStrategy)
        assert isinstance(internal_formatter._parsing_strategy, HtmlParsingStrategy)

    def test_html5_formatter_attribute_escaping(self):
        """Test that Html5Formatter uses HTML-friendly attribute escaping."""
        formatter = Html5Formatter(
            block_when=html_block_elements(),
            reformat_attribute_when={
                html_block_elements().with_attribute(
                    "style", lambda v: num_css_properties(v) >= 4
                ): css_multiline_formatter
            },
        )

        html = '<div><p style="color: green; background: black; margin: 10px; padding: 5px;">Complex</p></div>'
        result = formatter.format_str(html)

        # Should contain literal newlines, not &#10; entities
        assert "\n    color: green;" in result  # CSS formatter uses 4-space indentation
        assert "&#10;" not in result

    def test_html5_formatter_void_elements(self):
        """Test that Html5Formatter handles HTML5 void elements properly."""
        formatter = Html5Formatter(block_when=html_block_elements())

        # HTML5 void elements that don't need closing tags
        html = '<div><img src="test.jpg"><br><hr></div>'
        result = formatter.format_str(html)

        # lxml's HTML parser handles void elements, but MarkupLift still formats them
        # Note: The result will have a DOCTYPE because lxml adds it for HTML
        # MarkupLift will format as self-closing tags even for HTML
        assert '<img src="test.jpg"' in result
        assert "<br" in result
        assert "<hr" in result

    def test_html5_formatter_adds_doctype(self):
        """Test that Html5Formatter's HTML parser adds DOCTYPE."""
        formatter = Html5Formatter()

        html = "<div>content</div>"
        result = formatter.format_str(html)

        # lxml's HTML parser automatically adds DOCTYPE
        assert "DOCTYPE" in result

    def test_html5_formatter_delegation(self):
        """Test that Html5Formatter properly delegates all methods."""
        formatter = Html5Formatter(block_when=html_block_elements())

        # Test all public methods exist and work
        html = "<div>test</div>"

        # format_str
        str_result = formatter.format_str(html)
        assert "<div>" in str_result

        # format_bytes
        bytes_result = formatter.format_bytes(html.encode())
        assert "<div>" in bytes_result

        # format_tree (need to create a tree first)
        from lxml import html as lxml_html

        tree = lxml_html.fromstring(html)
        from lxml import etree

        tree_obj = etree.ElementTree(tree)
        tree_result = formatter.format_tree(tree_obj)
        assert "<div>" in tree_result

    def test_html5_formatter_vs_regular_formatter(self):
        """Test differences between Html5Formatter and regular Formatter."""
        # Create formatters with CSS multiline formatting
        html_formatter = Html5Formatter(
            reformat_attribute_when={
                tag_in("p").with_attribute("style", lambda v: num_css_properties(v) >= 4): css_multiline_formatter
            }
        )

        regular_formatter = Formatter(
            reformat_attribute_when={
                tag_in("p").with_attribute("style", lambda v: num_css_properties(v) >= 4): css_multiline_formatter
            }
        )

        test_html = '<p style="color: green; background: black; margin: 10px; padding: 5px;">Test</p>'

        html_result = html_formatter.format_str(test_html)
        regular_result = regular_formatter.format_str(test_html)

        # HTML formatter should have literal newlines
        assert "\n  color: green;" in html_result  # CSS formatter indentation based on element level
        assert "&#10;" not in html_result

        # Regular formatter should use XML escaping (encoded newlines)
        assert "&#10;" in regular_result
        assert "\n  color: green;" not in regular_result

    def test_html5_formatter_parsing_differences(self):
        """Test HTML5 vs XML parsing differences."""
        html_formatter = Html5Formatter()

        # Test with void elements (valid HTML, invalid XML without self-closing)
        html_content = '<div><img src="test.jpg"><br></div>'

        # HTML formatter should handle this fine
        html_result = html_formatter.format_str(html_content)
        assert "img" in html_result

        # Should also handle HTML-specific features
        html_with_html_tag = "<html><body><div>content</div></body></html>"
        result = html_formatter.format_str(html_with_html_tag)
        assert "html" in result
        assert "body" in result

    def test_html5_formatter_no_xml_declaration(self):
        """Test that Html5Formatter never produces XML declarations."""
        formatter = Html5Formatter()

        html = "<div>content</div>"
        result = formatter.format_str(html)

        # Should never contain XML declaration
        assert "<?xml" not in result

        # Test with doctype
        result_with_doctype = formatter.format_str(html, doctype="<!DOCTYPE html>")
        assert "<?xml" not in result_with_doctype
        assert "DOCTYPE html" in result_with_doctype

    def test_html5_formatter_uses_html_element_defaults(self):
        """Test that Html5Formatter uses HTML5 element classifications by default."""
        # Test with no configuration - should use HTML5 defaults
        formatter = Html5Formatter()

        html = "<div><p>Block content</p><strong>Inline content</strong></div>"
        result = formatter.format_str(html)

        # Should format with proper HTML5 block/inline classification
        assert "DOCTYPE html" in result

        # div and p should be formatted as blocks (with newlines and indentation)
        assert "<div>" in result
        assert "\n  <p>" in result  # p indented as block element

        # strong should be inline (no newlines around it)
        assert "<strong>Inline content</strong>" in result

    def test_html5_formatter_element_defaults_can_be_overridden(self):
        """Test that HTML5 element defaults can be overridden."""
        from markuplift.predicates import tag_in

        # Override to make only strong inline, with inline default
        formatter = Html5Formatter(
            block_when=tag_in("div"),
            inline_when=tag_in("strong", "p"),  # Make p explicitly inline
            default_type=ElementType.INLINE,  # Default unclassified elements to inline
        )

        html = "<div><p>Content</p><strong>Inline</strong></div>"
        result = formatter.format_str(html)

        # div should be block (indented)
        assert "<div>" in result

        # p should be inline (not indented on its own line)
        # When p is inline, it should be on the same line as div content
        assert "<div><p>Content</p>" in result

        # strong should be inline
        assert "<strong>Inline</strong>" in result

    def test_html5_formatter_explicit_none_uses_defaults(self):
        """Test that explicit None values still trigger HTML5 defaults."""
        formatter = Html5Formatter(block_when=None, inline_when=None)

        html = "<div><p>Content</p></div>"
        result = formatter.format_str(html)

        # Should still use HTML5 defaults
        assert "DOCTYPE html" in result
        assert "\n  <p>" in result  # p formatted as block

    def test_html5_formatter_whitespace_defaults(self):
        """Test that Html5Formatter uses sensible whitespace defaults."""
        formatter = Html5Formatter()

        # Test preserve_whitespace_when: should preserve whitespace in pre, code, etc.
        html_with_pre = "<div><pre>Line 1\n  Line 2\n    Line 3</pre></div>"
        result_pre = formatter.format_str(html_with_pre)

        # Should preserve the exact whitespace structure inside pre
        assert "Line 1\n  Line 2\n    Line 3" in result_pre

        # Test normalize_whitespace_when: should normalize whitespace in most elements
        html_with_spaces = "<div><p>Text   with    extra   spaces</p></div>"
        result_spaces = formatter.format_str(html_with_spaces)

        # Should normalize extra spaces to single spaces
        assert "Text with extra spaces" in result_spaces
        assert "Text   with    extra   spaces" not in result_spaces

    def test_html5_formatter_whitespace_significant_elements(self):
        """Test all whitespace-significant elements preserve whitespace."""
        formatter = Html5Formatter()

        # Test all whitespace-significant elements: pre, code, style, script, textarea
        test_cases = [
            "<pre>function() {\n  return true;\n}</pre>",
            "<code>let x = 1;\n  let y = 2;</code>",
            "<style>body {\n  margin: 0;\n}</style>",
            '<script>console.log(\n  "hello"\n);</script>',
            "<textarea>User input\n  with formatting</textarea>",
        ]

        for html in test_cases:
            result = formatter.format_str(f"<div>{html}</div>")
            # Each should preserve the internal whitespace structure
            if "function()" in html:
                assert "function() {\n  return true;\n}" in result
            elif "let x" in html:
                assert "let x = 1;\n  let y = 2;" in result
            elif "body" in html:
                assert "body {\n  margin: 0;\n}" in result
            elif "console.log" in html:
                assert 'console.log(\n  "hello"\n);' in result
            elif "User input" in html:
                assert "User input\n  with formatting" in result

    def test_html5_formatter_whitespace_can_be_overridden(self):
        """Test that whitespace defaults can be overridden."""
        from markuplift.predicates import tag_in

        # Override to preserve whitespace only in specific elements
        formatter = Html5Formatter(
            preserve_whitespace_when=tag_in("pre"),  # Only preserve in pre
            normalize_whitespace_when=tag_in("p"),  # Only normalize in p
        )

        # pre should still preserve whitespace (explicitly configured)
        html_pre = "<div><pre>Line 1\n  Line 2</pre></div>"
        result_pre = formatter.format_str(html_pre)
        assert "Line 1\n  Line 2" in result_pre

        # code should NOT preserve whitespace (not in override)
        html_code = "<div><code>Line 1\n  Line 2</code></div>"
        formatter.format_str(html_code)
        # Default formatting should apply (no special whitespace preservation)

        # p should normalize whitespace (explicitly configured)
        html_p = "<div><p>Text   with    spaces</p></div>"
        result_p = formatter.format_str(html_p)
        assert "Text with spaces" in result_p

    def test_html5_formatter_explicit_none_whitespace_uses_defaults(self):
        """Test that explicit None for whitespace parameters triggers defaults."""
        formatter = Html5Formatter(normalize_whitespace_when=None, preserve_whitespace_when=None)

        # Should still use HTML5 whitespace defaults
        html = "<div><p>Text   with   spaces</p><pre>Preserved\n  content</pre></div>"
        result = formatter.format_str(html)

        # Should normalize whitespace in p (default behavior)
        assert "Text with spaces" in result

        # Should preserve whitespace in pre (default behavior)
        assert "Preserved\n  content" in result

    def test_html5_formatter_strip_whitespace_defaults(self):
        """Test that Html5Formatter uses CSS block elements for strip_whitespace_when by default."""
        formatter = Html5Formatter()

        # Test CSS block elements: should strip leading/trailing whitespace
        test_cases = [
            ("<div>  content  </div>", "<div>content</div>"),
            ("<h1>  heading  </h1>", "<h1>heading</h1>"),
            ("<p>  paragraph  </p>", "<p>paragraph</p>"),
            ("<li>  list item  </li>", "<li>list item</li>"),
            ("<section>  section content  </section>", "<section>section content</section>"),
            ("<article>  article content  </article>", "<article>article content</article>"),
        ]

        for input_html, expected_content in test_cases:
            wrapped_input = f"<html><body>{input_html}</body></html>"
            result = formatter.format_str(wrapped_input)
            assert expected_content in result

    def test_html5_formatter_strip_whitespace_preserves_significant_elements(self):
        """Test that strip_whitespace_when excludes whitespace-significant elements."""
        formatter = Html5Formatter()

        # Whitespace-significant elements should NOT be stripped
        test_cases = [
            "<pre>  preserved content  </pre>",
            "<code>  preserved code  </code>",
            "<style>  body { margin: 0; }  </style>",
            '<script>  console.log("test");  </script>',
            "<textarea>  user input  </textarea>",
        ]

        for test_html in test_cases:
            wrapped_input = f"<html><body>{test_html}</body></html>"
            result = formatter.format_str(wrapped_input)
            # Should preserve the exact whitespace inside these elements
            if "preserved content" in test_html:
                assert "  preserved content  " in result
            elif "preserved code" in test_html:
                assert "  preserved code  " in result
            elif "margin: 0" in test_html:
                assert "  body { margin: 0; }  " in result
            elif "console.log" in test_html:
                assert '  console.log("test");  ' in result
            elif "user input" in test_html:
                assert "  user input  " in result

    def test_html5_formatter_strip_whitespace_css_block_elements(self):
        """Test all CSS block elements get whitespace stripped."""
        formatter = Html5Formatter()

        # Test a comprehensive set of CSS block elements
        block_elements = [
            "address",
            "article",
            "aside",
            "blockquote",
            "canvas",
            "dd",
            "div",
            "dl",
            "dt",
            "fieldset",
            "figcaption",
            "figure",
            "footer",
            "form",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "header",
            "hr",
            "li",
            "main",
            "nav",
            "noscript",
            "ol",
            "p",
            "section",
            "table",
            "tfoot",
            "ul",
            "video",
        ]

        for element in block_elements:
            # Skip void elements that don't have content
            if element in ("hr",):
                continue

            test_html = f"<{element}>  test content  </{element}>"
            wrapped_input = f"<html><body>{test_html}</body></html>"
            result = formatter.format_str(wrapped_input)

            # Should strip whitespace to become "test content"
            assert f"<{element}>test content</{element}>" in result

    def test_html5_formatter_strip_whitespace_can_be_overridden(self):
        """Test that strip_whitespace_when default can be overridden."""
        from markuplift.predicates import tag_in

        # Override to strip whitespace only from headings
        formatter = Html5Formatter(strip_whitespace_when=tag_in("h1", "h2", "h3"))

        # h1 should have whitespace stripped (explicitly configured)
        html_h1 = "<html><body><h1>  heading  </h1></body></html>"
        result_h1 = formatter.format_str(html_h1)
        assert "<h1>heading</h1>" in result_h1

        # p should NOT have whitespace stripped (not in override)
        # but whitespace normalization may still apply
        html_p = "<html><body><p>  paragraph  </p></body></html>"
        result_p = formatter.format_str(html_p)
        # Should contain " paragraph " (normalized but not fully stripped)
        assert " paragraph " in result_p and "<p>paragraph</p>" not in result_p

    def test_html5_formatter_explicit_none_strip_whitespace_uses_defaults(self):
        """Test that explicit None for strip_whitespace_when triggers defaults."""
        formatter = Html5Formatter(strip_whitespace_when=None)

        # Should still use CSS block element defaults
        html = "<html><body><div>  content  </div><pre>  preserved  </pre></body></html>"
        result = formatter.format_str(html)

        # Should strip whitespace in div (CSS block element)
        assert "<div>content</div>" in result

        # Should preserve whitespace in pre (whitespace-significant element)
        assert "  preserved  " in result

    def test_html5_formatter_script_tag_no_double_encoding(self):
        """Test that script tag content with > character doesn't get double-encoded."""
        formatter = Html5Formatter()

        # Test with > character that shouldn't be double-encoded
        # Simulate JavaScript code that contains >>> (Python REPL prompt)
        html = """<html>
<head>
<script>
const data = {
    "start_at": 0.025923,
    "text": ")\\r\\n>>> for i, name in enumerate(names):\\r\\n...     bright"
};
</script>
</head>
<body>
<p>Test</p>
</body>
</html>"""
        result = formatter.format_str(html)

        # Should NOT double-encode: should be >>> not &amp;gt;&amp;gt;&amp;gt;
        assert "&amp;gt;" not in result, "Script content should not be double-encoded"

        # The > characters should either be:
        # 1. Left as literal >>> (preferred for script content)
        # 2. Encoded once as &gt;&gt;&gt; (acceptable)
        # But NOT double-encoded as &amp;gt;

        # Check that we have the >>> sequence somewhere in the output
        # (either as literal or single-encoded)
        assert ">>>" in result or "&gt;&gt;&gt;" in result, "Script should contain the >>> sequence"

    def test_html5_formatter_script_tag_already_encoded_input(self):
        """Test that already-encoded input in script tags is preserved correctly.

        In HTML5, script and style elements use special parsing states (RAWTEXT/RCDATA)
        where character references are NOT decoded by the parser. This means &gt; stays
        as the literal string "&gt;" and should be preserved as-is in the output without
        double-encoding.

        This is correct HTML5 behavior per the spec.
        """
        formatter = Html5Formatter()

        # Test with ALREADY encoded &gt; in the INPUT
        # Per HTML5 spec, these should be preserved as-is (not double-encoded)
        html = """<html>
<head>
<script>
const data = {
    "start_at": 0.025923,
    "text": ")\\r\\n&gt;&gt;&gt; for i, name in enumerate(names):\\r\\n...     bright"
};
</script>
</head>
<body>
<p>Test</p>
</body>
</html>"""
        result = formatter.format_str(html)

        # HTML5 spec: script content is RAWTEXT, entities are NOT decoded
        # So &gt; in input should stay as &gt; in output (NOT become &amp;gt;)
        assert "&gt;&gt;&gt;" in result, "Script should preserve &gt; entities as-is"
        assert "&amp;gt;" not in result, "Script content should NOT be double-encoded"

    def test_html5_formatter_style_tag_no_double_encoding(self):
        """Test that style tag content with entities is not double-encoded.

        Style tags, like script tags, use RAWTEXT parsing in HTML5 where
        character references are not decoded. This test ensures we handle
        style content correctly.
        """
        formatter = Html5Formatter()

        html = """<html>
<head>
<style>
/* CSS with entity */
body::before { content: "&gt;&gt;&gt;"; }
body::after { content: "&lt;&lt;&lt;"; }
</style>
</head>
<body>
<p>Test</p>
</body>
</html>"""
        result = formatter.format_str(html)

        # Style content should preserve entities as-is (not double-encode)
        assert "&gt;&gt;&gt;" in result, "Style should preserve &gt; entities"
        assert "&lt;&lt;&lt;" in result, "Style should preserve &lt; entities"
        assert "&amp;gt;" not in result, "Style content should NOT be double-encoded"
        assert "&amp;lt;" not in result, "Style content should NOT be double-encoded"
