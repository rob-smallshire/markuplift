"""Example demonstrating XML namespace support in MarkupLift.

This example shows how to:
1. Format namespaced XML documents (e.g., SVG)
2. Use Clark notation in predicates for namespaced elements
3. Use QName objects for better readability
4. Preserve namespace prefixes from the original document
"""

from lxml import etree
from markuplift import XmlFormatter, ElementType
from markuplift.predicates import tag_in, tag_equals


def format_svg_with_namespaces():
    """Format an SVG document using Clark notation for namespaced elements."""
    svg_input = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:bx="https://boxy-svg.com" viewBox="0 0 500 500"><defs><linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:rgb(255,255,0);stop-opacity:1"/><stop offset="100%" style="stop-color:rgb(255,0,0);stop-opacity:1"/></linearGradient></defs><bx:grid x="0" y="0"/><rect x="10" y="10" width="100" height="100" fill="url(#gradient1)"/><circle cx="250" cy="250" r="50" fill="blue"/><use xlink:href="#gradient1"/><text x="50" y="150" xml:space="preserve">  Preserved   whitespace  </text></svg>"""

    # Define block elements using Clark notation
    svg_block_elements = tag_in(
        "{http://www.w3.org/2000/svg}svg",
        "{http://www.w3.org/2000/svg}defs",
        "{http://www.w3.org/2000/svg}linearGradient",
        "{http://www.w3.org/2000/svg}rect",
        "{http://www.w3.org/2000/svg}circle",
        "{http://www.w3.org/2000/svg}use",
        "{http://www.w3.org/2000/svg}text",
        "{https://boxy-svg.com}grid",  # Custom namespace
    )

    formatter = XmlFormatter(
        block_when=svg_block_elements,
        preserve_whitespace_when=tag_in("{http://www.w3.org/2000/svg}text"),
        default_type=ElementType.INLINE,
    )

    return formatter.format_str(svg_input)


def format_svg_with_qnames():
    """Format an SVG document using QName objects for better readability."""
    svg_input = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:bx="https://boxy-svg.com" viewBox="0 0 500 500"><defs><linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:rgb(255,255,0);stop-opacity:1"/><stop offset="100%" style="stop-color:rgb(255,0,0);stop-opacity:1"/></linearGradient></defs><bx:grid x="0" y="0"/><rect x="10" y="10" width="100" height="100" fill="url(#gradient1)"/><circle cx="250" cy="250" r="50" fill="blue"/><use xlink:href="#gradient1"/><text x="50" y="150" xml:space="preserve">  Preserved   whitespace  </text></svg>"""

    # Define namespace constants for readability
    SVG_NS = "http://www.w3.org/2000/svg"
    BX_NS = "https://boxy-svg.com"

    # Define block elements using QName objects
    svg_block_elements = tag_in(
        etree.QName(SVG_NS, "svg"),
        etree.QName(SVG_NS, "defs"),
        etree.QName(SVG_NS, "linearGradient"),
        etree.QName(SVG_NS, "rect"),
        etree.QName(SVG_NS, "circle"),
        etree.QName(SVG_NS, "use"),
        etree.QName(SVG_NS, "text"),
        etree.QName(BX_NS, "grid"),
    )

    formatter = XmlFormatter(
        block_when=svg_block_elements,
        preserve_whitespace_when=tag_equals(etree.QName(SVG_NS, "text")),
        default_type=ElementType.INLINE,
    )

    return formatter.format_str(svg_input)


def format_mixed_namespaces():
    """Format XML with multiple namespaces including default namespace changes."""
    xml_input = """<html xmlns="http://www.w3.org/1999/xhtml"><body><p>This is HTML content.</p><svg xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100"/><circle r="50"/></svg><p>More HTML content.</p></body></html>"""

    XHTML_NS = "http://www.w3.org/1999/xhtml"
    SVG_NS = "http://www.w3.org/2000/svg"

    # Define block elements from both namespaces
    block_elements = tag_in(
        etree.QName(XHTML_NS, "html"),
        etree.QName(XHTML_NS, "body"),
        etree.QName(XHTML_NS, "p"),
        etree.QName(SVG_NS, "svg"),
        etree.QName(SVG_NS, "rect"),
        etree.QName(SVG_NS, "circle"),
    )

    formatter = XmlFormatter(
        block_when=block_elements,
        default_type=ElementType.INLINE,
    )

    return formatter.format_str(xml_input)


if __name__ == "__main__":
    print("=== SVG with Clark Notation ===")
    print(format_svg_with_namespaces())
    print()

    print("=== SVG with QName Objects ===")
    print(format_svg_with_qnames())
    print()

    print("=== Mixed Namespaces (XHTML + SVG) ===")
    print(format_mixed_namespaces())
