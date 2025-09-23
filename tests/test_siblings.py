from lxml import etree
from typename import typename

from markuplift.utilities import siblings

# Helper to get node types for assertion clarity
def node_type(node):
    if isinstance(node, etree._Comment):
        return "comment"
    elif isinstance(node, etree._ProcessingInstruction):
        return f"pi:{node.target}"
    elif isinstance(node, etree._Element):
        return f"element:{node.tag}"

    assert False, f"Unexpected node type: f{typename(node)}"


def test_siblings_elements_only():
    xml = """
    <root>
        <a/>
        <b/>
        <c/>
    </root>
    """
    tree = etree.fromstring(xml)
    b = tree[1]
    sibs = siblings(b)
    assert [node.tag for node in sibs] == ["a", "b", "c"]
    assert b in sibs


def test_siblings_with_comment_and_pi():
    xml = """
    <root>
        <a/>
        <!-- a comment -->
        <?pi target?>
        <b/>
    </root>
    """
    parser = etree.XMLParser(remove_comments=False, remove_pis=False)
    tree = etree.fromstring(xml, parser)
    nodes = list(tree)
    # Find comment and PI
    comment = next(n for n in nodes if isinstance(n, etree._Comment))
    pi = next(n for n in nodes if isinstance(n, etree._ProcessingInstruction))
    b = next(n for n in nodes if isinstance(n, etree._Element) and n.tag == "b")
    # Siblings of comment
    sibs_comment = siblings(comment)
    assert [node_type(n) for n in sibs_comment] == ["element:a", "comment", "pi:pi", "element:b"]
    # Siblings of PI
    sibs_pi = siblings(pi)
    assert [node_type(n) for n in sibs_pi] == ["element:a", "comment", "pi:pi", "element:b"]
    # Siblings of b
    sibs_b = siblings(b)
    assert [node_type(n) for n in sibs_b] == ["element:a", "comment", "pi:pi", "element:b"]


def test_siblings_root_element():
    xml = "<root><a/></root>"
    tree = etree.fromstring(xml)
    sibs = siblings(tree)
    assert sibs == [tree]


def test_siblings_only_child():
    xml = "<root><a/></root>"
    tree = etree.fromstring(xml)
    a = tree[0]
    sibs = siblings(a)
    assert [node.tag for node in sibs] == ["a"]


def test_siblings_first_and_last_child():
    xml = "<root><a/><!--c--><?pi?><b/></root>"
    parser = etree.XMLParser(remove_comments=False, remove_pis=False)
    tree = etree.fromstring(xml, parser)
    nodes = list(tree)
    a = nodes[0]
    comment = nodes[1]
    pi = nodes[2]
    b = nodes[3]
    # First child
    sibs_a = siblings(a)
    assert [node_type(n) for n in sibs_a] == ["element:a", "comment", "pi:pi", "element:b"]
    # Last child
    sibs_b = siblings(b)
    assert [node_type(n) for n in sibs_b] == ["element:a", "comment", "pi:pi", "element:b"]


def test_siblings_mixed_content():
    xml = """
    <root>
        <a/>
        <!--c-->
        <?pi?>
        <b/>
        <!--d-->
    </root>
    """
    parser = etree.XMLParser(remove_comments=False, remove_pis=False)
    tree = etree.fromstring(xml, parser)
    nodes = list(tree)
    comment_d = [n for n in nodes if isinstance(n, etree._Comment)][1]
    sibs_d = siblings(comment_d)
    assert [node_type(n) for n in sibs_d] == ["element:a", "comment", "pi:pi", "element:b", "comment"]
