from inspect import cleandoc
from lxml import etree
import pytest

from helpers.predicates import is_block_or_root, is_inline
from markuplift.formatter import Formatter, PredicateFactory


def test_formatter_with_block_factory():
    """Test Formatter using a block predicate factory."""
    example = "<root><div>content</div></root>"

    def block_factory(root: etree._Element) -> callable:
        return lambda e: e.tag in ("root", "div")

    formatter = Formatter(block_predicate_factory=block_factory)
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <div>content</div>
        </root>
    """)
    assert actual == expected


def test_formatter_with_inline_factory():
    """Test Formatter using an inline predicate factory."""
    example = "<root><span>content</span></root>"

    def block_factory(root: etree._Element) -> callable:
        return lambda e: e.tag == "root"

    def inline_factory(root: etree._Element) -> callable:
        return lambda e: e.tag == "span"

    formatter = Formatter(
        block_predicate_factory=block_factory,
        inline_predicate_factory=inline_factory
    )
    actual = formatter.format_str(example)
    expected = "<root><span>content</span></root>"
    assert actual == expected


def test_formatter_with_normalize_whitespace_factory():
    """Test Formatter using a normalize whitespace predicate factory."""
    example = cleandoc("""
        <root>
            <p>Text with    extra   spaces
            and newlines</p>
        </root>
    """)

    def block_factory(root: etree._Element) -> callable:
        return lambda e: e.tag in ("root", "p")

    def normalize_factory(root: etree._Element) -> callable:
        return lambda e: e.tag == "p"

    formatter = Formatter(
        block_predicate_factory=block_factory,
        normalize_whitespace_predicate_factory=normalize_factory
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <p>Text with extra spaces and newlines</p>
        </root>
    """)
    assert actual == expected


def test_formatter_with_preserve_whitespace_factory():
    """Test Formatter using a preserve whitespace predicate factory."""
    example = cleandoc("""
        <root>
            <pre>  preserved  whitespace  </pre>
        </root>
    """)

    def block_factory(root: etree._Element) -> callable:
        return lambda e: e.tag in ("root", "pre")

    def preserve_factory(root: etree._Element) -> callable:
        return lambda e: e.tag == "pre"

    formatter = Formatter(
        block_predicate_factory=block_factory,
        preserve_whitespace_predicate_factory=preserve_factory
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <pre>  preserved  whitespace  </pre>
        </root>
    """)
    assert actual == expected


def test_formatter_with_strip_whitespace_factory():
    """Test Formatter using a strip whitespace predicate factory."""
    example = cleandoc("""
        <root>
            <div>   text with spaces   </div>
        </root>
    """)

    def block_factory(root: etree._Element) -> callable:
        return lambda e: e.tag in ("root", "div")

    def strip_factory(root: etree._Element) -> callable:
        return lambda e: e.tag == "div"

    formatter = Formatter(
        block_predicate_factory=block_factory,
        strip_whitespace_predicate_factory=strip_factory
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <div>text with spaces</div>
        </root>
    """)
    assert actual == expected


def test_formatter_with_wrap_attributes_factory():
    """Test Formatter using a wrap attributes predicate factory."""
    example = '<root><div class="test" id="example" data-value="123">content</div></root>'

    def block_factory(root: etree._Element) -> callable:
        return lambda e: e.tag in ("root", "div")

    def wrap_factory(root: etree._Element) -> callable:
        return lambda e: e.tag == "div"

    formatter = Formatter(
        block_predicate_factory=block_factory,
        wrap_attributes_predicate_factory=wrap_factory
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <div
            class="test"
            id="example"
            data-value="123"
          >content</div>
        </root>
    """)
    assert actual == expected


def test_formatter_with_text_formatters():
    """Test Formatter using text content formatters with factories."""
    example = "<root><code>function(){return true;}</code></root>"

    def block_factory(root: etree._Element) -> callable:
        return lambda e: e.tag in ("root", "code")

    def code_factory(root: etree._Element) -> callable:
        return lambda e: e.tag == "code"

    def simple_js_formatter(text, doc_formatter, physical_level):
        # Simple mock formatter that adds spaces around braces
        return text.replace("{", " { ").replace("}", " } ")

    formatter = Formatter(
        block_predicate_factory=block_factory,
        text_content_formatters={code_factory: simple_js_formatter}
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <code>function() { return true; } </code>
        </root>
    """)
    assert actual == expected


def test_formatter_with_multiple_factories():
    """Test Formatter using multiple predicate factories together."""
    example = cleandoc("""
        <root>
            <div class="container">
                <p>Text with    spaces</p>
                <span>inline content</span>
            </div>
        </root>
    """)

    def block_factory(root: etree._Element) -> callable:
        return lambda e: e.tag in ("root", "div", "p")

    def inline_factory(root: etree._Element) -> callable:
        return lambda e: e.tag == "span"

    def normalize_factory(root: etree._Element) -> callable:
        return lambda e: e.tag == "p"

    def wrap_factory(root: etree._Element) -> callable:
        return lambda e: e.tag == "div"

    formatter = Formatter(
        block_predicate_factory=block_factory,
        inline_predicate_factory=inline_factory,
        normalize_whitespace_predicate_factory=normalize_factory,
        wrap_attributes_predicate_factory=wrap_factory
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <div
            class="container"
          >
            <p>Text with spaces</p>
                <span>inline content</span>
            </div>
        </root>
    """)
    assert actual == expected


def test_formatter_factory_receives_correct_root():
    """Test that predicate factories receive the correct document root."""
    example = "<document><item id='test'>content</item></document>"

    received_roots = []

    def block_factory(root: etree._Element) -> callable:
        received_roots.append(root.tag)
        return lambda e: e.tag in ("document", "item")

    formatter = Formatter(block_predicate_factory=block_factory)
    formatter.format_str(example)

    # Factory should be called once with the document root
    assert len(received_roots) == 1
    assert received_roots[0] == "document"


def test_formatter_with_none_factories():
    """Test Formatter with None factory values (should use defaults)."""
    example = "<root><div>content</div></root>"

    formatter = Formatter(
        block_predicate_factory=None,
        inline_predicate_factory=None,
        normalize_whitespace_predicate_factory=None,
        preserve_whitespace_predicate_factory=None,
        strip_whitespace_predicate_factory=None,
        wrap_attributes_predicate_factory=None,
        text_content_formatters=None
    )
    actual = formatter.format_str(example)

    # With no predicates, should default to block behavior
    expected = cleandoc("""
        <root>
          <div>content</div>
        </root>
    """)
    assert actual == expected


def test_formatter_factory_caching():
    """Test that predicate factories are called once per document, not per element."""
    example = "<root><div>first</div><div>second</div><div>third</div></root>"

    call_count = 0

    def block_factory(root: etree._Element) -> callable:
        nonlocal call_count
        call_count += 1
        return lambda e: e.tag in ("root", "div")

    formatter = Formatter(block_predicate_factory=block_factory)
    formatter.format_str(example)

    # Factory should be called exactly once, not once per element
    assert call_count == 1


def test_formatter_with_custom_defaults():
    """Test Formatter with custom default settings."""
    example = "<root><unknown>content</unknown></root>"

    def block_factory(root: etree._Element) -> callable:
        return lambda e: e.tag == "root"  # Only root is block

    formatter = Formatter(
        block_predicate_factory=block_factory,
        default_type="inline",
        indent_size=4
    )
    actual = formatter.format_str(example)

    # Unknown element should be treated as block with 4-space indentation
    expected = cleandoc("""
        <root>
            <unknown>content</unknown>
        </root>
    """)
    assert actual == expected