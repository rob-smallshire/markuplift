#!/usr/bin/env python3
"""
Verify that lxml's HTML serializer preserves case for foreign elements.

This tests whether we actually need XML serialization or if HTML serialization
preserves case for SVG elements.
"""

from lxml import etree, html as lxml_html


def test_case_preservation_in_html_serialization():
    """Does HTML serialization preserve SVG element case?"""
    print("=== Case Preservation Test ===\n")

    # Create an HTML document with XML-parsed SVG
    html_source = """<!DOCTYPE html>
<html>
<body>
    <div id="container"></div>
</body>
</html>"""

    svg_source = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100">
    <defs>
        <path id="curvePath" d="M 10,50 Q 50,10 100,50"/>
    </defs>
    <text>
        <textPath href="#curvePath">
            <tspan>Text on a curve</tspan>
        </textPath>
    </text>
    <linearGradient id="grad1">
        <stop offset="0%"/>
    </linearGradient>
    <radialGradient id="grad2">
        <stop offset="100%"/>
    </radialGradient>
</svg>'''

    # Parse both
    html_tree = lxml_html.fromstring(html_source)
    svg_tree = etree.fromstring(svg_source.encode())

    # Insert SVG
    container = html_tree.get_element_by_id('container')
    container.append(svg_tree)

    # Serialize with HTML method
    output = lxml_html.tostring(html_tree, encoding='unicode', pretty_print=True, doctype="<!DOCTYPE html>")

    print("HTML Serialization Output:")
    print(output)
    print()

    # Check what's actually in the output
    case_sensitive_elements = ['textPath', 'linearGradient', 'radialGradient']

    print("Case Preservation Check:")
    for elem_name in case_sensitive_elements:
        if f"<{elem_name}" in output:
            print(f"  ✓ {elem_name} - case PRESERVED")
        elif f"<{elem_name.lower()}" in output:
            print(f"  ✗ {elem_name} - case LOST (found {elem_name.lower()})")
        else:
            print(f"  ? {elem_name} - not found in output")
    print()


def test_namespace_aware_serialization():
    """Test how namespaced elements are serialized."""
    print("=== Namespace-Aware Serialization ===\n")

    svg_with_namespace = '''<svg xmlns="http://www.w3.org/2000/svg">
    <textPath>Case test</textPath>
</svg>'''

    tree = etree.fromstring(svg_with_namespace.encode())

    print(f"Element tag in tree: {tree[0].tag}")
    print(f"Expected: {{http://www.w3.org/2000/svg}}textPath")
    print()

    # Serialize with HTML
    html_out = etree.tostring(tree, method='html', encoding='unicode')
    print(f"HTML serialization: {html_out}")
    print()

    # Serialize with XML
    xml_out = etree.tostring(tree, method='xml', encoding='unicode')
    print(f"XML serialization: {xml_out}")
    print()


if __name__ == "__main__":
    test_case_preservation_in_html_serialization()
    test_namespace_aware_serialization()

    print("="*60)
    print("CONCLUSION")
    print("="*60)
    print("""
If HTML serialization PRESERVES case for namespaced SVG elements,
then we don't need to use XML serialization for SVG subtrees!

We only need to:
1. Parse SVG subtrees as XML (to preserve case in the tree)
2. Serialize the whole document with HTML method (no self-closing tags)

This would be simpler and more HTML5-compliant (no self-closing non-void tags).
""")
