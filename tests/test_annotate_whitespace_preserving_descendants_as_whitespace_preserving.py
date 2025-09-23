from io import StringIO
from lxml import etree
from markuplift.annotation import (
    WHITESPACE_ANNOTATION_KEY,
    PRESERVE_WHITESPACE_ANNOTATION,
    Annotations,
    annotate_xml_space,
    annotate_explicit_whitespace_preserving_elements,
    annotate_whitespace_preserving_descendants_as_whitespace_preserving,
    STRICT_WHITESPACE_ANNOTATION,
)
from markuplift.utilities import tagname
def parse(xml):
    return etree.parse(StringIO(xml))

def test_descendants_annotated_from_xml_space_preserve():
    tree = parse("""
    <root xml:space="preserve">
        <child1/>
        <child2>
            <grandchild/>
        </child2>
    </root>
    """)
    annotations = Annotations()
    annotate_xml_space(tree, annotations)
    root = tree.getroot()
    child1 = root.find("child1")
    child2 = root.find("child2")
    grandchild = child2.find("grandchild")
    assert annotations.annotation(root, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(child1, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(child2, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(grandchild, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION

def test_descendants_annotated_from_explicit_preserve():
    tree = parse("""
    <root>
        <preserve>
            <child/>
        </preserve>
        <normal>
            <child/>
        </normal>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_whitespace_preserving_elements(tree, annotations, lambda e: tagname(e) == "preserve")
    annotate_whitespace_preserving_descendants_as_whitespace_preserving(tree, annotations)
    preserve = tree.getroot().find("preserve")
    preserve_child = preserve.find("child")
    normal = tree.getroot().find("normal")
    normal_child = normal.find("child")
    assert annotations.annotation(preserve, WHITESPACE_ANNOTATION_KEY) == PRESERVE_WHITESPACE_ANNOTATION
    assert annotations.annotation(preserve_child, WHITESPACE_ANNOTATION_KEY) == PRESERVE_WHITESPACE_ANNOTATION
    assert annotations.annotation(normal, WHITESPACE_ANNOTATION_KEY) is None
    assert annotations.annotation(normal_child, WHITESPACE_ANNOTATION_KEY) is None

def test_propagation_stopped_by_xml_space_default():
    tree = parse("""
    <root xml:space="preserve">
        <default xml:space="default">
            <child/>
        </default>
    </root>
    """)
    annotations = Annotations()
    annotate_xml_space(tree, annotations)
    root = tree.getroot()
    default = root.find("default")
    child = default.find("child")
    assert annotations.annotation(root, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(default, WHITESPACE_ANNOTATION_KEY) is None
    assert annotations.annotation(child, WHITESPACE_ANNOTATION_KEY) is None

def test_mixed_explicit_and_xml_space_preserve():
    tree = parse("""
    <root>
        <explicit>
            <child/>
        </explicit>
        <xmlspace xml:space="preserve">
            <child/>
        </xmlspace>
    </root>
    """)
    annotations = Annotations()
    annotate_xml_space(tree, annotations)
    annotate_explicit_whitespace_preserving_elements(tree, annotations, lambda e: getattr(e, 'tag', None) == "explicit")
    annotate_explicit_whitespace_preserving_elements(tree, annotations, lambda e: tagname(e) == "explicit")
    annotate_whitespace_preserving_descendants_as_whitespace_preserving(tree, annotations)
    explicit = tree.getroot().find("explicit")
    explicit_child = explicit.find("child")
    xmlspace = tree.getroot().find("xmlspace")
    xmlspace_child = xmlspace.find("child")
    assert annotations.annotation(explicit, WHITESPACE_ANNOTATION_KEY) == PRESERVE_WHITESPACE_ANNOTATION
    assert annotations.annotation(explicit_child, WHITESPACE_ANNOTATION_KEY) == PRESERVE_WHITESPACE_ANNOTATION
    assert annotations.annotation(xmlspace, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(xmlspace_child, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION

def test_nested_preserve_and_default():
    tree = parse("""
    <root xml:space="preserve">
        <outer>
            <inner xml:space="default">
                <deep/>
            </inner>
        </outer>
    </root>
    """)
    annotations = Annotations()
    annotate_xml_space(tree, annotations)
    root = tree.getroot()
    outer = root.find("outer")
    inner = outer.find("inner")
    deep = inner.find("deep")
    assert annotations.annotation(root, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(outer, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(inner, WHITESPACE_ANNOTATION_KEY) is None
    assert annotations.annotation(deep, WHITESPACE_ANNOTATION_KEY) is None

def test_comment_and_pi_descendants():
    tree = parse("""
    <root xml:space="preserve">
        <!-- comment -->
        <?pi data?>
        <child/>
    </root>
    """)
    annotations = Annotations()
    annotate_xml_space(tree, annotations)
    root = tree.getroot()
    comment = root.getchildren()[0]
    pi = root.getchildren()[1]
    child = root.find("child")
    assert annotations.annotation(comment, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(pi, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(child, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION

def test_preserve_propagation_with_mixed_initial_annotations():
    tree = parse("""
    <root>
        <explicit>
            <child xml:space="preserve">
                <grandchild/>
            </child>
        </explicit>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_whitespace_preserving_elements(tree, annotations, lambda e: getattr(e, 'tag', None) == "explicit")
    annotate_explicit_whitespace_preserving_elements(tree, annotations, lambda e: tagname(e) == "explicit")
    annotate_whitespace_preserving_descendants_as_whitespace_preserving(tree, annotations)
    annotate_xml_space(tree, annotations)
    explicit = tree.getroot().find("explicit")
    child = explicit.find("child")
    grandchild = child.find("grandchild")
    assert annotations.annotation(explicit, WHITESPACE_ANNOTATION_KEY) == PRESERVE_WHITESPACE_ANNOTATION
    assert annotations.annotation(child, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(grandchild, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
