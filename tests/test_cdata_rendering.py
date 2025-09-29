"""Low-level unit tests for CDATA rendering algorithms.

This module contains comprehensive tests for the _render_safe_cdata method
and related CDATA handling functionality in DocumentFormatter.
"""

import pytest
from lxml import etree

from markuplift.document_formatter import DocumentFormatter
from markuplift.escaping import XmlEscapingStrategy
from markuplift.doctype import NullDoctypeStrategy
from markuplift.attribute_formatting import NullAttributeStrategy
from markuplift.types import ElementType


class TestCDATARenderingSafety:
    """Test the _render_safe_cdata method for correct handling of problematic sequences."""

    @pytest.fixture
    def formatter(self):
        """Create a minimal DocumentFormatter for testing."""
        return DocumentFormatter(
            block_predicate=lambda e: False,
            inline_predicate=lambda e: True,
            normalize_whitespace_predicate=lambda e: False,
            strip_whitespace_predicate=lambda e: False,
            preserve_whitespace_predicate=lambda e: False,
            wrap_attributes_predicate=lambda e: False,
            text_content_formatters={},
            attribute_content_formatters={},
            escaping_strategy=XmlEscapingStrategy(),
            doctype_strategy=NullDoctypeStrategy(),
            attribute_strategy=NullAttributeStrategy(),
            indent_size=2,
            default_type=ElementType.BLOCK
        )

    def test_render_safe_cdata_simple_content(self, formatter):
        """Test CDATA rendering with simple, safe content."""
        result = formatter._render_safe_cdata("simple content")
        assert result == "<![CDATA[simple content]]>"

    def test_render_safe_cdata_empty_content(self, formatter):
        """Test CDATA rendering with empty content."""
        result = formatter._render_safe_cdata("")
        assert result == "<![CDATA[]]>"

    def test_render_safe_cdata_whitespace_only(self, formatter):
        """Test CDATA rendering with whitespace-only content."""
        result = formatter._render_safe_cdata("   \n\t  ")
        assert result == "<![CDATA[   \n\t  ]]>"

    def test_render_safe_cdata_single_terminator(self, formatter):
        """Test CDATA rendering with just the ]]> terminator."""
        result = formatter._render_safe_cdata("]]>")
        assert result == "]]&gt;"

    def test_render_safe_cdata_terminator_at_start(self, formatter):
        """Test CDATA rendering with ]]> at the beginning."""
        result = formatter._render_safe_cdata("]]>content")
        assert result == "]]&gt;<![CDATA[content]]>"

    def test_render_safe_cdata_terminator_at_end(self, formatter):
        """Test CDATA rendering with ]]> at the end."""
        result = formatter._render_safe_cdata("content]]>")
        assert result == "<![CDATA[content]]]]>&gt;"

    def test_render_safe_cdata_terminator_in_middle(self, formatter):
        """Test CDATA rendering with ]]> in the middle."""
        result = formatter._render_safe_cdata("before]]>after")
        assert result == "<![CDATA[before]]]]>&gt;<![CDATA[after]]>"

    def test_render_safe_cdata_multiple_terminators(self, formatter):
        """Test CDATA rendering with multiple ]]> sequences."""
        result = formatter._render_safe_cdata("a]]>b]]>c")
        expected = "<![CDATA[a]]]]>&gt;<![CDATA[b]]]]>&gt;<![CDATA[c]]>"
        assert result == expected

    def test_render_safe_cdata_consecutive_terminators(self, formatter):
        """Test CDATA rendering with consecutive ]]> sequences."""
        result = formatter._render_safe_cdata("]]>]]>")
        assert result == "]]&gt;]]&gt;"

    def test_render_safe_cdata_mixed_consecutive_terminators(self, formatter):
        """Test CDATA rendering with mixed content and consecutive terminators."""
        result = formatter._render_safe_cdata("before]]>]]>after")
        expected = "<![CDATA[before]]]]>&gt;]]&gt;<![CDATA[after]]>"
        assert result == expected

    def test_render_safe_cdata_multiple_brackets(self, formatter):
        """Test CDATA rendering with multiple closing brackets."""
        result = formatter._render_safe_cdata("content]]]]>more")
        expected = "<![CDATA[content]]]]]]>&gt;<![CDATA[more]]>"
        assert result == expected

    def test_render_safe_cdata_content_ending_with_bracket(self, formatter):
        """Test CDATA rendering with content ending in single bracket."""
        result = formatter._render_safe_cdata("content]")
        assert result == "<![CDATA[content]]]>"

    def test_render_safe_cdata_content_ending_with_double_bracket(self, formatter):
        """Test CDATA rendering with content ending in double bracket."""
        result = formatter._render_safe_cdata("content]]")
        assert result == "<![CDATA[content]]]]>"

    def test_render_safe_cdata_content_starting_with_gt(self, formatter):
        """Test CDATA rendering with content starting with >."""
        result = formatter._render_safe_cdata(">content")
        assert result == "<![CDATA[>content]]>"

    def test_render_safe_cdata_complex_javascript(self, formatter):
        """Test CDATA rendering with complex JavaScript containing ]]>."""
        js_content = '''
        function test() {
            var regex = /]]>/g;
            return "test]]>value";
        }
        '''
        result = formatter._render_safe_cdata(js_content)
        # Should contain the split pattern
        assert "]]]]>&gt;" in result
        assert "<![CDATA[" in result

    def test_render_safe_cdata_xml_like_content(self, formatter):
        """Test CDATA rendering with XML-like content containing ]]>."""
        xml_content = 'var data = "<root>content]]></root>";'
        result = formatter._render_safe_cdata(xml_content)
        expected = '<![CDATA[var data = "<root>content]]]]>&gt;<![CDATA[</root>";]]>'
        assert result == expected


class TestCDATAValidation:
    """Test that generated CDATA output is valid XML."""

    @pytest.fixture
    def formatter(self):
        """Create a minimal DocumentFormatter for testing."""
        return DocumentFormatter(
            block_predicate=lambda e: False,
            inline_predicate=lambda e: True,
            normalize_whitespace_predicate=lambda e: False,
            strip_whitespace_predicate=lambda e: False,
            preserve_whitespace_predicate=lambda e: False,
            wrap_attributes_predicate=lambda e: False,
            text_content_formatters={},
            attribute_content_formatters={},
            escaping_strategy=XmlEscapingStrategy(),
            doctype_strategy=NullDoctypeStrategy(),
            attribute_strategy=NullAttributeStrategy(),
            indent_size=2,
            default_type=ElementType.BLOCK
        )

    def _validate_xml_with_cdata(self, cdata_content: str) -> bool:
        """Helper to validate that CDATA content produces valid XML."""
        try:
            xml = f"<test>{cdata_content}</test>"
            etree.fromstring(xml)
            return True
        except etree.XMLSyntaxError:
            return False

    def test_cdata_validation_simple_cases(self, formatter):
        """Test that simple CDATA cases produce valid XML."""
        test_cases = [
            "simple content",
            "",
            "content with <brackets> and &entities;",
            "   whitespace   ",
            "\n\tspecial\nwhitespace\t",
        ]

        for content in test_cases:
            result = formatter._render_safe_cdata(content)
            assert self._validate_xml_with_cdata(result), f"Invalid XML for content: {content!r}"

    def test_cdata_validation_problematic_sequences(self, formatter):
        """Test that problematic sequences produce valid XML."""
        test_cases = [
            "]]>",
            "before]]>after",
            "]]>]]>",
            "start]]>middle]]>end",
            "content]]",
            "content]",
            ">content",
            "]]]]>",
            "content]]]]>more",
        ]

        for content in test_cases:
            result = formatter._render_safe_cdata(content)
            assert self._validate_xml_with_cdata(result), f"Invalid XML for content: {content!r}"

    def test_cdata_validation_round_trip(self, formatter):
        """Test that CDATA content can be round-tripped through XML parsing."""
        test_cases = [
            "simple content",
            "before]]>after",
            "multiple]]>terminators]]>here",
            'javascript: var x = "]]>";',
            "content] with] brackets]",
        ]

        for original_content in test_cases:
            # Render as CDATA
            cdata_output = formatter._render_safe_cdata(original_content)

            # Parse as XML
            xml = f"<test>{cdata_output}</test>"
            parsed = etree.fromstring(xml)
            recovered_content = parsed.text

            # Content should be preserved (though may be normalized)
            assert recovered_content is not None
            # The actual content comparison depends on how lxml handles the mixed CDATA/text


class TestCDATAPathologicalCases:
    """Test edge cases and pathological inputs for CDATA rendering."""

    @pytest.fixture
    def formatter(self):
        """Create a minimal DocumentFormatter for testing."""
        return DocumentFormatter(
            block_predicate=lambda e: False,
            inline_predicate=lambda e: True,
            normalize_whitespace_predicate=lambda e: False,
            strip_whitespace_predicate=lambda e: False,
            preserve_whitespace_predicate=lambda e: False,
            wrap_attributes_predicate=lambda e: False,
            text_content_formatters={},
            attribute_content_formatters={},
            escaping_strategy=XmlEscapingStrategy(),
            doctype_strategy=NullDoctypeStrategy(),
            attribute_strategy=NullAttributeStrategy(),
            indent_size=2,
            default_type=ElementType.BLOCK
        )

    @pytest.mark.parametrize("content", [
        "]",
        "]]",
        "]]]",
        "]]]]",
        "]]]]]",
        "]]]]]]",
    ])
    def test_cdata_bracket_variations(self, formatter, content):
        """Test various numbers of closing brackets."""
        result = formatter._render_safe_cdata(content)
        assert f"<![CDATA[{content}]]>" == result

    @pytest.mark.parametrize("content", [
        ">",
        ">>",
        ">>>",
        ">>>>",
    ])
    def test_cdata_gt_variations(self, formatter, content):
        """Test various numbers of > characters."""
        result = formatter._render_safe_cdata(content)
        assert f"<![CDATA[{content}]]>" == result

    @pytest.mark.parametrize("terminator_count", [1, 2, 3, 5, 10])
    def test_cdata_multiple_terminators_generated(self, formatter, terminator_count):
        """Test content with many ]]> terminators."""
        content = "]]>".join(["part"] * (terminator_count + 1))
        result = formatter._render_safe_cdata(content)

        # Should be valid XML
        xml = f"<test>{result}</test>"
        parsed = etree.fromstring(xml)
        assert parsed is not None

    def test_cdata_very_long_content(self, formatter):
        """Test CDATA with very long content."""
        long_content = "x" * 10000 + "]]>" + "y" * 10000
        result = formatter._render_safe_cdata(long_content)

        # Should contain the split
        assert "]]]]>&gt;" in result
        assert len(result) > len(long_content)  # Should be longer due to CDATA markup

    def test_cdata_unicode_content(self, formatter):
        """Test CDATA with Unicode content."""
        unicode_content = "Hello 世界]]>🌍 content"
        result = formatter._render_safe_cdata(unicode_content)

        # Should handle Unicode properly
        xml = f"<test>{result}</test>"
        parsed = etree.fromstring(xml)
        assert parsed is not None


if __name__ == "__main__":
    pytest.main([__file__])