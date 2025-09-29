"""Example demonstrating the derive() method for creating customized formatters."""

from markuplift import Html5Formatter, XmlFormatter, Formatter
from markuplift.predicates import tag_in, any_of, all_of, tag_equals


def demonstrate_derive_basic():
    """Basic example of deriving a new formatter from an existing one."""
    # Create a base formatter with some settings
    base_formatter = Formatter(block_when=tag_in("div", "p"), inline_when=tag_in("span", "em"), indent_size=2)

    # Derive a new formatter with different indentation
    compact_formatter = base_formatter.derive(indent_size=0)

    # Derive another formatter with additional block elements
    extended_formatter = base_formatter.derive(
        block_when=any_of(base_formatter.block_when, tag_in("section", "article", "aside"))
    )

    # Test HTML
    html = "<root><div>Content</div><section>More content</section></root>"

    print("Base formatter output (indent=2):")
    print(base_formatter.format_str(html))
    print()

    print("Compact formatter output (indent=0):")
    print(compact_formatter.format_str(html))
    print()

    print("Extended formatter output (with section as block):")
    print(extended_formatter.format_str(html))


def demonstrate_html5_derive():
    """Example of deriving from Html5Formatter to extend HTML5 defaults."""
    # Start with HTML5 defaults
    base_html = Html5Formatter()

    # Create a custom formatter that adds support for custom web components
    # while keeping all HTML5 defaults
    custom_html = base_html.derive(
        block_when=any_of(base_html.block_when, tag_in("custom-card", "custom-section", "custom-header")),
        inline_when=any_of(base_html.inline_when, tag_in("custom-icon", "custom-badge")),
    )

    # Test with mixed HTML5 and custom elements
    html = """
    <div>
        <custom-card>
            <custom-header>Title</custom-header>
            <p>This is a paragraph with <custom-icon></custom-icon> icon.</p>
            <custom-badge>NEW</custom-badge>
        </custom-card>
    </div>
    """

    print("Custom HTML5 formatter with web components:")
    print(custom_html.format_str(html))


def demonstrate_xml_derive():
    """Example of deriving from XmlFormatter for specialized XML formats."""
    # Create a base XML formatter for a specific document type
    doc_formatter = XmlFormatter(
        block_when=tag_in("chapter", "section", "paragraph"), inline_when=tag_in("emphasis", "code"), indent_size=4
    )

    # Derive a formatter for a different document variant
    # that adds support for additional elements
    extended_doc = doc_formatter.derive(
        block_when=any_of(doc_formatter.block_when, tag_in("note", "warning", "example")),
        preserve_whitespace_when=tag_equals("code-block"),
    )

    xml = """<?xml version="1.0"?>
    <document>
        <chapter>
            <section>
                <paragraph>Text with <emphasis>emphasis</emphasis>.</paragraph>
                <note>This is a note.</note>
                <code-block>
                    def example():
                        return "preserved"
                </code-block>
            </section>
        </chapter>
    </document>
    """

    print("Extended XML formatter:")
    print(extended_doc.format_str(xml))


def demonstrate_incremental_customization():
    """Example showing incremental customization through multiple derive() calls."""
    # Start with a minimal formatter
    base = Formatter(block_when=tag_in("div"))

    # Step 1: Add more block elements
    step1 = base.derive(block_when=any_of(base.block_when, tag_in("p", "section")))

    # Step 2: Add inline elements
    step2 = step1.derive(inline_when=tag_in("span", "em", "strong"))

    # Step 3: Add whitespace preservation for code
    step3 = step2.derive(preserve_whitespace_when=tag_in("pre", "code"))

    # Step 4: Adjust indentation
    final = step3.derive(indent_size=3)

    html = """<div>
        <p>Paragraph with <em>emphasis</em>.</p>
        <pre>  preserved  whitespace  </pre>
    </div>"""

    print("Final incrementally customized formatter:")
    print(final.format_str(html))


def demonstrate_combinator_usage():
    """Example showing how to use combinators with derive() to modify existing rules."""
    from markuplift.predicates import has_attribute, not_matching

    # Create a formatter with some rules
    base = Html5Formatter()

    # Derive a formatter that:
    # 1. Keeps all HTML5 block elements
    # 2. But excludes elements with 'inline' attribute from being blocks
    # 3. Adds custom elements with 'block' attribute as blocks
    custom = base.derive(
        block_when=any_of(all_of(base.block_when, not_matching(has_attribute("inline"))), has_attribute("block"))
    )

    html = """
    <div>Normal div (block)</div>
    <div inline="true">Inline div</div>
    <custom block="true">Block custom element</custom>
    <span>Normal span (inline)</span>
    """

    print("Formatter with attribute-based block/inline classification:")
    print(custom.format_str(html))


if __name__ == "__main__":
    print("=" * 60)
    print("Basic derive() example:")
    print("=" * 60)
    demonstrate_derive_basic()
    print()

    print("=" * 60)
    print("HTML5 derive() example:")
    print("=" * 60)
    demonstrate_html5_derive()
    print()

    print("=" * 60)
    print("XML derive() example:")
    print("=" * 60)
    demonstrate_xml_derive()
    print()

    print("=" * 60)
    print("Incremental customization example:")
    print("=" * 60)
    demonstrate_incremental_customization()
    print()

    print("=" * 60)
    print("Combinator usage example:")
    print("=" * 60)
    demonstrate_combinator_usage()
