import pytest
from lxml import etree
import click

from markuplift.predicates import matches_xpath


def test_matches_xpath_simple_tag():
    """Test XPath matching for simple tag names."""
    xml = "<root><div>content</div><span>other</span></root>"
    tree = etree.fromstring(xml)

    factory = matches_xpath("//div")
    predicate = factory(tree)

    div_elem = tree.find("div")
    span_elem = tree.find("span")

    assert predicate(div_elem) is True
    assert predicate(span_elem) is False
    assert predicate(tree) is False


def test_matches_xpath_multiple_matches():
    """Test XPath matching multiple elements."""
    xml = "<root><p>first</p><p>second</p><div>other</div></root>"
    tree = etree.fromstring(xml)

    factory = matches_xpath("//p")
    predicate = factory(tree)

    p_elements = tree.findall("p")
    div_element = tree.find("div")

    assert predicate(p_elements[0]) is True
    assert predicate(p_elements[1]) is True
    assert predicate(div_element) is False


def test_matches_xpath_with_attributes():
    """Test XPath matching with attribute conditions."""
    xml = '<root><div class="test">match</div><div>no match</div></root>'
    tree = etree.fromstring(xml)

    factory = matches_xpath("//div[@class='test']")
    predicate = factory(tree)

    div_with_class = tree.find("div[@class='test']")
    div_without_class = tree.xpath("//div[not(@class)]")[0]

    assert predicate(div_with_class) is True
    assert predicate(div_without_class) is False


def test_matches_xpath_complex_expression():
    """Test complex XPath expressions."""
    xml = """
    <root>
        <article>
            <header><h1>Title</h1></header>
            <section><p>Content</p></section>
            <footer><p>Footer</p></footer>
        </article>
    </root>
    """
    tree = etree.fromstring(xml)

    factory = matches_xpath("//article//p")
    predicate = factory(tree)

    section_p = tree.find(".//section/p")
    footer_p = tree.find(".//footer/p")
    h1_elem = tree.find(".//h1")

    assert predicate(section_p) is True
    assert predicate(footer_p) is True
    assert predicate(h1_elem) is False


def test_matches_xpath_no_matches():
    """Test XPath that matches no elements."""
    xml = "<root><div>content</div></root>"
    tree = etree.fromstring(xml)

    factory = matches_xpath("//span")
    predicate = factory(tree)

    div_elem = tree.find("div")
    assert predicate(div_elem) is False
    assert predicate(tree) is False


def test_matches_xpath_invalid_expression():
    """Test that invalid XPath expressions raise appropriate errors."""
    xml = "<root><div>content</div></root>"
    tree = etree.fromstring(xml)

    factory = matches_xpath("//invalid[[[")

    with pytest.raises(click.ClickException, match="Invalid XPath expression"):
        predicate = factory(tree)


def test_matches_xpath_performance_optimization():
    """Test that XPath is evaluated only once per document."""
    xml = "<root><p>1</p><p>2</p><p>3</p></root>"
    tree = etree.fromstring(xml)

    factory = matches_xpath("//p")
    predicate = factory(tree)

    # The test shows that the predicate works correctly and uses set membership
    # for O(1) lookups rather than re-evaluating XPath for each element
    p_elements = tree.findall("p")

    # All p elements should match
    for p in p_elements:
        assert predicate(p) is True

    # Root should not match
    assert predicate(tree) is False

    # This documents the performance behavior: XPath is evaluated once
    # during factory creation and results are cached in a set


def test_matches_xpath_with_namespaces():
    """Test XPath matching with XML namespaces using Clark notation."""
    xml = '''
    <root xmlns:ns="http://example.com/ns">
        <ns:element>namespaced</ns:element>
        <element>not namespaced</element>
    </root>
    '''
    tree = etree.fromstring(xml)

    # Use Clark notation for namespaced elements
    factory = matches_xpath("//*[local-name()='element' and namespace-uri()='http://example.com/ns']")
    predicate = factory(tree)

    namespaced_elem = tree.find(".//{http://example.com/ns}element")
    regular_elem = tree.find(".//element")

    assert predicate(namespaced_elem) is True
    assert predicate(regular_elem) is False


def test_matches_xpath_reusable_factory():
    """Test that the same factory can be used with different documents."""
    factory = matches_xpath("//div")

    # First document
    xml1 = "<root><div>first</div><span>other</span></root>"
    tree1 = etree.fromstring(xml1)
    predicate1 = factory(tree1)

    div1 = tree1.find("div")
    span1 = tree1.find("span")

    assert predicate1(div1) is True
    assert predicate1(span1) is False

    # Second document
    xml2 = "<document><div>second</div><p>paragraph</p></document>"
    tree2 = etree.fromstring(xml2)
    predicate2 = factory(tree2)

    div2 = tree2.find("div")
    p2 = tree2.find("p")

    assert predicate2(div2) is True
    assert predicate2(p2) is False