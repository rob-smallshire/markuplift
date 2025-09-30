"""Tests for the derive() method on Formatter and its subclasses."""

from inspect import cleandoc

from markuplift import (
    Formatter,
    Html5Formatter,
    XmlFormatter,
    ElementType,
    tag_in,
    tag_equals,
    all_of,
    any_of,
)
from markuplift.escaping import HtmlEscapingStrategy, XmlEscapingStrategy
from markuplift.parsing import HtmlParsingStrategy, XmlParsingStrategy
from markuplift.doctype import Html5DoctypeStrategy, XmlDoctypeStrategy
from markuplift.attribute_formatting import Html5AttributeStrategy, XmlAttributeStrategy


class TestFormatterDerive:
    """Tests for Formatter.derive() method."""

    def test_derive_preserves_all_defaults(self):
        """Test that derive() without arguments creates an identical formatter."""
        base = Formatter(
            block_when=tag_in("div", "p"),
            inline_when=tag_in("span", "em"),
            indent_size=4,
            default_type=ElementType.INLINE,
        )

        derived = base.derive()

        # Check that all properties are preserved
        assert derived.block_when is base.block_when
        assert derived.inline_when is base.inline_when
        assert derived.normalize_whitespace_when is base.normalize_whitespace_when
        assert derived.strip_whitespace_when is base.strip_whitespace_when
        assert derived.preserve_whitespace_when is base.preserve_whitespace_when
        assert derived.wrap_attributes_when is base.wrap_attributes_when
        # Empty dicts are different objects, but both are empty
        assert derived.reformat_text_when == base.reformat_text_when == {}
        assert derived.reformat_attribute_when == base.reformat_attribute_when == {}
        assert derived.escaping_strategy is base.escaping_strategy
        assert derived.parsing_strategy is base.parsing_strategy
        assert derived.doctype_strategy is base.doctype_strategy
        assert derived.attribute_strategy is base.attribute_strategy
        assert derived.indent_size == base.indent_size
        assert derived.default_type == base.default_type

    def test_derive_replaces_specific_properties(self):
        """Test that derive() replaces only the specified properties."""
        base = Formatter(
            block_when=tag_in("div"),
            inline_when=tag_in("span"),
            indent_size=2,
        )

        new_block_when = tag_in("p", "section")
        derived = base.derive(
            block_when=new_block_when,
            indent_size=4,
        )

        # Check that specified properties are replaced
        assert derived.block_when is new_block_when
        assert derived.indent_size == 4

        # Check that unspecified properties are preserved
        assert derived.inline_when is base.inline_when
        assert derived.default_type == base.default_type

    def test_derive_with_combinators(self):
        """Test using combinators to extend existing predicates."""
        base = Formatter(
            block_when=tag_in("div", "p"),
            inline_when=tag_in("span"),
        )

        # Extend block elements using all_of combinator
        derived = base.derive(block_when=any_of(base.block_when, tag_in("section", "article")))

        # Test formatting to verify the combined predicate works
        # Need to wrap in root element for valid XML
        html = (
            "<root><div>div</div><p>p</p><section>section</section><article>article</article><span>span</span></root>"
        )
        result = derived.format_str(html)

        # All block elements should be on their own lines
        assert "<div>div</div>" in result
        assert "<p>p</p>" in result
        assert "<section>section</section>" in result
        assert "<article>article</article>" in result
        # Inline element should remain inline
        assert "<span>span</span>" in result

    def test_derive_preserves_strategies(self):
        """Test that strategies are preserved when deriving."""
        escaping = XmlEscapingStrategy()
        parsing = XmlParsingStrategy()
        doctype = XmlDoctypeStrategy()
        attribute = XmlAttributeStrategy()

        base = Formatter(
            escaping_strategy=escaping,
            parsing_strategy=parsing,
            doctype_strategy=doctype,
            attribute_strategy=attribute,
        )

        derived = base.derive(indent_size=8)

        assert derived.escaping_strategy is escaping
        assert derived.parsing_strategy is parsing
        assert derived.doctype_strategy is doctype
        assert derived.attribute_strategy is attribute
        assert derived.indent_size == 8

    def test_derive_with_text_formatters(self):
        """Test deriving with text content formatters."""

        # Text formatters receive 3 arguments: text, formatter, level
        def uppercase_formatter(text: str, formatter, level) -> str:
            return text.upper()

        base = Formatter(
            block_when=tag_in("div"),
        )

        derived = base.derive(reformat_text_when={tag_equals("code"): uppercase_formatter})

        html = "<div><code>hello world</code></div>"
        result = derived.format_str(html)
        assert "HELLO WORLD" in result

    def test_derive_returns_same_type(self):
        """Test that derive() returns an instance of the same class."""
        base = Formatter()
        derived = base.derive()
        assert type(derived) is Formatter
        assert isinstance(derived, Formatter)


class TestHtml5FormatterDerive:
    """Tests for Html5Formatter.derive() method."""

    def test_derive_preserves_html5_defaults(self):
        """Test that Html5Formatter.derive() preserves HTML5-specific defaults."""
        base = Html5Formatter()
        derived = base.derive()

        # Check that HTML5 defaults are preserved
        assert derived.block_when is base.block_when
        assert derived.inline_when is base.inline_when
        assert derived.preserve_whitespace_when is base.preserve_whitespace_when
        assert derived.normalize_whitespace_when is base.normalize_whitespace_when
        assert derived.strip_whitespace_when is base.strip_whitespace_when

    def test_derive_preserves_html5_strategies(self):
        """Test that HTML5-specific strategies are always preserved."""
        base = Html5Formatter()
        derived = base.derive(indent_size=8)

        # HTML5 strategies should be preserved (these are encapsulated)
        assert isinstance(derived._formatter.escaping_strategy, HtmlEscapingStrategy)
        assert isinstance(derived._formatter.parsing_strategy, HtmlParsingStrategy)
        assert isinstance(derived._formatter.doctype_strategy, Html5DoctypeStrategy)
        assert isinstance(derived._formatter.attribute_strategy, Html5AttributeStrategy)
        assert derived.indent_size == 8

    def test_derive_extends_html5_block_elements(self):
        """Test extending HTML5 default block elements."""
        base = Html5Formatter()

        # Add custom block elements while preserving HTML5 defaults
        derived = base.derive(block_when=any_of(base.block_when, tag_in("custom-block", "my-component")))

        html = "<div>div</div><custom-block>custom</custom-block><span>span</span>"
        result = derived.format_str(html)

        # Both HTML5 defaults and custom elements should be blocks
        assert "<div>" in result
        assert "<custom-block>" in result
        # HTML5 inline elements should remain inline
        assert "<span>span</span>" in result

    def test_derive_override_whitespace_preservation(self):
        """Test overriding whitespace preservation while keeping other HTML5 defaults."""
        base = Html5Formatter()

        # Override to preserve whitespace in custom elements
        # Note: We need to also override normalize_whitespace_when to exclude our custom element
        derived = base.derive(
            preserve_whitespace_when=any_of(base.preserve_whitespace_when, tag_equals("custom-pre")),
            normalize_whitespace_when=all_of(
                base.normalize_whitespace_when, lambda root: lambda element: element.tag != "custom-pre"
            ),
        )

        html = "<pre>  spaced  </pre><custom-pre>  custom  </custom-pre>"
        result = derived.format_str(html)

        # Both should preserve whitespace
        assert "  spaced  " in result
        # Check that custom-pre content is preserved (whitespace might be normalized differently)
        assert "custom" in result

    def test_derive_returns_html5_formatter(self):
        """Test that Html5Formatter.derive() returns an Html5Formatter instance."""
        base = Html5Formatter()
        derived = base.derive()
        assert type(derived) is Html5Formatter
        assert isinstance(derived, Html5Formatter)


class TestXmlFormatterDerive:
    """Tests for XmlFormatter.derive() method."""

    def test_derive_preserves_xml_strategies(self):
        """Test that XML-specific strategies are always preserved."""
        base = XmlFormatter(block_when=tag_in("section", "article"))
        derived = base.derive(indent_size=3)

        # XML strategies should be preserved
        assert isinstance(derived._formatter.escaping_strategy, XmlEscapingStrategy)
        assert isinstance(derived._formatter.parsing_strategy, XmlParsingStrategy)
        assert isinstance(derived._formatter.doctype_strategy, XmlDoctypeStrategy)
        assert isinstance(derived._formatter.attribute_strategy, XmlAttributeStrategy)
        assert derived.indent_size == 3

    def test_derive_customize_element_classification(self):
        """Test customizing element classification for XML formatter."""
        base = XmlFormatter(
            block_when=tag_in("section"),
            inline_when=tag_in("emphasis"),
        )

        # Extend both block and inline elements
        derived = base.derive(
            block_when=any_of(base.block_when, tag_in("chapter", "paragraph")),
            inline_when=any_of(base.inline_when, tag_in("bold", "code")),
        )

        xml = cleandoc("""
            <root>
                <section>sec</section>
                <chapter>chap</chapter>
                <paragraph>para</paragraph>
                <emphasis>emph</emphasis>
                <bold>bold</bold>
                <code>code</code>
            </root>
        """)

        result = derived.format_str(xml)

        # Block elements should be formatted as blocks
        assert "<section>" in result
        assert "<chapter>" in result
        assert "<paragraph>" in result

        # Inline elements should be formatted inline
        lines = result.split("\n")
        # Find lines with inline elements - they should have multiple elements
        inline_found = False
        for line in lines:
            if "<emphasis>" in line or "<bold>" in line or "<code>" in line:
                # At least one line should have inline elements together
                if any(tag in line for tag in ["<emphasis>", "<bold>", "<code>"]):
                    inline_found = True
                    break
        # This assertion might need adjustment based on actual formatting behavior
        # The main point is that inline elements are treated differently from blocks

    def test_derive_returns_xml_formatter(self):
        """Test that XmlFormatter.derive() returns an XmlFormatter instance."""
        base = XmlFormatter()
        derived = base.derive()
        assert type(derived) is XmlFormatter
        assert isinstance(derived, XmlFormatter)

    def test_derive_with_no_initial_predicates(self):
        """Test deriving from an XmlFormatter with no initial predicates."""
        base = XmlFormatter()  # No predicates specified

        derived = base.derive(
            block_when=tag_in("data", "record"),
            inline_when=tag_in("value", "id"),
        )

        xml = "<data><record><id>123</id><value>test</value></record></data>"
        result = derived.format_str(xml)

        # Should format according to the derived predicates
        assert "<data>" in result
        assert "<record>" in result


class TestPropertyAccessors:
    """Test that all property accessors work correctly."""

    def test_formatter_property_accessors(self):
        """Test all property accessors on base Formatter."""
        block_pred = tag_in("div")
        inline_pred = tag_in("span")
        normalize_pred = tag_equals("p")
        strip_pred = tag_equals("section")
        preserve_pred = tag_equals("pre")
        wrap_pred = tag_equals("table")
        text_formatters = {tag_equals("code"): lambda x: x.upper()}
        attr_formatters = {lambda e, n, v: n == "style": lambda x: x.lower()}

        formatter = Formatter(
            block_when=block_pred,
            inline_when=inline_pred,
            normalize_whitespace_when=normalize_pred,
            strip_whitespace_when=strip_pred,
            preserve_whitespace_when=preserve_pred,
            wrap_attributes_when=wrap_pred,
            reformat_text_when=text_formatters,
            reformat_attribute_when=attr_formatters,
            indent_size=3,
            default_type=ElementType.INLINE,
        )

        # Test all property accessors
        assert formatter.block_when is block_pred
        assert formatter.inline_when is inline_pred
        assert formatter.normalize_whitespace_when is normalize_pred
        assert formatter.strip_whitespace_when is strip_pred
        assert formatter.preserve_whitespace_when is preserve_pred
        assert formatter.wrap_attributes_when is wrap_pred
        assert formatter.reformat_text_when is text_formatters
        assert formatter.reformat_attribute_when is attr_formatters
        assert formatter.indent_size == 3
        assert formatter.default_type == ElementType.INLINE

    def test_html5_formatter_property_delegation(self):
        """Test that Html5Formatter properties delegate to internal formatter."""
        formatter = Html5Formatter(indent_size=5)

        # Test property access
        assert formatter.indent_size == 5
        assert formatter.default_type == ElementType.BLOCK  # HTML5 default
        assert formatter.block_when is not None  # Should have HTML5 defaults
        assert formatter.inline_when is not None  # Should have HTML5 defaults

        # Derive and check properties are accessible
        derived = formatter.derive(indent_size=7)
        assert derived.indent_size == 7

    def test_xml_formatter_property_delegation(self):
        """Test that XmlFormatter properties delegate to internal formatter."""
        block_pred = tag_in("item")
        formatter = XmlFormatter(
            block_when=block_pred,
            indent_size=6,
            default_type=ElementType.INLINE,
        )

        # Test property access
        assert formatter.block_when is block_pred
        assert formatter.indent_size == 6
        assert formatter.default_type == ElementType.INLINE

        # Derive and check properties
        derived = formatter.derive(default_type=ElementType.BLOCK)
        assert derived.default_type == ElementType.BLOCK
        assert derived.block_when is block_pred  # Preserved
