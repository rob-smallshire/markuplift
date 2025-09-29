from io import StringIO
from lxml import etree
from markuplift.annotation import (
    WHITESPACE_ANNOTATION_KEY,
    PRESERVE_WHITESPACE_ANNOTATION,
    NORMALIZE_WHITESPACE_ANNOTATION,
    Annotations,
    annotate_xml_space,
    annotate_explicit_whitespace_preserving_elements,
    annotate_explicit_whitespace_normalizing_elements,
    STRICT_WHITESPACE_ANNOTATION,
    annotate_whitespace_preserving_descendants_as_whitespace_preserving,
)
from markuplift.utilities import tagname


def parse(xml):
    return etree.parse(StringIO(xml))


def test_normalize_on_element():
    tree = parse("""
    <root>
        <normalize/>
        <preserve/>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_whitespace_normalizing_elements(tree, annotations, lambda e: tagname(e) == "normalize")
    normalize = tree.getroot().find("normalize")
    preserve = tree.getroot().find("preserve")
    assert annotations.annotation(normalize, WHITESPACE_ANNOTATION_KEY) == NORMALIZE_WHITESPACE_ANNOTATION
    assert annotations.annotation(preserve, WHITESPACE_ANNOTATION_KEY) is None


def test_normalize_on_multiple_elements():
    tree = parse("""
    <root>
        <normalize1/>
        <normalize2/>
        <preserve/>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_whitespace_normalizing_elements(
        tree, annotations, lambda e: tagname(e) in {"normalize1", "normalize2"}
    )
    assert (
        annotations.annotation(tree.getroot().find("normalize1"), WHITESPACE_ANNOTATION_KEY)
        == NORMALIZE_WHITESPACE_ANNOTATION
    )
    assert (
        annotations.annotation(tree.getroot().find("normalize2"), WHITESPACE_ANNOTATION_KEY)
        == NORMALIZE_WHITESPACE_ANNOTATION
    )
    assert annotations.annotation(tree.getroot().find("preserve"), WHITESPACE_ANNOTATION_KEY) is None


def test_normalize_on_comment_and_pi():
    tree = parse("""
    <root>
        <!-- comment -->
        <?pi data?>
        <preserve/>
    </root>
    """)
    annotations = Annotations()

    def predicate(e):
        from lxml import etree

        return isinstance(e, (etree._Comment, etree._ProcessingInstruction))

    annotate_explicit_whitespace_normalizing_elements(tree, annotations, predicate)
    comment = tree.getroot().getchildren()[0]
    pi = tree.getroot().getchildren()[1]
    preserve = tree.getroot().find("preserve")
    assert annotations.annotation(comment, WHITESPACE_ANNOTATION_KEY) == NORMALIZE_WHITESPACE_ANNOTATION
    assert annotations.annotation(pi, WHITESPACE_ANNOTATION_KEY) == NORMALIZE_WHITESPACE_ANNOTATION
    assert annotations.annotation(preserve, WHITESPACE_ANNOTATION_KEY) is None


def test_normalize_does_not_propagate_to_descendants():
    tree = parse("""
    <root>
        <normalize>
            <child/>
        </normalize>
        <preserve>
            <child/>
        </preserve>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_whitespace_normalizing_elements(tree, annotations, lambda e: tagname(e) == "normalize")
    normalize = tree.getroot().find("normalize")
    normalize_child = normalize.find("child")
    preserve = tree.getroot().find("preserve")
    preserve_child = preserve.find("child")
    assert annotations.annotation(normalize, WHITESPACE_ANNOTATION_KEY) == NORMALIZE_WHITESPACE_ANNOTATION
    assert annotations.annotation(normalize_child, WHITESPACE_ANNOTATION_KEY) is None
    assert annotations.annotation(preserve, WHITESPACE_ANNOTATION_KEY) is None
    assert annotations.annotation(preserve_child, WHITESPACE_ANNOTATION_KEY) is None


def test_normalize_does_not_override_strict():
    tree = parse("""
    <root>
        <preserve xml:space="preserve">
            <normalize/>
        </preserve>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_whitespace_normalizing_elements(tree, annotations, lambda e: tagname(e) == "normalize")
    annotate_xml_space(tree, annotations)
    preserve = tree.getroot().find("preserve")
    normalize = preserve.find("normalize")
    assert annotations.annotation(preserve, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(normalize, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION


def test_normalize_overrides_explicit_preserve():
    tree = parse("""
    <root>
        <preserve>
            <normalize/>
        </preserve>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_whitespace_preserving_elements(tree, annotations, lambda e: tagname(e) == "preserve")
    annotate_whitespace_preserving_descendants_as_whitespace_preserving(tree, annotations)
    annotate_explicit_whitespace_normalizing_elements(tree, annotations, lambda e: tagname(e) == "normalize")
    preserve = tree.getroot().find("preserve")
    normalize = preserve.find("normalize")
    assert annotations.annotation(preserve, WHITESPACE_ANNOTATION_KEY) == PRESERVE_WHITESPACE_ANNOTATION
    assert annotations.annotation(normalize, WHITESPACE_ANNOTATION_KEY) == NORMALIZE_WHITESPACE_ANNOTATION


def test_normalize_on_descendants_of_strict_whitespace_is_ignored():
    tree = parse("""
    <root xml:space="preserve">
        <normalize>
            <child/>
        </normalize>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_whitespace_normalizing_elements(tree, annotations, lambda e: tagname(e) == "normalize")
    annotate_xml_space(tree, annotations)
    root = tree.getroot()
    normalize = root.find("normalize")
    child = normalize.find("child")
    assert annotations.annotation(root, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(normalize, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION
    assert annotations.annotation(child, WHITESPACE_ANNOTATION_KEY) == STRICT_WHITESPACE_ANNOTATION


def test_normalize_on_comment_and_pi_with_preserve():
    tree = parse("""
    <root xml:space="preserve">
        <!-- comment -->
        <?pi data?>
        <normalize/>
    </root>
    """)
    annotations = Annotations()
    annotate_xml_space(tree, annotations)

    def predicate(e):
        from lxml import etree

        return isinstance(e, (etree._Comment, etree._ProcessingInstruction)) or tagname(e) == "normalize"

    annotate_explicit_whitespace_normalizing_elements(tree, annotations, predicate)
    root = tree.getroot()
    comment = root.getchildren()[0]
    pi = root.getchildren()[1]
    normalize = root.find("normalize")
    assert annotations.annotation(comment, WHITESPACE_ANNOTATION_KEY) == NORMALIZE_WHITESPACE_ANNOTATION
    assert annotations.annotation(pi, WHITESPACE_ANNOTATION_KEY) == NORMALIZE_WHITESPACE_ANNOTATION
    assert annotations.annotation(normalize, WHITESPACE_ANNOTATION_KEY) == NORMALIZE_WHITESPACE_ANNOTATION
