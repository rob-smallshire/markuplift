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


def test_formatter_reuse_across_different_documents():
    """Test that a single Formatter instance can efficiently handle multiple different documents."""
    def block_factory(root: etree._Element) -> callable:
        # Factory that adapts to different document structures
        return lambda e: e.tag in ("html", "body", "div", "p", "root", "container", "item")

    formatter = Formatter(block_predicate_factory=block_factory)

    # Test with HTML-like structure
    html_doc = "<html><body><div>HTML content</div></body></html>"
    html_result = formatter.format_str(html_doc)
    expected_html = cleandoc("""
        <html>
          <body>
            <div>HTML content</div>
          </body>
        </html>
    """)
    assert html_result == expected_html

    # Test with different XML structure
    xml_doc = "<root><container><item>XML content</item></container></root>"
    xml_result = formatter.format_str(xml_doc)
    expected_xml = cleandoc("""
        <root>
          <container>
            <item>XML content</item>
          </container>
        </root>
    """)
    assert xml_result == expected_xml


def test_formatter_factory_called_once_per_document_multi_use():
    """Test that factories are called exactly once per document, even when reusing Formatter."""
    call_count = 0
    documents_seen = []

    def tracking_block_factory(root: etree._Element) -> callable:
        nonlocal call_count
        call_count += 1
        documents_seen.append(root.tag)
        return lambda e: e.tag in ("root", "div", "html", "body")

    formatter = Formatter(block_predicate_factory=tracking_block_factory)

    # Format first document
    formatter.format_str("<root><div>first</div></root>")
    assert call_count == 1
    assert documents_seen == ["root"]

    # Format second document
    formatter.format_str("<html><body>second</body></html>")
    assert call_count == 2
    assert documents_seen == ["root", "html"]

    # Format first document again
    formatter.format_str("<root><div>third</div></root>")
    assert call_count == 3
    assert documents_seen == ["root", "html", "root"]


def test_formatter_with_xpath_like_factory():
    """Test Formatter with factory that simulates XPath-based predicate creation."""
    def xpath_like_factory(root: etree._Element) -> callable:
        # Simulate XPath evaluation: find all elements with specific attributes
        elements_with_class = set()
        for elem in root.iter():
            if 'class' in elem.attrib:
                elements_with_class.add(elem)

        return lambda e: e in elements_with_class

    formatter = Formatter(
        block_predicate_factory=lambda root: lambda e: e.tag in ("root", "div", "p"),
        wrap_attributes_predicate_factory=xpath_like_factory
    )

    example = '<root><div class="styled">content</div><p>no class</p></root>'
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <div
            class="styled"
          >content</div>
          <p>no class</p>
        </root>
    """)
    assert actual == expected


def test_formatter_factory_exception_handling():
    """Test Formatter behavior when factory raises an exception."""
    def failing_factory(root: etree._Element) -> callable:
        raise ValueError("Factory failed")

    formatter = Formatter(
        block_predicate_factory=lambda root: lambda e: e.tag == "root",
        normalize_whitespace_predicate_factory=failing_factory
    )

    example = "<root><p>text</p></root>"

    # Should raise the factory exception
    with pytest.raises(ValueError, match="Factory failed"):
        formatter.format_str(example)


def test_formatter_with_document_specific_predicates():
    """Test that factory predicates can make document-specific decisions."""
    def document_aware_factory(root: etree._Element) -> callable:
        # Different behavior based on document type
        if root.tag == "html":
            # HTML mode: treat divs and ps as blocks
            return lambda e: e.tag in ("html", "body", "div", "p")
        else:
            # XML mode: treat containers and items as blocks
            return lambda e: e.tag in ("root", "container", "item")

    formatter = Formatter(block_predicate_factory=document_aware_factory)

    # Test HTML document
    html_doc = "<html><body><div>content</div></body></html>"
    html_result = formatter.format_str(html_doc)
    expected_html = cleandoc("""
        <html>
          <body>
            <div>content</div>
          </body>
        </html>
    """)
    assert html_result == expected_html

    # Test XML document with different structure
    xml_doc = "<root><container><item>content</item></container></root>"
    xml_result = formatter.format_str(xml_doc)
    expected_xml = cleandoc("""
        <root>
          <container>
            <item>content</item>
          </container>
        </root>
    """)
    assert xml_result == expected_xml


def test_formatter_complex_text_formatter_factories():
    """Test Formatter with text formatters using factory-based predicate keys."""
    def code_factory(root: etree._Element) -> callable:
        # Find code elements with specific type attributes
        code_elements = set()
        for elem in root.iter("code"):
            if elem.get("type") == "javascript":
                code_elements.add(elem)
        return lambda e: e in code_elements

    def css_factory(root: etree._Element) -> callable:
        return lambda e: e.tag == "style"

    def js_formatter(text, doc_formatter, physical_level):
        return text.replace(";", ";\n" + "  " * physical_level)

    def css_formatter(text, doc_formatter, physical_level):
        return text.replace("}", "}\n" + "  " * physical_level)

    formatter = Formatter(
        block_predicate_factory=lambda root: lambda e: e.tag in ("root", "code", "style"),
        text_content_formatters={
            code_factory: js_formatter,
            css_factory: css_formatter
        }
    )

    example = cleandoc("""
        <root>
            <code type="javascript">var x=1;var y=2;</code>
            <code type="python">print("hello")</code>
            <style>body{color:red}div{margin:0}</style>
        </root>
    """)

    result = formatter.format_str(example)

    # Should format JavaScript but not Python code, and should format CSS
    assert "var x=1;\n  var y=2;" in result
    assert 'print("hello")' in result  # Unchanged
    assert "body{color:red}\n  div{margin:0}" in result


def test_formatter_with_namespace_aware_factory():
    """Test Formatter with factory that handles namespaced elements."""
    def namespace_factory(root: etree._Element) -> callable:
        # Find elements in specific namespaces
        ns_elements = set()
        for elem in root.iter():
            if elem.tag.startswith("{http://example.com/ns}"):
                ns_elements.add(elem)
        return lambda e: e in ns_elements

    formatter = Formatter(
        block_predicate_factory=lambda root: lambda e: e.tag in ("root", "{http://example.com/ns}block"),
        wrap_attributes_predicate_factory=namespace_factory
    )

    example = '<root xmlns:ns="http://example.com/ns"><ns:block ns:attr="value">content</ns:block></root>'
    result = formatter.format_str(example)

    # Should wrap attributes for namespaced elements
    assert 'attr="value"' in result  # Namespace prefix stripped by lxml
    assert result.count('\n') > 1  # Should have line breaks from attribute wrapping


def test_formatter_empty_and_none_text_formatters():
    """Test Formatter behavior with empty and None text formatter dictionaries."""
    def block_factory(root: etree._Element) -> callable:
        return lambda e: e.tag in ("root", "code")

    # Test with empty dict
    formatter1 = Formatter(
        block_predicate_factory=block_factory,
        text_content_formatters={}
    )

    # Test with None
    formatter2 = Formatter(
        block_predicate_factory=block_factory,
        text_content_formatters=None
    )

    example = "<root><code>unchanged text</code></root>"
    expected = cleandoc("""
        <root>
          <code>unchanged text</code>
        </root>
    """)

    assert formatter1.format_str(example) == expected
    assert formatter2.format_str(example) == expected


def test_formatter_factory_predicate_consistency():
    """Test that factory-generated predicates maintain consistency across multiple calls."""
    evaluation_log = []

    def logging_factory(root: etree._Element) -> callable:
        target_elements = {elem for elem in root.iter() if elem.get("important") == "true"}

        def predicate(element):
            evaluation_log.append(element.tag)
            return element in target_elements

        return predicate

    formatter = Formatter(
        block_predicate_factory=lambda root: lambda e: e.tag in ("root", "div"),
        wrap_attributes_predicate_factory=logging_factory
    )

    example = '<root><div important="true" class="test">content</div><div>other</div></root>'
    result = formatter.format_str(example)

    # Verify the important div got attribute wrapping
    assert 'class="test"' in result
    assert result.count('\n') > 2  # Should have attribute wrapping

    # Verify predicate was called for elements during formatting
    assert "div" in evaluation_log