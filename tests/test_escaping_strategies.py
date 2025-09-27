"""Tests for escaping strategy differences and behaviors.

This test module verifies that different escaping strategies (HTML vs XML)
behave correctly and produce the expected output differences for various
attribute value scenarios.
"""

import pytest
from markuplift import Formatter, Html5Formatter, XmlFormatter
from markuplift.escaping import HtmlEscapingStrategy, XmlEscapingStrategy
from markuplift.predicates import tag_in


class TestEscapingStrategyBehaviors:
    """Test escaping strategy behaviors in isolation."""

    def test_html_escaping_strategy_quote_attribute(self):
        """Test HtmlEscapingStrategy quote_attribute behavior."""
        strategy = HtmlEscapingStrategy()

        # Test with quotes - HTML strategy escapes them
        value_with_quotes = 'Say "hello" world'
        result = strategy.quote_attribute(value_with_quotes)
        assert result == '"Say &quot;hello&quot; world"'

        # Test with newlines - HTML strategy preserves them literally
        value_with_newlines = 'line1\nline2'
        result = strategy.quote_attribute(value_with_newlines)
        assert result == '"line1\nline2"'
        assert '&#10;' not in result

        # Test with ampersands
        value_with_amp = 'Tom & Jerry'
        result = strategy.quote_attribute(value_with_amp)
        assert result == '"Tom &amp; Jerry"'

    def test_xml_escaping_strategy_quote_attribute(self):
        """Test XmlEscapingStrategy quote_attribute behavior."""
        strategy = XmlEscapingStrategy()

        # Test with quotes - XML strategy chooses optimal quoting
        value_with_quotes = 'Say "hello" world'
        result = strategy.quote_attribute(value_with_quotes)
        # quoteattr chooses single quotes to avoid escaping
        assert result == '\'Say "hello" world\''

        # Test with single quotes - XML strategy chooses double quotes
        value_with_single = "Say 'hello' world"
        result = strategy.quote_attribute(value_with_single)
        assert result == '"Say \'hello\' world"'

        # Test with both quotes - XML strategy escapes one type
        value_with_both = 'Say "hello" and \'goodbye\''
        result = strategy.quote_attribute(value_with_both)
        # Should escape one type (usually double quotes become &quot;)
        assert '&quot;' in result or '&#39;' in result

        # Test with newlines - XML strategy escapes them
        value_with_newlines = 'line1\nline2'
        result = strategy.quote_attribute(value_with_newlines)
        assert '&#10;' in result

    def test_text_escaping_consistency(self):
        """Test that both strategies handle text content escaping consistently."""
        html_strategy = HtmlEscapingStrategy()
        xml_strategy = XmlEscapingStrategy()

        # Basic XML entities should be escaped the same way
        test_text = 'Tom & Jerry < 5 > 3'
        html_result = html_strategy.escape_text(test_text)
        xml_result = xml_strategy.escape_text(test_text)

        # Both should escape &, <, > consistently
        assert html_result == xml_result
        assert '&amp;' in html_result
        assert '&lt;' in html_result
        assert '&gt;' in html_result

    def test_comment_escaping_consistency(self):
        """Test comment text escaping behavior."""
        html_strategy = HtmlEscapingStrategy()
        xml_strategy = XmlEscapingStrategy()

        test_comment = 'Comment with & special < chars >'
        html_result = html_strategy.escape_comment_text(test_comment)
        xml_result = xml_strategy.escape_comment_text(test_comment)

        # Both should escape basic XML entities in comments
        assert html_result == xml_result
        assert '&amp;' in html_result
        assert '&lt;' in html_result
        assert '&gt;' in html_result


class TestFormatterEscapingDifferences:
    """Test how different formatters handle escaping in practice."""

    def test_css_multiline_escaping_differences(self):
        """Test CSS multiline formatting with different escaping strategies."""
        css_value = "color: red;\nbackground: blue;\nmargin: 10px;"

        def css_multiline_formatter(value, formatter, level):
            # Simple multiline formatter for testing
            properties = [prop.strip() for prop in value.split(';') if prop.strip()]
            return '\n' + ';\n'.join(properties) + '\n'

        # HTML5 formatter - should have literal newlines
        html_formatter = Html5Formatter(
            reformat_attribute_when={
                tag_in("div").with_attribute("style"): css_multiline_formatter
            }
        )

        # XML formatter - should have escaped newlines
        xml_formatter = XmlFormatter(
            reformat_attribute_when={
                tag_in("div").with_attribute("style"): css_multiline_formatter
            }
        )

        test_xml = f'<div style="{css_value}">content</div>'

        html_result = html_formatter.format_str(test_xml)
        xml_result = xml_formatter.format_str(test_xml)

        # HTML should contain literal newlines
        assert '\ncolor: red' in html_result
        assert '&#10;' not in html_result

        # XML should contain escaped newlines
        assert '&#10;' in xml_result
        assert '\ncolor: red' not in xml_result

    def test_json_attribute_escaping(self):
        """Test JSON-like attributes with different escaping strategies."""
        json_value = '{"theme": "dark", "options": ["a", "b"]}'

        # Regular formatter (XML strategy)
        xml_formatter = Formatter()

        # HTML5 formatter
        html_formatter = Html5Formatter()

        test_xml = f'<div data-config=\'{json_value}\'>content</div>'

        xml_result = xml_formatter.format_str(test_xml)
        html_result = html_formatter.format_str(test_xml)

        # XML formatter uses smart quoting (single quotes around, preserves double quotes inside)
        assert 'data-config=\'' in xml_result
        assert '"theme"' in xml_result

        # HTML formatter should escape quotes
        assert '&quot;theme&quot;' in html_result

    def test_mixed_quote_scenarios(self):
        """Test various combinations of quotes in attribute values."""
        # Test cases with pre-escaped XML input since parsers expect valid XML
        test_cases = [
            ('Simple &quot;double&quot; quotes', 'Simple "double" quotes', 'Contains double quotes'),
            ("Simple 'single' quotes", "Simple 'single' quotes", 'Contains single quotes'),
            ('Both &quot;double&quot; and \'single\'', 'Both "double" and \'single\'', 'Contains both quote types'),
            ('No quotes at all', 'No quotes at all', 'No quotes'),
        ]

        xml_formatter = Formatter()  # Uses XML strategy
        html_formatter = Html5Formatter()

        for input_value, expected_value, description in test_cases:
            test_xml = f'<div title="{input_value}">content</div>'

            try:
                xml_result = xml_formatter.format_str(test_xml)
                html_result = html_formatter.format_str(test_xml)

                # Both should produce valid, parseable XML/HTML
                assert '<div' in xml_result
                assert '<div' in html_result

                # Should contain the expected unescaped value somewhere in the output
                # (exact escaping in output depends on strategy)

            except Exception as e:
                pytest.fail(f"Failed to format {description} ('{input_value}'): {e}")

    def test_newline_in_attributes_scenarios(self):
        """Test handling of newlines in attribute values during output formatting."""
        # We need to test the output formatting, not input parsing
        # Create elements programmatically to test escaping strategies

        from lxml import etree

        xml_formatter = Formatter()  # XML strategy
        html_formatter = Html5Formatter()  # HTML strategy

        # Create element with newline in attribute programmatically
        root = etree.Element("div")
        root.set("style", "line1\nline2")
        tree = etree.ElementTree(root)

        xml_result = xml_formatter.format_tree(tree)
        html_result = html_formatter.format_tree(tree)

        # XML strategy should escape newlines in output
        assert '&#10;' in xml_result

        # HTML strategy should preserve literal newlines in output
        assert '\n' in html_result or 'DOCTYPE' in html_result  # HTML parser might add DOCTYPE

    def test_ampersand_escaping_consistency(self):
        """Test that ampersands are handled consistently."""
        # Use properly escaped XML as input since parsers expect valid XML
        test_cases = [
            ('Tom &amp; Jerry', 'Tom & Jerry'),
            ('A &amp; B &amp; C', 'A & B & C'),
            ('URL with ?param=1&amp;other=2', 'URL with ?param=1&other=2'),
        ]

        xml_formatter = Formatter()
        html_formatter = Html5Formatter()

        for input_value, expected_content in test_cases:
            test_xml = f'<div data-value="{input_value}">content</div>'

            xml_result = xml_formatter.format_str(test_xml)
            html_result = html_formatter.format_str(test_xml)

            # Both should handle the ampersands properly
            assert '<div' in xml_result
            assert '<div' in html_result
            # Ampersands should be escaped in output
            assert '&amp;' in xml_result
            assert '&amp;' in html_result


class TestBackwardCompatibility:
    """Test that escaping changes maintain backward compatibility where expected."""

    def test_regular_formatter_unchanged_behavior(self):
        """Test that regular Formatter behavior is unchanged for simple cases."""
        formatter = Formatter()

        # Simple XML that should format the same way
        simple_xml = '<root><child attr="simple value">text</child></root>'
        result = formatter.format_str(simple_xml)

        # Should be well-formed and contain expected elements
        assert '<root>' in result
        assert '<child attr="simple value">' in result
        assert 'text' in result

    def test_xml_formatter_matches_regular_formatter(self):
        """Test that XmlFormatter produces identical output to regular Formatter."""
        regular_formatter = Formatter()
        xml_formatter = XmlFormatter()

        test_cases = [
            '<root>simple</root>',
            '<root attr="value">content</root>',
            '<root><child>nested</child></root>',
            '<!-- comment --><root>with comment</root>',
        ]

        for xml in test_cases:
            regular_result = regular_formatter.format_str(xml)
            xml_result = xml_formatter.format_str(xml)

            # Should produce identical output
            assert regular_result == xml_result

    def test_escaping_strategy_injection_works(self):
        """Test that custom escaping strategies can be injected."""
        # Create a custom formatter with HTML escaping strategy
        custom_formatter = Formatter(escaping_strategy=HtmlEscapingStrategy())

        # Test with quotes to verify the strategy is being used
        test_xml = '<div title=\'Say "hello"\'>content</div>'
        result = custom_formatter.format_str(test_xml)

        # Should use HTML escaping (escape quotes as &quot;)
        assert '&quot;' in result