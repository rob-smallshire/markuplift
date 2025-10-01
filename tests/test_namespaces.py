"""Tests for XML namespace handling.

These tests verify that MarkupLift correctly handles XML namespaces, including:
- Preserving namespace prefixes from parsed documents
- Formatting namespace declarations (xmlns attributes)
- Converting between Clark notation and prefix:localname
- Handling default namespaces, prefixed namespaces, and the xml namespace
- Supporting fragments (subtrees) with namespaces
"""

import pytest
from lxml import etree
from markuplift import XmlFormatter
from markuplift.namespace import (
    qname_to_str,
    get_new_namespace_declarations,
    format_tag_name,
    format_attribute_name,
    format_xmlns_declarations,
)


class TestQNameConversion:
    """Test qname_to_str utility function."""

    def test_qname_to_string(self):
        """QName objects are converted to Clark notation."""
        qname = etree.QName("http://www.w3.org/2000/svg", "rect")
        assert qname_to_str(qname) == "{http://www.w3.org/2000/svg}rect"

    def test_string_passthrough(self):
        """String inputs are returned unchanged."""
        assert qname_to_str("div") == "div"
        assert qname_to_str("{http://example.com}tag") == "{http://example.com}tag"

    def test_qname_from_element(self):
        """QName created from element tag."""
        doc = '<svg xmlns="http://www.w3.org/2000/svg"/>'
        elem = etree.fromstring(doc.encode())
        qname = etree.QName(elem)
        assert qname_to_str(qname) == "{http://www.w3.org/2000/svg}svg"


class TestNamespaceDeclarations:
    """Test get_new_namespace_declarations function."""

    def test_root_element_all_namespaces_new(self):
        """Root element - all namespaces are new."""
        doc = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"/>'
        root = etree.fromstring(doc.encode())

        decls = get_new_namespace_declarations(root)

        assert decls == {
            None: "http://www.w3.org/2000/svg",
            "xlink": "http://www.w3.org/1999/xlink"
        }

    def test_child_inherits_no_new_declarations(self):
        """Child with same nsmap as parent - no new declarations."""
        doc = '<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
        root = etree.fromstring(doc.encode())
        child = root[0]

        decls = get_new_namespace_declarations(child)

        assert decls == {}

    def test_child_introduces_namespace(self):
        """Child introduces new namespace."""
        doc = '''<root>
          <svg xmlns="http://www.w3.org/2000/svg">
            <rect/>
          </svg>
        </root>'''
        root = etree.fromstring(doc.encode())
        svg = root[0]

        decls = get_new_namespace_declarations(svg)

        assert decls == {None: "http://www.w3.org/2000/svg"}

    def test_changing_default_namespace(self):
        """Changing default namespace."""
        doc = '''<html xmlns="http://www.w3.org/1999/xhtml">
          <body>
            <svg xmlns="http://www.w3.org/2000/svg"/>
          </body>
        </html>'''
        root = etree.fromstring(doc.encode())
        svg = root[0][0]

        decls = get_new_namespace_declarations(svg)

        assert decls == {None: "http://www.w3.org/2000/svg"}


class TestTagNameFormatting:
    """Test format_tag_name function."""

    def test_default_namespace(self):
        """Element in default namespace - no prefix."""
        doc = '<svg xmlns="http://www.w3.org/2000/svg"/>'
        elem = etree.fromstring(doc.encode())

        assert format_tag_name(elem) == "svg"

    def test_prefixed_namespace(self):
        """Element with namespace prefix."""
        doc = '<svg xmlns:bx="https://boxy-svg.com"><bx:grid/></svg>'
        root = etree.fromstring(doc.encode())
        grid = root[0]

        assert format_tag_name(grid) == "bx:grid"

    def test_no_namespace(self):
        """Element without namespace."""
        doc = '<root><child/></root>'
        root = etree.fromstring(doc.encode())
        child = root[0]

        assert format_tag_name(child) == "child"

    def test_xml_namespace(self):
        """Element using xml namespace (rare, but possible)."""
        # Note: xml namespace is typically used for attributes, not elements
        # But the function should handle it
        doc = '<root/>'
        elem = etree.fromstring(doc.encode())
        # Manually set tag to xml namespace for testing
        elem.tag = "{http://www.w3.org/XML/1998/namespace}test"

        assert format_tag_name(elem) == "xml:test"


class TestAttributeNameFormatting:
    """Test format_attribute_name function."""

    def test_no_namespace(self):
        """Regular attribute without namespace."""
        doc = '<rect width="100"/>'
        elem = etree.fromstring(doc.encode())

        assert format_attribute_name(elem, "width") == "width"

    def test_prefixed_namespace(self):
        """Attribute with namespace prefix."""
        doc = '<svg xmlns:xlink="http://www.w3.org/1999/xlink"><use xlink:href="#shape"/></svg>'
        root = etree.fromstring(doc.encode())
        use_elem = root[0]
        attr_name = list(use_elem.attrib.keys())[0]

        assert format_attribute_name(use_elem, attr_name) == "xlink:href"

    def test_xml_namespace(self):
        """Attribute using xml namespace."""
        doc = '<text xml:space="preserve"/>'
        elem = etree.fromstring(doc.encode())
        attr_name = list(elem.attrib.keys())[0]

        assert format_attribute_name(elem, attr_name) == "xml:space"


class TestXmlnsFormatting:
    """Test format_xmlns_declarations function."""

    def test_default_namespace_only(self):
        """Format default namespace declaration."""
        decls = {None: "http://www.w3.org/2000/svg"}

        result = format_xmlns_declarations(decls)

        assert result == ['xmlns="http://www.w3.org/2000/svg"']

    def test_prefixed_namespace_only(self):
        """Format prefixed namespace declaration."""
        decls = {"xlink": "http://www.w3.org/1999/xlink"}

        result = format_xmlns_declarations(decls)

        assert result == ['xmlns:xlink="http://www.w3.org/1999/xlink"']

    def test_mixed_declarations(self):
        """Format mixed default and prefixed namespaces."""
        decls = {
            None: "http://www.w3.org/2000/svg",
            "bx": "https://boxy-svg.com",
            "xlink": "http://www.w3.org/1999/xlink"
        }

        result = format_xmlns_declarations(decls)

        # Default namespace should be first
        assert result[0] == 'xmlns="http://www.w3.org/2000/svg"'
        # Others should be alphabetically sorted
        assert 'xmlns:bx="https://boxy-svg.com"' in result
        assert 'xmlns:xlink="http://www.w3.org/1999/xlink"' in result

    def test_empty_namespace(self):
        """Format empty namespace (removes default namespace)."""
        decls = {None: ""}

        result = format_xmlns_declarations(decls)

        assert result == ['xmlns=""']


class TestFormatterIntegration:
    """Test namespace handling in formatter."""

    def test_simple_svg(self):
        """Format simple SVG with default namespace."""
        doc = '<svg xmlns="http://www.w3.org/2000/svg"><rect width="100"/></svg>'

        formatter = XmlFormatter()
        result = formatter.format_str(doc)

        assert 'xmlns="http://www.w3.org/2000/svg"' in result
        assert '<svg' in result
        assert '<rect' in result
        assert '{http://www.w3.org/2000/svg}' not in result  # No Clark notation

    def test_multiple_namespaces(self):
        """Format document with multiple namespaces."""
        doc = '''<svg xmlns="http://www.w3.org/2000/svg"
                      xmlns:xlink="http://www.w3.org/1999/xlink"
                      xmlns:bx="https://boxy-svg.com">
          <bx:grid x="0"/>
          <use xlink:href="#shape"/>
        </svg>'''

        formatter = XmlFormatter()
        result = formatter.format_str(doc)

        assert 'xmlns="http://www.w3.org/2000/svg"' in result
        assert 'xmlns:xlink=' in result
        assert 'xmlns:bx=' in result
        assert '<bx:grid' in result
        assert 'xlink:href' in result

    def test_namespace_introduced_on_child(self):
        """Format document where namespace is introduced on child element."""
        doc = '''<root>
          <svg xmlns="http://www.w3.org/2000/svg">
            <rect width="100"/>
          </svg>
        </root>'''

        formatter = XmlFormatter()
        result = formatter.format_str(doc)

        # xmlns should only appear on <svg>, not on <root>
        assert result.count('xmlns=') == 1
        assert '<svg xmlns=' in result

    def test_changing_default_namespace(self):
        """Format document with changing default namespace."""
        doc = '''<html xmlns="http://www.w3.org/1999/xhtml">
          <body>
            <svg xmlns="http://www.w3.org/2000/svg">
              <rect width="100"/>
            </svg>
          </body>
        </html>'''

        formatter = XmlFormatter()
        result = formatter.format_str(doc)

        assert 'xmlns="http://www.w3.org/1999/xhtml"' in result
        assert 'xmlns="http://www.w3.org/2000/svg"' in result

    def test_xml_space_attribute(self):
        """Format document with xml:space attribute."""
        doc = '<text xmlns="http://www.w3.org/2000/svg" xml:space="preserve">  Keep   spaces  </text>'

        formatter = XmlFormatter()
        result = formatter.format_str(doc)

        assert 'xml:space="preserve"' in result
        # xml namespace should NOT be declared (it's implicit)
        assert 'xmlns:xml=' not in result

    def test_fragment_formatting(self):
        """Format a subtree (fragment) with namespaces."""
        # Convert fragment to string and format
        full_doc = '''<root>
          <svg xmlns="http://www.w3.org/2000/svg" xmlns:bx="https://boxy-svg.com">
            <bx:grid x="0"/>
          </svg>
        </root>'''

        root = etree.fromstring(full_doc.encode())
        svg_fragment = root[0]

        # Serialize fragment to string for formatting
        fragment_str = etree.tostring(svg_fragment, encoding='unicode')

        formatter = XmlFormatter()
        result = formatter.format_str(fragment_str)

        assert 'xmlns="http://www.w3.org/2000/svg"' in result
        assert 'xmlns:bx=' in result
        assert '<bx:grid' in result

    def test_round_trip_preservation(self):
        """Round-trip: parse → format → parse → format should be stable."""
        original = '''<svg xmlns="http://www.w3.org/2000/svg" xmlns:bx="https://boxy-svg.com">
  <bx:grid x="0" y="0"/>
</svg>'''

        formatter = XmlFormatter()

        # First format
        result1 = formatter.format_str(original)

        # Parse result and format again
        result2 = formatter.format_str(result1)

        # Should be identical
        assert result1 == result2

    def test_no_namespace_still_works(self):
        """Ensure non-namespaced XML still works correctly."""
        doc = '<root><child attribute="value">text</child></root>'

        formatter = XmlFormatter()
        result = formatter.format_str(doc)

        assert '<root>' in result
        assert '<child' in result
        assert 'xmlns' not in result  # No namespace declarations


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
