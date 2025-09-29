from lxml import etree
from markuplift.utilities import tagname


def test_node_tagname_element():
    xml = "<root><child/></root>"
    tree = etree.fromstring(xml)
    assert tagname(tree) == "root"
    assert tagname(tree[0]) == "child"


def test_node_tagname_comment():
    xml = "<root><!-- a comment --></root>"
    parser = etree.XMLParser(remove_comments=False)
    tree = etree.fromstring(xml, parser)
    comment = next(n for n in tree if isinstance(n, etree._Comment))
    assert tagname(comment) == "#comment"


def test_node_tagname_processing_instruction():
    xml = "<root><?myproc some data?><child/></root>"
    parser = etree.XMLParser(remove_pis=False)
    tree = etree.fromstring(xml, parser)
    pi = next(n for n in tree if isinstance(n, etree._ProcessingInstruction))
    assert tagname(pi) == "?myproc"


def test_node_tagname_mixed():
    xml = """
    <root>
        <a/>
        <!-- comment -->
        <?pi data?>
        <b/>
    </root>
    """
    parser = etree.XMLParser(remove_comments=False, remove_pis=False)
    tree = etree.fromstring(xml, parser)
    nodes = list(tree)
    assert tagname(nodes[0]) == "a"
    assert tagname(nodes[1]) == "#comment"
    assert tagname(nodes[2]) == "?pi"
    assert tagname(nodes[3]) == "b"


def test_node_tagname_edge_cases():
    # Root element with no parent
    xml = "<root/>"
    tree = etree.fromstring(xml)
    assert tagname(tree) == "root"
    # Comment as only child
    xml = "<root><!--only--></root>"
    parser = etree.XMLParser(remove_comments=False)
    tree = etree.fromstring(xml, parser)
    comment = next(n for n in tree if isinstance(n, etree._Comment))
    assert tagname(comment) == "#comment"
    # PI as only child
    xml = "<root><?onlypi?></root>"
    parser = etree.XMLParser(remove_pis=False)
    tree = etree.fromstring(xml, parser)
    pi = next(n for n in tree if isinstance(n, etree._ProcessingInstruction))
    assert tagname(pi) == "?onlypi"
