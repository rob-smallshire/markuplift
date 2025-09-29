import pytest
from lxml import etree

from markuplift.predicates import tag_in, PredicateError


def test_tag_in_simple_match():
    """Test tag_in with simple tag matching."""
    xml = "<root><div>content</div><span>other</span><p>paragraph</p></root>"
    tree = etree.fromstring(xml)

    factory = tag_in("div", "span")
    predicate = factory(tree)

    div_elem = tree.find("div")
    span_elem = tree.find("span")
    p_elem = tree.find("p")
    root_elem = tree

    assert predicate(div_elem) is True
    assert predicate(span_elem) is True
    assert predicate(p_elem) is False
    assert predicate(root_elem) is False


def test_tag_in_single_tag():
    """Test tag_in with only one tag (should behave like tag_equals)."""
    xml = "<root><div>content</div><span>other</span></root>"
    tree = etree.fromstring(xml)

    factory = tag_in("div")
    predicate = factory(tree)

    div_elem = tree.find("div")
    span_elem = tree.find("span")

    assert predicate(div_elem) is True
    assert predicate(span_elem) is False


def test_tag_in_no_matches():
    """Test tag_in when no elements match any of the tags."""
    xml = "<root><div>content</div><span>other</span></root>"
    tree = etree.fromstring(xml)

    factory = tag_in("p", "h1", "article")
    predicate = factory(tree)

    div_elem = tree.find("div")
    span_elem = tree.find("span")
    root_elem = tree

    assert predicate(div_elem) is False
    assert predicate(span_elem) is False
    assert predicate(root_elem) is False


def test_tag_in_many_tags():
    """Test tag_in with many different tags."""
    xml = """
    <root>
        <div>div content</div>
        <p>paragraph</p>
        <span>span content</span>
        <article>article content</article>
        <section>section content</section>
        <header>header content</header>
    </root>
    """
    tree = etree.fromstring(xml)

    factory = tag_in("div", "p", "span", "article", "section")
    predicate = factory(tree)

    div_elem = tree.find("div")
    p_elem = tree.find("p")
    span_elem = tree.find("span")
    article_elem = tree.find("article")
    section_elem = tree.find("section")
    header_elem = tree.find("header")

    assert predicate(div_elem) is True
    assert predicate(p_elem) is True
    assert predicate(span_elem) is True
    assert predicate(article_elem) is True
    assert predicate(section_elem) is True
    assert predicate(header_elem) is False


def test_tag_in_duplicate_tags():
    """Test tag_in with duplicate tag names (should still work correctly)."""
    xml = "<root><div>content</div><span>other</span></root>"
    tree = etree.fromstring(xml)

    factory = tag_in("div", "span", "div", "span")  # Duplicates
    predicate = factory(tree)

    div_elem = tree.find("div")
    span_elem = tree.find("span")

    assert predicate(div_elem) is True
    assert predicate(span_elem) is True


def test_tag_in_empty_tags():
    """Test tag_in with empty tags."""
    # Empty tag name should raise PredicateError
    with pytest.raises(PredicateError, match="Tag name cannot be empty"):
        tag_in("", "div")


def test_tag_in_case_sensitive():
    """Test that tag_in is case-sensitive."""
    xml = "<root><Div>content</Div><div>other</div><SPAN>span</SPAN></root>"
    tree = etree.fromstring(xml)

    factory = tag_in("div", "span")
    predicate = factory(tree)

    upper_div = tree.find("Div")
    lower_div = tree.find("div")
    upper_span = tree.find("SPAN")

    assert predicate(upper_div) is False
    assert predicate(lower_div) is True
    assert predicate(upper_span) is False


def test_tag_in_with_namespaces():
    """Test tag_in with namespaced elements."""
    xml = """
    <root xmlns:ns="http://example.com/ns">
        <ns:div>namespaced div</ns:div>
        <div>regular div</div>
        <ns:span>namespaced span</ns:span>
        <p>paragraph</p>
    </root>
    """
    tree = etree.fromstring(xml)

    # Test matching both regular and namespaced elements
    factory = tag_in("div", "{http://example.com/ns}span", "p")
    predicate = factory(tree)

    ns_div = tree.find(".//{http://example.com/ns}div")
    regular_div = tree.find(".//div")
    ns_span = tree.find(".//{http://example.com/ns}span")
    p_elem = tree.find(".//p")

    assert predicate(ns_div) is False  # ns:div doesn't match "div"
    assert predicate(regular_div) is True
    assert predicate(ns_span) is True
    assert predicate(p_elem) is True


def test_tag_in_no_args():
    """Test tag_in with no arguments (should raise error)."""
    # No arguments should raise PredicateError
    with pytest.raises(PredicateError, match="At least one tag name must be provided"):
        tag_in()


def test_tag_in_reusable_factory():
    """Test that the same factory works with different documents."""
    factory = tag_in("div", "span", "p")

    # First document
    xml1 = "<root><div>first</div><span>span content</span><h1>header</h1></root>"
    tree1 = etree.fromstring(xml1)
    predicate1 = factory(tree1)

    div1 = tree1.find("div")
    span1 = tree1.find("span")
    h1_1 = tree1.find("h1")

    assert predicate1(div1) is True
    assert predicate1(span1) is True
    assert predicate1(h1_1) is False

    # Second document with different structure
    xml2 = "<document><p>paragraph</p><article>article</article></document>"
    tree2 = etree.fromstring(xml2)
    predicate2 = factory(tree2)

    p2 = tree2.find("p")
    article2 = tree2.find("article")

    assert predicate2(p2) is True
    assert predicate2(article2) is False
