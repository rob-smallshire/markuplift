from io import StringIO
from lxml import etree
from markuplift.annotation import (
    PRESERVE_WHITESPACE_ANNOTATION,
    WHITESPACE_ANNOTATION_KEY,
    Annotations,
    annotate_explicit_whitespace_preserving_elements,
    annotate_xml_space, annotate_whitespace_preserving_descendants_as_whitespace_preserving,
    STRICT_WHITESPACE_ANNOTATION,
)
from markuplift.utilities import tagname

def parse(xml):
    return etree.parse(StringIO(xml))

def test_explicit_preserve_on_element():
    tree = parse("""
    <root>
        <preserve/>
        <normal/>
    </root>
    """)
    annotations = Annotations()
    # Predicate matches only <preserve>
    annotate_explicit_whitespace_preserving_elements(tree, annotations, lambda e: tagname(e) == "preserve")
    preserve = tree.getroot().find("preserve")
    normal = tree.getroot().find("normal")
    assert annotations.annotation(preserve, WHITESPACE_ANNOTATION_KEY) == PRESERVE_WHITESPACE_ANNOTATION
    assert annotations.annotation(normal, WHITESPACE_ANNOTATION_KEY) is None

def test_explicit_preserve_on_multiple_elements():
    tree = parse("""
    <root>
        <preserve1/>
        <preserve2/>
        <normal/>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_whitespace_preserving_elements(tree, annotations, lambda e: tagname(e) in {"preserve1", "preserve2"})
    assert annotations.annotation(tree.getroot().find("preserve1"), WHITESPACE_ANNOTATION_KEY) == PRESERVE_WHITESPACE_ANNOTATION
    assert annotations.annotation(tree.getroot().find("preserve2"), WHITESPACE_ANNOTATION_KEY) == PRESERVE_WHITESPACE_ANNOTATION
    assert annotations.annotation(tree.getroot().find("normal"), WHITESPACE_ANNOTATION_KEY) is None

def test_explicit_preserve_on_comment_and_pi():
    tree = parse("""
    <root>
        <!-- comment -->
        <?pi data?>
        <normal/>
    </root>
    """)
    annotations = Annotations()
    def predicate(e):
        from lxml import etree
        return isinstance(e, (etree._Comment, etree._ProcessingInstruction))
    annotate_explicit_whitespace_preserving_elements(tree, annotations, predicate)
    comment = tree.getroot().getchildren()[0]
    pi = tree.getroot().getchildren()[1]
    normal = tree.getroot().find("normal")
    assert annotations.annotation(comment, WHITESPACE_ANNOTATION_KEY) == PRESERVE_WHITESPACE_ANNOTATION
    assert annotations.annotation(pi, WHITESPACE_ANNOTATION_KEY) == PRESERVE_WHITESPACE_ANNOTATION
    assert annotations.annotation(normal, WHITESPACE_ANNOTATION_KEY) is None


def test_explicit_preserve_stopped_by_normalize():
    tree = parse("""
    <root>
        <preserve>
            <normalize xml:space="default">
                <child/>
            </normalize>
        </preserve>
    </root>
    """)
    annotations = Annotations()
    # Predicate matches <preserve>
    annotate_explicit_whitespace_preserving_elements(tree, annotations, lambda e: tagname(e) == "preserve")
    preserve = tree.getroot().find("preserve")
    normalize = preserve.find("normalize")
    child = normalize.find("child")
    # <normalize> should not inherit preserve due to xml:space="default"
    assert annotations.annotation(preserve, WHITESPACE_ANNOTATION_KEY) == PRESERVE_WHITESPACE_ANNOTATION
    assert annotations.annotation(normalize, WHITESPACE_ANNOTATION_KEY) is None
    assert annotations.annotation(child, WHITESPACE_ANNOTATION_KEY) is None


def test_xml_space_preserve_takes_precedence():
    tree = parse("""
    <root>
        <preserve xml:space="preserve">
            <child/>
        </preserve>
        <normal>
            <child xml:space="preserve"/>
        </normal>
    </root>
    """)
    annotations = Annotations()
    # Predicate matches only <normal>
    annotate_explicit_whitespace_preserving_elements(tree, annotations, lambda e: tagname(e) == "normal")
    annotate_whitespace_preserving_descendants_as_whitespace_preserving(tree, annotations)
    annotate_xml_space(tree, annotations)
    preserve = tree.getroot().find("preserve")
    preserve_child = preserve.find("child")
    normal = tree.getroot().find("normal")
    normal_child = normal.find("child")
    # xml:space="preserve" must take precedence
    assert annotations.annotation(preserve, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(preserve_child, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(normal, WHITESPACE_ANNOTATION_KEY) == PRESERVE_WHITESPACE_ANNOTATION  # predicate matched
    assert annotations.annotation(normal_child, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION  # xml:space wins


def test_explicit_and_xml_space_preserve_combined():
    tree = parse("""
    <root>
        <preserve xml:space="preserve">
            <child/>
        </preserve>
        <explicit>
            <child/>
        </explicit>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_whitespace_preserving_elements(tree, annotations, lambda e: tagname(e) == "explicit")
    annotate_whitespace_preserving_descendants_as_whitespace_preserving(tree, annotations)
    annotate_xml_space(tree, annotations)
    preserve = tree.getroot().find("preserve")
    preserve_child = preserve.find("child")
    explicit = tree.getroot().find("explicit")
    explicit_child = explicit.find("child")
    assert annotations.annotation(preserve, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(preserve_child, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(explicit, WHITESPACE_ANNOTATION_KEY) == PRESERVE_WHITESPACE_ANNOTATION
    assert annotations.annotation(explicit_child, WHITESPACE_ANNOTATION_KEY) == PRESERVE_WHITESPACE_ANNOTATION
