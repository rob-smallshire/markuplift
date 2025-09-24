from lxml import etree

from markuplift.predicates import tag_equals


def test_tag_equals_simple_match():
    """Test tag_equals with simple tag matching."""
    xml = "<root><div>content</div><span>other</span></root>"
    tree = etree.fromstring(xml)

    factory = tag_equals("div")
    predicate = factory(tree)

    div_elem = tree.find("div")
    span_elem = tree.find("span")
    root_elem = tree

    assert predicate(div_elem) is True
    assert predicate(span_elem) is False
    assert predicate(root_elem) is False


def test_tag_equals_no_matches():
    """Test tag_equals when no elements match."""
    xml = "<root><div>content</div><span>other</span></root>"
    tree = etree.fromstring(xml)

    factory = tag_equals("p")
    predicate = factory(tree)

    div_elem = tree.find("div")
    span_elem = tree.find("span")
    root_elem = tree

    assert predicate(div_elem) is False
    assert predicate(span_elem) is False
    assert predicate(root_elem) is False


def test_tag_equals_multiple_same_tags():
    """Test tag_equals with multiple elements of the same tag."""
    xml = "<root><p>first</p><p>second</p><div>other</div></root>"
    tree = etree.fromstring(xml)

    factory = tag_equals("p")
    predicate = factory(tree)

    p_elements = tree.findall("p")
    div_element = tree.find("div")

    assert predicate(p_elements[0]) is True
    assert predicate(p_elements[1]) is True
    assert predicate(div_element) is False


def test_tag_equals_case_sensitive():
    """Test that tag matching is case-sensitive."""
    xml = "<root><Div>content</Div><div>other</div></root>"
    tree = etree.fromstring(xml)

    factory = tag_equals("div")
    predicate = factory(tree)

    upper_div = tree.find("Div")
    lower_div = tree.find("div")

    assert predicate(upper_div) is False
    assert predicate(lower_div) is True


def test_tag_equals_with_namespaces():
    """Test tag_equals with namespaced elements."""
    xml = '''
    <root xmlns:ns="http://example.com/ns">
        <ns:element>namespaced</ns:element>
        <element>not namespaced</element>
    </root>
    '''
    tree = etree.fromstring(xml)

    # Test matching Clark notation
    factory = tag_equals("{http://example.com/ns}element")
    predicate = factory(tree)

    namespaced_elem = tree.find(".//{http://example.com/ns}element")
    regular_elem = tree.find(".//element")

    assert predicate(namespaced_elem) is True
    assert predicate(regular_elem) is False


def test_tag_equals_empty_tag():
    """Test tag_equals with empty string tag."""
    xml = "<root><div>content</div></root>"
    tree = etree.fromstring(xml)

    factory = tag_equals("")
    predicate = factory(tree)

    div_elem = tree.find("div")
    root_elem = tree

    assert predicate(div_elem) is False
    assert predicate(root_elem) is False


def test_tag_equals_reusable_factory():
    """Test that the same factory works with different documents."""
    factory = tag_equals("div")

    # First document
    xml1 = "<root><div>first</div><span>other</span></root>"
    tree1 = etree.fromstring(xml1)
    predicate1 = factory(tree1)

    div1 = tree1.find("div")
    span1 = tree1.find("span")

    assert predicate1(div1) is True
    assert predicate1(span1) is False

    # Second document with different structure
    xml2 = "<document><div>second</div><p>paragraph</p></document>"
    tree2 = etree.fromstring(xml2)
    predicate2 = factory(tree2)

    div2 = tree2.find("div")
    p2 = tree2.find("p")

    assert predicate2(div2) is True
    assert predicate2(p2) is False