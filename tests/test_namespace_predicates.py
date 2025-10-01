"""Tests for namespace-aware predicates.

These tests verify that tag-matching predicates work correctly with:
- Clark notation for namespaced elements
- QName objects for readable namespace handling
- Mixed usage of both in the same predicate
"""

import pytest
from lxml import etree
from markuplift.predicates import tag_equals, tag_in, tag_name


class TestTagEqualsWithNamespaces:
    """Test tag_equals predicate with namespaces."""

    @pytest.fixture
    def svg_doc(self):
        """SVG document with namespaces."""
        doc = '''<svg xmlns="http://www.w3.org/2000/svg" xmlns:bx="https://boxy-svg.com">
          <rect width="100"/>
          <bx:grid x="0" y="0"/>
          <circle r="50"/>
        </svg>'''
        return etree.fromstring(doc.encode())

    def test_clark_notation_string(self, svg_doc):
        """Match element using Clark notation string."""
        rect = svg_doc[0]
        grid = svg_doc[1]

        predicate_factory = tag_equals("{http://www.w3.org/2000/svg}rect")
        predicate = predicate_factory(svg_doc)

        assert predicate(rect) is True
        assert predicate(grid) is False

    def test_qname_object(self, svg_doc):
        """Match element using QName object."""
        rect = svg_doc[0]
        grid = svg_doc[1]

        qname = etree.QName("http://www.w3.org/2000/svg", "rect")
        predicate_factory = tag_equals(qname)
        predicate = predicate_factory(svg_doc)

        assert predicate(rect) is True
        assert predicate(grid) is False

    def test_qname_from_element(self, svg_doc):
        """Create QName from element and use it in predicate."""
        rect = svg_doc[0]

        qname = etree.QName(rect)
        predicate_factory = tag_equals(qname)
        predicate = predicate_factory(svg_doc)

        assert predicate(rect) is True

    def test_prefixed_namespace_clark(self, svg_doc):
        """Match prefixed namespace element with Clark notation."""
        grid = svg_doc[1]

        predicate_factory = tag_equals("{https://boxy-svg.com}grid")
        predicate = predicate_factory(svg_doc)

        assert predicate(grid) is True

    def test_prefixed_namespace_qname(self, svg_doc):
        """Match prefixed namespace element with QName."""
        grid = svg_doc[1]

        qname = etree.QName("https://boxy-svg.com", "grid")
        predicate_factory = tag_equals(qname)
        predicate = predicate_factory(svg_doc)

        assert predicate(grid) is True

    def test_no_namespace_element(self):
        """Match element without namespace."""
        doc = '<root><child/></root>'
        root = etree.fromstring(doc.encode())
        child = root[0]

        predicate_factory = tag_equals("child")
        predicate = predicate_factory(root)

        assert predicate(child) is True


class TestTagInWithNamespaces:
    """Test tag_in predicate with namespaces."""

    @pytest.fixture
    def svg_doc(self):
        """SVG document with multiple element types."""
        doc = '''<svg xmlns="http://www.w3.org/2000/svg" xmlns:bx="https://boxy-svg.com">
          <rect width="100"/>
          <bx:grid x="0"/>
          <circle r="50"/>
          <line x1="0" y1="0" x2="100" y2="100"/>
        </svg>'''
        return etree.fromstring(doc.encode())

    def test_clark_notation_strings(self, svg_doc):
        """Match multiple elements using Clark notation."""
        rect = svg_doc[0]
        grid = svg_doc[1]
        circle = svg_doc[2]
        line = svg_doc[3]

        predicate_factory = tag_in(
            "{http://www.w3.org/2000/svg}rect",
            "{http://www.w3.org/2000/svg}circle"
        )
        predicate = predicate_factory(svg_doc)

        assert predicate(rect) is True
        assert predicate(grid) is False
        assert predicate(circle) is True
        assert predicate(line) is False

    def test_qname_objects(self, svg_doc):
        """Match multiple elements using QName objects."""
        rect = svg_doc[0]
        circle = svg_doc[2]

        SVG_NS = "http://www.w3.org/2000/svg"
        predicate_factory = tag_in(
            etree.QName(SVG_NS, "rect"),
            etree.QName(SVG_NS, "circle")
        )
        predicate = predicate_factory(svg_doc)

        assert predicate(rect) is True
        assert predicate(circle) is True

    def test_mixed_clark_and_qname(self, svg_doc):
        """Match elements using mixed Clark notation and QName."""
        rect = svg_doc[0]
        grid = svg_doc[1]
        circle = svg_doc[2]

        predicate_factory = tag_in(
            "{http://www.w3.org/2000/svg}rect",
            etree.QName("https://boxy-svg.com", "grid")
        )
        predicate = predicate_factory(svg_doc)

        assert predicate(rect) is True
        assert predicate(grid) is True
        assert predicate(circle) is False

    def test_mixed_namespaced_and_plain(self):
        """Match both namespaced and non-namespaced elements."""
        doc = '''<root>
          <child/>
          <svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>
        </root>'''
        root = etree.fromstring(doc.encode())
        child = root[0]
        rect = root[1][0]

        predicate_factory = tag_in(
            "child",
            "{http://www.w3.org/2000/svg}rect"
        )
        predicate = predicate_factory(root)

        assert predicate(child) is True
        assert predicate(rect) is True


class TestTagNameAlias:
    """Test tag_name alias for tag_equals."""

    def test_tag_name_with_clark_notation(self):
        """tag_name works with Clark notation."""
        doc = '<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
        root = etree.fromstring(doc.encode())
        rect = root[0]

        predicate_factory = tag_name("{http://www.w3.org/2000/svg}rect")
        predicate = predicate_factory(root)

        assert predicate(rect) is True

    def test_tag_name_with_qname(self):
        """tag_name works with QName objects."""
        doc = '<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
        root = etree.fromstring(doc.encode())
        rect = root[0]

        qname = etree.QName("http://www.w3.org/2000/svg", "rect")
        predicate_factory = tag_name(qname)
        predicate = predicate_factory(root)

        assert predicate(rect) is True


class TestPredicateChaining:
    """Test that namespace predicates work with attribute chaining."""

    def test_clark_notation_with_attribute(self):
        """Match namespaced element with specific attribute."""
        doc = '''<svg xmlns="http://www.w3.org/2000/svg">
          <rect width="100"/>
          <circle width="100"/>
        </svg>'''
        root = etree.fromstring(doc.encode())
        rect = root[0]
        circle = root[1]

        factory = tag_equals("{http://www.w3.org/2000/svg}rect").with_attribute("width")
        predicate = factory(root)

        # Note: This tests AttributePredicate, not ElementPredicate
        # AttributePredicate signature: predicate(element, attr_name, attr_value)
        # Must match BOTH element tag AND attribute
        assert predicate(rect, "width", "100") is True
        assert predicate(circle, "width", "100") is False  # wrong tag (circle not rect)

    def test_qname_with_attribute(self):
        """QName predicates support attribute chaining."""
        doc = '''<svg xmlns="http://www.w3.org/2000/svg">
          <rect width="100"/>
        </svg>'''
        root = etree.fromstring(doc.encode())
        rect = root[0]

        qname = etree.QName("http://www.w3.org/2000/svg", "rect")
        factory = tag_name(qname).with_attribute("width")
        predicate = factory(root)

        assert predicate(rect, "width", "100") is True


class TestAttributePredicatesWithNamespaces:
    """Test attribute predicates with namespaced attributes."""

    @pytest.fixture
    def svg_doc(self):
        """SVG document with namespaced attributes."""
        doc = '''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
          <use xlink:href="#shape1"/>
          <use xlink:href="#shape2"/>
          <image xlink:href="photo.jpg"/>
        </svg>'''
        return etree.fromstring(doc.encode())

    def test_has_attribute_with_clark_notation(self, svg_doc):
        """has_attribute works with Clark notation for namespaced attributes."""
        from markuplift.predicates import has_attribute

        factory = has_attribute("{http://www.w3.org/1999/xlink}href")
        predicate = factory(svg_doc)

        use1 = svg_doc[0]
        use2 = svg_doc[1]
        image = svg_doc[2]

        assert predicate(use1) is True
        assert predicate(use2) is True
        assert predicate(image) is True

    def test_has_attribute_with_qname(self, svg_doc):
        """has_attribute works with QName objects."""
        from markuplift.predicates import has_attribute

        qname = etree.QName("http://www.w3.org/1999/xlink", "href")
        factory = has_attribute(qname)
        predicate = factory(svg_doc)

        use1 = svg_doc[0]
        use2 = svg_doc[1]
        image = svg_doc[2]

        assert predicate(use1) is True
        assert predicate(use2) is True
        assert predicate(image) is True

    def test_attribute_equals_with_clark_notation(self, svg_doc):
        """attribute_equals works with Clark notation for namespaced attributes."""
        from markuplift.predicates import attribute_equals

        factory = attribute_equals("{http://www.w3.org/1999/xlink}href", "#shape1")
        predicate = factory(svg_doc)

        use1 = svg_doc[0]
        use2 = svg_doc[1]
        image = svg_doc[2]

        assert predicate(use1) is True
        assert predicate(use2) is False
        assert predicate(image) is False

    def test_attribute_equals_with_qname(self, svg_doc):
        """attribute_equals works with QName objects."""
        from markuplift.predicates import attribute_equals

        qname = etree.QName("http://www.w3.org/1999/xlink", "href")
        factory = attribute_equals(qname, "#shape1")
        predicate = factory(svg_doc)

        use1 = svg_doc[0]
        use2 = svg_doc[1]
        image = svg_doc[2]

        assert predicate(use1) is True
        assert predicate(use2) is False
        assert predicate(image) is False

    def test_with_attribute_qname_chaining(self, svg_doc):
        """Chaining with QName in .with_attribute() works correctly."""
        from markuplift.predicates import tag_equals

        # Match SVG use elements that have xlink:href attribute
        SVG_NS = "http://www.w3.org/2000/svg"
        XLINK_NS = "http://www.w3.org/1999/xlink"

        qname = etree.QName(XLINK_NS, "href")
        factory = tag_equals(etree.QName(SVG_NS, "use")).with_attribute(qname)
        predicate = factory(svg_doc)

        use1 = svg_doc[0]
        use2 = svg_doc[1]
        image = svg_doc[2]

        # Both use elements should match (they have the tag AND the attribute)
        for attr_name, attr_value in use1.attrib.items():
            result = predicate(use1, attr_name, attr_value)
            if attr_name == "{http://www.w3.org/1999/xlink}href":
                assert result is True

        # Image has the attribute but wrong tag
        for attr_name, attr_value in image.attrib.items():
            result = predicate(image, attr_name, attr_value)
            assert result is False

    def test_with_attribute_qname_value_matching(self, svg_doc):
        """Chaining with QName name and specific value works correctly."""
        from markuplift.predicates import tag_in

        # Match use OR image elements that have xlink:href="#shape1"
        SVG_NS = "http://www.w3.org/2000/svg"
        XLINK_NS = "http://www.w3.org/1999/xlink"

        qname = etree.QName(XLINK_NS, "href")
        factory = tag_in(
            etree.QName(SVG_NS, "use"),
            etree.QName(SVG_NS, "image")
        ).with_attribute(qname, "#shape1")
        predicate = factory(svg_doc)

        use1 = svg_doc[0]
        use2 = svg_doc[1]
        image = svg_doc[2]

        # use1 has xlink:href="#shape1" - should match
        for attr_name, attr_value in use1.attrib.items():
            result = predicate(use1, attr_name, attr_value)
            if attr_name == "{http://www.w3.org/1999/xlink}href":
                assert result is True

        # use2 has xlink:href="#shape2" - should not match
        for attr_name, attr_value in use2.attrib.items():
            result = predicate(use2, attr_name, attr_value)
            assert result is False

        # image has xlink:href="photo.jpg" - should not match
        for attr_name, attr_value in image.attrib.items():
            result = predicate(image, attr_name, attr_value)
            assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
