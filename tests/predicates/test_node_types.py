from lxml import etree

from markuplift.predicates import is_comment, is_processing_instruction, is_element


def test_is_comment_matches_comments():
    """Test is_comment predicate with comment nodes."""
    xml = """
    <root>
        <!-- This is a comment -->
        <div>content</div>
        <!-- Another comment -->
    </root>
    """
    tree = etree.fromstring(xml)

    factory = is_comment()
    predicate = factory(tree)

    # Get all nodes including comments
    all_nodes = []
    for node in tree.iter():
        all_nodes.append(node)
    for comment in tree.xpath("//comment()"):
        all_nodes.append(comment)

    div_elem = tree.find("div")
    root_elem = tree
    comments = tree.xpath("//comment()")

    assert predicate(div_elem) is False
    assert predicate(root_elem) is False

    for comment in comments:
        assert predicate(comment) is True


def test_is_processing_instruction_matches_pis():
    """Test is_processing_instruction predicate with PI nodes."""
    xml = """
    <root>
        <?xml-stylesheet type="text/xsl" href="style.xsl"?>
        <div>content</div>
        <?processing-instruction data?>
    </root>
    """
    tree = etree.fromstring(xml)

    factory = is_processing_instruction()
    predicate = factory(tree)

    div_elem = tree.find("div")
    root_elem = tree
    pis = tree.xpath("//processing-instruction()")

    assert predicate(div_elem) is False
    assert predicate(root_elem) is False

    for pi in pis:
        assert predicate(pi) is True


def test_is_processing_instruction_with_target():
    """Test is_processing_instruction with specific target filtering."""
    xml = """
    <root>
        <?xml-stylesheet type="text/xsl" href="style.xsl"?>
        <div>content</div>
        <?processing-instruction data?>
        <?another-target data?>
    </root>
    """
    tree = etree.fromstring(xml)

    stylesheet_factory = is_processing_instruction("xml-stylesheet")
    general_factory = is_processing_instruction("processing-instruction")

    stylesheet_predicate = stylesheet_factory(tree)
    general_predicate = general_factory(tree)

    pis = tree.xpath("//processing-instruction()")

    # Find specific PIs by target
    stylesheet_pi = None
    general_pi = None
    other_pi = None

    for pi in pis:
        if pi.target == "xml-stylesheet":
            stylesheet_pi = pi
        elif pi.target == "processing-instruction":
            general_pi = pi
        elif pi.target == "another-target":
            other_pi = pi

    if stylesheet_pi is not None:
        assert stylesheet_predicate(stylesheet_pi) is True
    if general_pi is not None:
        assert general_predicate(general_pi) is True
    if other_pi is not None:
        assert stylesheet_predicate(other_pi) is False
        assert general_predicate(other_pi) is False


def test_is_element_matches_regular_elements():
    """Test is_element predicate with regular element nodes."""
    xml = """
    <root>
        <!-- This is a comment -->
        <div>content</div>
        <?processing-instruction data?>
        <span>more content</span>
    </root>
    """
    tree = etree.fromstring(xml)

    factory = is_element()
    predicate = factory(tree)

    div_elem = tree.find("div")
    span_elem = tree.find("span")
    root_elem = tree
    comments = tree.xpath("//comment()")
    pis = tree.xpath("//processing-instruction()")

    # Regular elements should match
    assert predicate(div_elem) is True
    assert predicate(span_elem) is True
    assert predicate(root_elem) is True

    # Comments and PIs should not match
    for comment in comments:
        assert predicate(comment) is False
    for pi in pis:
        assert predicate(pi) is False


def test_node_type_predicates_mixed_content():
    """Test all node type predicates with mixed content."""
    xml = """
    <root>
        <!-- Comment 1 -->
        <div>Element 1</div>
        <?stylesheet href="test.css"?>
        <!-- Comment 2 -->
        <span>Element 2</span>
        <?script src="test.js"?>
    </root>
    """
    tree = etree.fromstring(xml)

    comment_factory = is_comment()
    pi_factory = is_processing_instruction()
    element_factory = is_element()

    comment_predicate = comment_factory(tree)
    pi_predicate = pi_factory(tree)
    element_predicate = element_factory(tree)

    # Get all different node types
    elements = [tree, tree.find("div"), tree.find("span")]
    comments = tree.xpath("//comment()")
    pis = tree.xpath("//processing-instruction()")

    # Test comment predicate
    for elem in elements:
        assert comment_predicate(elem) is False
    for comment in comments:
        assert comment_predicate(comment) is True
    for pi in pis:
        assert comment_predicate(pi) is False

    # Test PI predicate
    for elem in elements:
        assert pi_predicate(elem) is False
    for comment in comments:
        assert pi_predicate(comment) is False
    for pi in pis:
        assert pi_predicate(pi) is True

    # Test element predicate
    for elem in elements:
        assert element_predicate(elem) is True
    for comment in comments:
        assert element_predicate(comment) is False
    for pi in pis:
        assert element_predicate(pi) is False


def test_node_type_predicates_empty_document():
    """Test node type predicates with minimal document."""
    xml = "<root></root>"
    tree = etree.fromstring(xml)

    comment_factory = is_comment()
    pi_factory = is_processing_instruction()
    element_factory = is_element()

    comment_predicate = comment_factory(tree)
    pi_predicate = pi_factory(tree)
    element_predicate = element_factory(tree)

    root_elem = tree

    assert comment_predicate(root_elem) is False
    assert pi_predicate(root_elem) is False
    assert element_predicate(root_elem) is True


def test_node_type_predicates_reusable_factories():
    """Test that node type factories work with different documents."""
    comment_factory = is_comment()
    pi_factory = is_processing_instruction()
    element_factory = is_element()

    # First document
    xml1 = "<root><!-- comment --><div>content</div></root>"
    tree1 = etree.fromstring(xml1)

    comment_pred1 = comment_factory(tree1)
    pi_pred1 = pi_factory(tree1)
    element_pred1 = element_factory(tree1)

    comments1 = tree1.xpath("//comment()")
    div1 = tree1.find("div")

    assert comment_pred1(comments1[0]) is True if comments1 else True
    assert pi_pred1(div1) is False
    assert element_pred1(div1) is True

    # Second document
    xml2 = "<document><?xml-stylesheet href='style.css'?><p>text</p></document>"
    tree2 = etree.fromstring(xml2)

    comment_pred2 = comment_factory(tree2)
    pi_pred2 = pi_factory(tree2)
    element_pred2 = element_factory(tree2)

    pis2 = tree2.xpath("//processing-instruction()")
    p2 = tree2.find("p")

    assert pi_pred2(pis2[0]) is True if pis2 else True
    assert comment_pred2(p2) is False
    assert element_pred2(p2) is True