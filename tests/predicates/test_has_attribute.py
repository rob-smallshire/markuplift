import pytest
from lxml import etree

from markuplift.predicates import has_attribute, PredicateError


def test_has_attribute_simple_match():
    """Test has_attribute with simple attribute presence."""
    xml = '<root><div class="test">content</div><span>other</span></root>'
    tree = etree.fromstring(xml)

    factory = has_attribute("class")
    predicate = factory(tree)

    div_elem = tree.find("div")
    span_elem = tree.find("span")
    root_elem = tree

    assert predicate(div_elem) is True
    assert predicate(span_elem) is False
    assert predicate(root_elem) is False


def test_has_attribute_multiple_attributes():
    """Test has_attribute when elements have multiple attributes."""
    xml = '<root><div class="test" id="main" data-value="123">content</div><span title="tooltip">other</span></root>'
    tree = etree.fromstring(xml)

    class_factory = has_attribute("class")
    id_factory = has_attribute("id")
    title_factory = has_attribute("title")

    class_predicate = class_factory(tree)
    id_predicate = id_factory(tree)
    title_predicate = title_factory(tree)

    div_elem = tree.find("div")
    span_elem = tree.find("span")

    assert class_predicate(div_elem) is True
    assert class_predicate(span_elem) is False

    assert id_predicate(div_elem) is True
    assert id_predicate(span_elem) is False

    assert title_predicate(div_elem) is False
    assert title_predicate(span_elem) is True


def test_has_attribute_no_matches():
    """Test has_attribute when no elements have the attribute."""
    xml = "<root><div>content</div><span>other</span></root>"
    tree = etree.fromstring(xml)

    factory = has_attribute("class")
    predicate = factory(tree)

    div_elem = tree.find("div")
    span_elem = tree.find("span")
    root_elem = tree

    assert predicate(div_elem) is False
    assert predicate(span_elem) is False
    assert predicate(root_elem) is False


def test_has_attribute_empty_value():
    """Test has_attribute with empty attribute values."""
    xml = '<root><div class="">content</div><span class="test">other</span></root>'
    tree = etree.fromstring(xml)

    factory = has_attribute("class")
    predicate = factory(tree)

    div_elem = tree.find("div")
    span_elem = tree.find("span")

    # Both elements have the class attribute, regardless of value
    assert predicate(div_elem) is True
    assert predicate(span_elem) is True


def test_has_attribute_case_sensitive():
    """Test that attribute names are case-sensitive."""
    xml = '<root><div Class="test">content</div><span class="test">other</span></root>'
    tree = etree.fromstring(xml)

    lowercase_factory = has_attribute("class")
    uppercase_factory = has_attribute("Class")

    lowercase_predicate = lowercase_factory(tree)
    uppercase_predicate = uppercase_factory(tree)

    div_elem = tree.find("div")
    span_elem = tree.find("span")

    assert lowercase_predicate(div_elem) is False  # No lowercase "class"
    assert lowercase_predicate(span_elem) is True

    assert uppercase_predicate(div_elem) is True
    assert uppercase_predicate(span_elem) is False  # No uppercase "Class"


def test_has_attribute_with_namespaces():
    """Test has_attribute with namespaced attributes."""
    xml = '''
    <root xmlns:ns="http://example.com/ns">
        <div ns:custom="value">namespaced attribute</div>
        <span custom="value">regular attribute</span>
    </root>
    '''
    tree = etree.fromstring(xml)

    # Test both Clark notation and regular attribute names
    ns_factory = has_attribute("{http://example.com/ns}custom")
    regular_factory = has_attribute("custom")

    ns_predicate = ns_factory(tree)
    regular_predicate = regular_factory(tree)

    div_elem = tree.find("div")
    span_elem = tree.find("span")

    assert ns_predicate(div_elem) is True
    assert ns_predicate(span_elem) is False

    assert regular_predicate(div_elem) is False
    assert regular_predicate(span_elem) is True


def test_has_attribute_special_characters():
    """Test has_attribute with special characters in attribute names."""
    xml = '<root><div data-test="value" under_score="value3">content</div></root>'
    tree = etree.fromstring(xml)

    dash_factory = has_attribute("data-test")
    underscore_factory = has_attribute("under_score")

    dash_predicate = dash_factory(tree)
    underscore_predicate = underscore_factory(tree)

    div_elem = tree.find("div")

    assert dash_predicate(div_elem) is True
    assert underscore_predicate(div_elem) is True


def test_has_attribute_empty_attribute_name():
    """Test has_attribute with empty attribute name."""
    # Empty attribute name should raise PredicateError
    with pytest.raises(PredicateError, match="Attribute name cannot be empty"):
        has_attribute("")


def test_has_attribute_reusable_factory():
    """Test that the same factory works with different documents."""
    factory = has_attribute("class")

    # First document
    xml1 = '<root><div class="test">first</div><span>other</span></root>'
    tree1 = etree.fromstring(xml1)
    predicate1 = factory(tree1)

    div1 = tree1.find("div")
    span1 = tree1.find("span")

    assert predicate1(div1) is True
    assert predicate1(span1) is False

    # Second document with different structure
    xml2 = '<document><p class="paragraph">second</p><article>article</article></document>'
    tree2 = etree.fromstring(xml2)
    predicate2 = factory(tree2)

    p2 = tree2.find("p")
    article2 = tree2.find("article")

    assert predicate2(p2) is True
    assert predicate2(article2) is False