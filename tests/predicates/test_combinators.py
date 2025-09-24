from lxml import etree

from markuplift.predicates import (
    tag_equals, tag_in, has_attribute, attribute_equals,
    any_of, all_of, not_matching
)


def test_any_of_simple_combination():
    """Test any_of combining simple predicates."""
    xml = '<root><div class="test">div content</div><span>span content</span><p>paragraph</p></root>'
    tree = etree.fromstring(xml)

    # Match div OR span elements
    factory = any_of(tag_equals("div"), tag_equals("span"))
    predicate = factory(tree)

    div_elem = tree.find("div")
    span_elem = tree.find("span")
    p_elem = tree.find("p")
    root_elem = tree

    assert predicate(div_elem) is True
    assert predicate(span_elem) is True
    assert predicate(p_elem) is False
    assert predicate(root_elem) is False


def test_any_of_with_attribute_predicates():
    """Test any_of combining attribute-based predicates."""
    xml = '''
    <root>
        <div class="test">has class</div>
        <div id="main">has id</div>
        <div class="other" id="secondary">has both</div>
        <div>has neither</div>
    </root>
    '''
    tree = etree.fromstring(xml)

    # Match elements with class OR id
    factory = any_of(has_attribute("class"), has_attribute("id"))
    predicate = factory(tree)

    divs = tree.findall("div")

    assert predicate(divs[0]) is True  # has class
    assert predicate(divs[1]) is True  # has id
    assert predicate(divs[2]) is True  # has both
    assert predicate(divs[3]) is False  # has neither


def test_any_of_no_predicates():
    """Test any_of with no predicate arguments."""
    xml = "<root><div>content</div></root>"
    tree = etree.fromstring(xml)

    factory = any_of()  # No predicates
    predicate = factory(tree)

    div_elem = tree.find("div")
    root_elem = tree

    # Should never match anything
    assert predicate(div_elem) is False
    assert predicate(root_elem) is False


def test_all_of_simple_combination():
    """Test all_of combining simple predicates."""
    xml = '''
    <root>
        <div class="test">div with class</div>
        <div>div without class</div>
        <span class="test">span with class</span>
    </root>
    '''
    tree = etree.fromstring(xml)

    # Match div elements that also have class attribute
    factory = all_of(tag_equals("div"), has_attribute("class"))
    predicate = factory(tree)

    div_with_class = tree.find("div[@class]")
    div_without_class = tree.xpath("//div[not(@class)]")[0]
    span_with_class = tree.find("span")

    assert predicate(div_with_class) is True
    assert predicate(div_without_class) is False
    assert predicate(span_with_class) is False


def test_all_of_attribute_predicates():
    """Test all_of combining multiple attribute predicates."""
    xml = '''
    <root>
        <div class="test" id="main">has both</div>
        <div class="test">has class only</div>
        <div id="other">has id only</div>
        <div>has neither</div>
    </root>
    '''
    tree = etree.fromstring(xml)

    # Match elements with BOTH class AND id
    factory = all_of(has_attribute("class"), has_attribute("id"))
    predicate = factory(tree)

    divs = tree.findall("div")

    assert predicate(divs[0]) is True  # has both
    assert predicate(divs[1]) is False  # has class only
    assert predicate(divs[2]) is False  # has id only
    assert predicate(divs[3]) is False  # has neither


def test_all_of_specific_values():
    """Test all_of with specific attribute value predicates."""
    xml = '''
    <root>
        <div class="test" data-type="button">match</div>
        <div class="test" data-type="link">no match</div>
        <div class="other" data-type="button">no match</div>
        <div class="test">no match</div>
    </root>
    '''
    tree = etree.fromstring(xml)

    # Match elements with class="test" AND data-type="button"
    factory = all_of(
        attribute_equals("class", "test"),
        attribute_equals("data-type", "button")
    )
    predicate = factory(tree)

    divs = tree.findall("div")

    assert predicate(divs[0]) is True  # matches both
    assert predicate(divs[1]) is False  # class=test, data-type=link
    assert predicate(divs[2]) is False  # class=other, data-type=button
    assert predicate(divs[3]) is False  # class=test, no data-type


def test_all_of_no_predicates():
    """Test all_of with no predicate arguments."""
    xml = "<root><div>content</div></root>"
    tree = etree.fromstring(xml)

    factory = all_of()  # No predicates
    predicate = factory(tree)

    div_elem = tree.find("div")
    root_elem = tree

    # Should match everything (empty AND is true)
    assert predicate(div_elem) is True
    assert predicate(root_elem) is True


def test_not_matching_simple_negation():
    """Test not_matching with simple predicate negation."""
    xml = "<root><div>div content</div><span>span content</span></root>"
    tree = etree.fromstring(xml)

    # Match elements that are NOT div
    factory = not_matching(tag_equals("div"))
    predicate = factory(tree)

    div_elem = tree.find("div")
    span_elem = tree.find("span")
    root_elem = tree

    assert predicate(div_elem) is False
    assert predicate(span_elem) is True
    assert predicate(root_elem) is True


def test_not_matching_attribute_negation():
    """Test not_matching with attribute predicate negation."""
    xml = '''
    <root>
        <div class="test">has class</div>
        <div>no class</div>
        <span class="other">has class</span>
    </root>
    '''
    tree = etree.fromstring(xml)

    # Match elements that do NOT have a class attribute
    factory = not_matching(has_attribute("class"))
    predicate = factory(tree)

    div_with_class = tree.find("div[@class]")
    div_without_class = tree.xpath("//div[not(@class)]")[0]
    span_with_class = tree.find("span")
    root_elem = tree

    assert predicate(div_with_class) is False
    assert predicate(div_without_class) is True
    assert predicate(span_with_class) is False
    assert predicate(root_elem) is True


def test_nested_combinators():
    """Test complex nested combinator predicates."""
    xml = '''
    <root>
        <div class="highlight" data-type="important">match1</div>
        <div class="normal" data-type="important">no match</div>
        <span class="highlight" data-type="info">no match</span>
        <div class="highlight">no match</div>
        <p class="highlight" data-type="important">match2</p>
    </root>
    '''
    tree = etree.fromstring(xml)

    # Match (div OR p) AND (has class="highlight") AND (has data-type="important")
    factory = all_of(
        any_of(tag_equals("div"), tag_equals("p")),
        attribute_equals("class", "highlight"),
        attribute_equals("data-type", "important")
    )
    predicate = factory(tree)

    div1 = tree.find("div[@class='highlight'][@data-type='important']")
    div2 = tree.find("div[@class='normal']")
    span = tree.find("span")
    div3 = tree.xpath("//div[@class='highlight' and not(@data-type)]")[0]
    p = tree.find("p")

    assert predicate(div1) is True  # matches all conditions
    assert predicate(div2) is False  # class=normal
    assert predicate(span) is False  # not div or p
    assert predicate(div3) is False  # no data-type
    assert predicate(p) is True  # matches all conditions


def test_double_negation():
    """Test double negation with not_matching."""
    xml = "<root><div>div content</div><span>span content</span></root>"
    tree = etree.fromstring(xml)

    # NOT (NOT div) should be equivalent to div
    factory = not_matching(not_matching(tag_equals("div")))
    predicate = factory(tree)

    div_elem = tree.find("div")
    span_elem = tree.find("span")

    assert predicate(div_elem) is True
    assert predicate(span_elem) is False


def test_complex_real_world_scenario():
    """Test a complex real-world combinator scenario."""
    xml = '''
    <html>
        <head>
            <title>Page Title</title>
            <link rel="stylesheet" href="style.css" type="text/css"/>
            <script src="app.js" type="text/javascript"></script>
        </head>
        <body>
            <div class="container" id="main">
                <h1>Heading</h1>
                <p class="intro">Introduction paragraph</p>
                <div class="content">
                    <span class="highlight">highlighted text</span>
                </div>
            </div>
        </body>
    </html>
    '''
    tree = etree.fromstring(xml)

    # Find content elements: (div OR p) AND (has class) AND NOT (in head section)
    # This is a bit simplified since we can't easily detect "in head" without parent checking
    content_factory = all_of(
        any_of(tag_equals("div"), tag_equals("p")),
        has_attribute("class"),
        not_matching(tag_in("title", "link", "script"))  # Exclude head elements
    )

    predicate = content_factory(tree)

    container_div = tree.find(".//div[@class='container']")
    content_div = tree.find(".//div[@class='content']")
    intro_p = tree.find(".//p[@class='intro']")
    plain_divs = tree.xpath(".//div[not(@class)]")
    plain_div = plain_divs[0] if plain_divs else None
    h1 = tree.find(".//h1")

    assert predicate(container_div) is True  # div with class
    assert predicate(content_div) is True  # div with class
    assert predicate(intro_p) is True  # p with class
    assert predicate(h1) is False  # h1, not div or p


def test_combinator_reusable_factories():
    """Test that combinator factories work with different documents."""
    # Create a reusable factory for divs with class attributes
    factory = all_of(tag_equals("div"), has_attribute("class"))

    # First document
    xml1 = '<root><div class="test">has class</div><div>no class</div></root>'
    tree1 = etree.fromstring(xml1)
    predicate1 = factory(tree1)

    div_with_class1 = tree1.find("div[@class]")
    div_without_class1 = tree1.xpath("//div[not(@class)]")[0]

    assert predicate1(div_with_class1) is True
    assert predicate1(div_without_class1) is False

    # Second document with different structure
    xml2 = '<document><div id="main" class="container">match</div><span class="test">no match</span></document>'
    tree2 = etree.fromstring(xml2)
    predicate2 = factory(tree2)

    div2 = tree2.find("div")
    span2 = tree2.find("span")

    assert predicate2(div2) is True
    assert predicate2(span2) is False