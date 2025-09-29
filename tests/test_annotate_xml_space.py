from lxml import etree
from markuplift.annotation import (
    annotate_xml_space,
    Annotations,
    WHITESPACE_ANNOTATION_KEY,
    STRICT_WHITESPACE_ANNOTATION,
)


def get_annotated_nodes(tree, annotations, key, value):
    return [el for el in tree.iter() if annotations.annotation(el, key) == value]


def test_propagation_from_root():
    xml = """<root xml:space="preserve"><a><b/></a><c/></root>"""
    tree = etree.fromstring(xml)
    annotations = Annotations()
    annotate_xml_space(tree, annotations)
    for el in tree.iter():
        assert annotations.annotation(el, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION


def test_override_by_descendant():
    xml = """<root xml:space="preserve"><a xml:space="default"><b/></a><c/></root>"""
    tree = etree.fromstring(xml)
    annotations = Annotations()
    annotate_xml_space(tree, annotations)
    # root and c should be annotated, a and b should not
    root, a, b, c = tree, tree[0], tree[0][0], tree[1]
    assert annotations.annotation(root, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(c, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(a, WHITESPACE_ANNOTATION_KEY) is None
    assert annotations.annotation(b, WHITESPACE_ANNOTATION_KEY) is None


def test_mixed_propagation():
    xml = """<root><a xml:space="preserve"><b/></a><c xml:space="default"><d/></c></root>"""
    tree = etree.fromstring(xml)
    annotations = Annotations()
    annotate_xml_space(tree, annotations)
    a, b, c, d = tree[0], tree[0][0], tree[1], tree[1][0]
    assert annotations.annotation(a, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(b, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(c, WHITESPACE_ANNOTATION_KEY) is None
    assert annotations.annotation(d, WHITESPACE_ANNOTATION_KEY) is None


def test_no_xml_space():
    xml = """<root><a><b/></a><c/></root>"""
    tree = etree.fromstring(xml)
    annotations = Annotations()
    annotate_xml_space(tree, annotations)
    for el in tree.iter():
        assert annotations.annotation(el, WHITESPACE_ANNOTATION_KEY) is None


def test_multiple_nested_overrides():
    xml = """<root xml:space="preserve"><a xml:space="default"><b xml:space="preserve"/></a><c/></root>"""
    tree = etree.fromstring(xml)
    annotations = Annotations()
    annotate_xml_space(tree, annotations)
    root, a, b, c = tree, tree[0], tree[0][0], tree[1]
    assert annotations.annotation(root, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(a, WHITESPACE_ANNOTATION_KEY) is None
    assert annotations.annotation(b, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(c, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION


def test_non_element_nodes():
    xml = """<root xml:space="preserve"><a><!-- comment --></a><?pi test?><b/></root>"""
    tree = etree.fromstring(xml)
    annotations = Annotations()
    annotate_xml_space(tree, annotations)
    # Only elements should be annotated
    for el in tree.iter():
        assert annotations.annotation(el, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    # Comments and PIs are not elements in lxml.etree.fromstring, so not annotated
