#!/usr/bin/env python3
"""
Test different serialization strategies for SVG in HTML5 documents.

Question: Should we serialize XML-parsed SVG subtrees with:
1. XML serialization (allows self-closing tags like <rect />)
2. HTML serialization (no self-closing for non-void elements)
3. Hybrid approach (XML serialization but constrained to HTML-compatible output)
"""

from lxml import etree, html as lxml_html


def test_xml_serialization_in_html():
    """Test what happens when we embed XML-serialized SVG in HTML."""
    print("=== Test 1: XML-Serialized SVG in HTML ===\n")

    # Parse SVG as XML (preserves case)
    svg_source = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect x="10" y="10" width="30" height="30" fill="blue"/>
    <textPath href="#path">Text</textPath>
</svg>'''

    svg_tree = etree.fromstring(svg_source.encode())

    # Serialize with XML method
    xml_output = etree.tostring(svg_tree, method='xml', encoding='unicode', pretty_print=True)
    print("XML serialization:")
    print(xml_output)

    # Serialize with HTML method
    html_output = etree.tostring(svg_tree, method='html', encoding='unicode', pretty_print=True)
    print("HTML serialization:")
    print(html_output)

    # Serialize with C14N method (canonical XML) - returns bytes
    c14n_output = etree.tostring(svg_tree, method='c14n').decode('utf-8')
    print("C14N serialization:")
    print(c14n_output)
    print()


def test_embedding_in_full_document():
    """Test embedding XML-parsed SVG into HTML-parsed document."""
    print("=== Test 2: Embedding Strategies ===\n")

    html_source = """<!DOCTYPE html>
<html>
<body>
    <p>Before SVG</p>
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <textpath>Wrong case</textpath>
    </svg>
    <p>After SVG</p>
</body>
</html>"""

    # Parse as HTML (lowercases tags)
    html_tree = lxml_html.fromstring(html_source)

    # Find and replace SVG with XML-parsed version
    svg_elem = html_tree.find('.//svg')

    # Parse correct SVG as XML
    correct_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect x="10" y="10" width="30" height="30" fill="blue"/>
    <textPath href="#path">Correct case</textPath>
</svg>'''
    xml_svg = etree.fromstring(correct_svg.encode())

    # Replace in tree
    svg_parent = svg_elem.getparent()
    svg_index = list(svg_parent).index(svg_elem)
    svg_parent.remove(svg_elem)
    svg_parent.insert(svg_index, xml_svg)

    print("Strategy 1: Serialize entire document as HTML")
    html_method_output = lxml_html.tostring(html_tree, encoding='unicode', pretty_print=True)
    print(html_method_output)
    print()

    print("Strategy 2: Serialize entire document as XML")
    # Need to use etree for XML serialization
    xml_method_output = etree.tostring(html_tree, method='xml', encoding='unicode', pretty_print=True)
    print(xml_method_output)
    print()


def test_self_closing_variations():
    """Test different self-closing tag scenarios."""
    print("=== Test 3: Self-Closing Tag Variations ===\n")

    test_cases = [
        ("Empty rect with self-closing", '<rect x="10" y="10"/>'),
        ("Empty rect with explicit close", '<rect x="10" y="10"></rect>'),
        ("Rect with attributes", '<rect x="10" y="10" width="30" height="30"/>'),
    ]

    for name, svg_content in test_cases:
        svg_wrapped = f'<svg xmlns="http://www.w3.org/2000/svg">{svg_content}</svg>'
        tree = etree.fromstring(svg_wrapped.encode())

        xml_out = etree.tostring(tree, method='xml', encoding='unicode')
        html_out = etree.tostring(tree, method='html', encoding='unicode')

        print(f"{name}:")
        print(f"  XML:  {xml_out}")
        print(f"  HTML: {html_out}")
        print()


def test_html_serialization_options():
    """Check what options lxml provides for HTML serialization."""
    print("=== Test 4: HTML Serialization Options ===\n")

    svg_source = '''<svg xmlns="http://www.w3.org/2000/svg">
    <rect x="10" y="10" width="30" height="30"/>
    <textPath href="#p">Text</textPath>
</svg>'''

    tree = etree.fromstring(svg_source.encode())

    # Try different HTML serialization options
    print("Default HTML method:")
    print(etree.tostring(tree, method='html', encoding='unicode'))
    print()

    # Check if there's an option for self-closing in HTML mode
    # (Spoiler: there isn't - HTML method uses HTML rules)


def test_manual_hybrid_serialization():
    """Test manually controlling serialization per subtree."""
    print("=== Test 5: Manual Hybrid Serialization ===\n")

    html_source = """<!DOCTYPE html>
<html>
<body>
    <p>Before SVG</p>
    <div id="svg-container"></div>
    <p>After SVG</p>
</body>
</html>"""

    svg_xml_source = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect x="10" y="10" width="30" height="30" fill="blue"/>
    <textPath href="#path">Correct case</textPath>
</svg>'''

    # Parse both
    html_tree = lxml_html.fromstring(html_source)
    svg_tree = etree.fromstring(svg_xml_source.encode())

    # Insert XML-parsed SVG
    container = html_tree.get_element_by_id('svg-container')
    container.append(svg_tree)

    # Now serialize the whole thing
    print("Approach: Serialize HTML tree with embedded XML-parsed SVG")
    print()

    # HTML serialization
    print("Using method='html':")
    result = lxml_html.tostring(html_tree, encoding='unicode', pretty_print=True)
    print(result)
    print()

    # Check what actually happened to the SVG
    svg_in_output = html_tree.get_element_by_id('svg-container')[0]
    print(f"SVG tag name in tree: {svg_in_output.tag}")
    textpath = svg_in_output.find('.//{http://www.w3.org/2000/svg}textPath')
    if textpath is not None:
        print(f"textPath found: {textpath.tag}")
    else:
        textpath_lower = svg_in_output.find('.//{http://www.w3.org/2000/svg}textpath')
        if textpath_lower is not None:
            print(f"textpath (lowercase) found: {textpath_lower.tag}")
        else:
            print("No textPath element found!")


if __name__ == "__main__":
    test_xml_serialization_in_html()
    test_embedding_in_full_document()
    test_self_closing_variations()
    test_html_serialization_options()
    test_manual_hybrid_serialization()

    print("\n" + "="*60)
    print("CONCLUSIONS")
    print("="*60)
    print("""
Key findings:
1. When XML-parsed elements are in the tree, serializing with method='html'
   will LOWERCASE the tags and NOT use self-closing syntax
2. When serializing with method='xml', self-closing tags ARE used and case
   is preserved
3. Per the HTML5 spec, SVG in HTML CAN use self-closing tags because
   they're in "foreign content" mode
4. Browsers accept both styles: <rect/> and <rect></rect> in SVG

Recommendation:
- For SVG subtrees in HTML5 documents, we should serialize them with
  method='xml' to preserve case and allow self-closing tags
- This is spec-compliant and browser-compatible
- We need to manually control serialization on a per-subtree basis
""")
