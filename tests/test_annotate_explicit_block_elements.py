from inspect import cleandoc
from io import StringIO

from lxml import etree

from markuplift.annotation import TYPE_ANNOTATION_KEY, Annotations, annotate_explicit_block_elements, AnnotationConflictError, AnnotationConflictMode
from markuplift.utilities import tagname, siblings


def test_no_matches_no_annotation():
    tree = etree.parse(StringIO("<root/>"))
    annotations = Annotations()
    annotate_explicit_block_elements(tree, annotations, lambda e: False)
    assert annotations.annotation(tree.getroot(), TYPE_ANNOTATION_KEY) is None


def test_root_matches_block_annotation():
    tree = etree.parse(StringIO("<root/>"))
    annotations = Annotations()
    annotate_explicit_block_elements(tree, annotations, lambda e: e.tag == "root")
    assert annotations.annotation(tree.getroot(), TYPE_ANNOTATION_KEY) == "block"


def test_child_matches_block_annotation():
    tree = etree.parse(StringIO(cleandoc("""
        <root>
            <child/>
        </root>
    """)))
    annotations = Annotations()
    annotate_explicit_block_elements(tree, annotations, lambda e: e.tag == "child")
    assert annotations.annotation(tree.getroot(), TYPE_ANNOTATION_KEY) is None
    child = tree.getroot().find("child")
    assert annotations.annotation(child, TYPE_ANNOTATION_KEY) == "block"


def test_multiple_children_match_block_annotation():
    tree = etree.parse(StringIO(cleandoc("""
        <root>
            <child1/>
            <child2/>
        </root>
    """)))
    annotations = Annotations()
    annotate_explicit_block_elements(tree, annotations, lambda e: e.tag in {"child1", "child2"})
    assert annotations.annotation(tree.getroot(), TYPE_ANNOTATION_KEY) is None
    child1 = tree.getroot().find("child1")
    child2 = tree.getroot().find("child2")
    assert annotations.annotation(child1, TYPE_ANNOTATION_KEY) == "block"
    assert annotations.annotation(child2, TYPE_ANNOTATION_KEY) == "block"


def test_some_children_match_block_annotation():
    tree = etree.parse(StringIO(cleandoc("""
        <root>
            <child1/>
            <child2/>
            <child3/>
        </root>
    """)))
    annotations = Annotations()
    annotate_explicit_block_elements(tree, annotations, lambda e: e.tag in {"child1", "child3"})
    assert annotations.annotation(tree.getroot(), TYPE_ANNOTATION_KEY) is None
    child1 = tree.getroot().find("child1")
    child2 = tree.getroot().find("child2")
    child3 = tree.getroot().find("child3")
    assert annotations.annotation(child1, TYPE_ANNOTATION_KEY) == "block"
    assert annotations.annotation(child2, TYPE_ANNOTATION_KEY) is None
    assert annotations.annotation(child3, TYPE_ANNOTATION_KEY) == "block"


def test_comment_matches_block_annotation():
    tree = etree.parse(StringIO(cleandoc("""
        <root>
            <!-- A comment -->
        </root>
    """)))
    annotations = Annotations()
    annotate_explicit_block_elements(tree, annotations, lambda e: isinstance(e, etree._Comment))
    assert annotations.annotation(tree.getroot(), TYPE_ANNOTATION_KEY) is None
    comment = tree.getroot().getchildren()[0]
    assert isinstance(comment, etree._Comment)
    assert annotations.annotation(comment, TYPE_ANNOTATION_KEY) == "block"


def test_processing_instruction_matches_block_annotation():
    tree = etree.parse(StringIO(cleandoc("""
        <root>
            <?pi data?>
        </root>
    """)))
    annotations = Annotations()
    annotate_explicit_block_elements(tree, annotations, lambda e: isinstance(e, etree._ProcessingInstruction))
    assert annotations.annotation(tree.getroot(), TYPE_ANNOTATION_KEY) is None
    pi = tree.getroot().getchildren()[0]
    assert isinstance(pi, etree._ProcessingInstruction)
    assert annotations.annotation(pi, TYPE_ANNOTATION_KEY) == "block"


def test_complex_block_annotation_predicate_processing_instruction_as_sibling_of_div_matches():
    tree = etree.parse(StringIO(cleandoc("""
    <root>
        <?pi data?>
        <div/>
    </root>
    """)))
    annotations = Annotations()
    annotate_explicit_block_elements(
        tree,
        annotations,
        lambda e: isinstance(e, etree._ProcessingInstruction) and "div" in {tagname(sib) for sib in siblings(e)}
    )
