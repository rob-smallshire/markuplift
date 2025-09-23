from inspect import cleandoc
from io import StringIO

from lxml import etree

from markuplift.annotation import TYPE_ANNOTATION_KEY, Annotations, annotate_explicit_inline_elements, AnnotationConflictError, AnnotationConflictMode

def test_no_matches_no_annotation():
    tree = etree.parse(StringIO("<root/>"))
    annotations = Annotations()
    annotate_explicit_inline_elements(tree, annotations, lambda e: False)
    assert annotations.annotation(tree.getroot(), TYPE_ANNOTATION_KEY) is None

def test_root_matches_inline_annotation():
    tree = etree.parse(StringIO("<root/>"))
    annotations = Annotations()
    annotate_explicit_inline_elements(tree, annotations, lambda e: e.tag == "root")
    assert annotations.annotation(tree.getroot(), TYPE_ANNOTATION_KEY) == "inline"

def test_child_matches_inline_annotation():
    tree = etree.parse(StringIO(cleandoc("""
        <root>
            <child/>
        </root>
    """)))
    annotations = Annotations()
    annotate_explicit_inline_elements(tree, annotations, lambda e: e.tag == "child")
    assert annotations.annotation(tree.getroot(), TYPE_ANNOTATION_KEY) is None
    child = tree.getroot().find("child")
    assert annotations.annotation(child, TYPE_ANNOTATION_KEY) == "inline"

def test_multiple_children_match_inline_annotation():
    tree = etree.parse(StringIO(cleandoc("""
        <root>
            <child1/>
            <child2/>
        </root>
    """)))
    annotations = Annotations()
    annotate_explicit_inline_elements(tree, annotations, lambda e: e.tag in {"child1", "child2"})
    assert annotations.annotation(tree.getroot(), TYPE_ANNOTATION_KEY) is None
    child1 = tree.getroot().find("child1")
    child2 = tree.getroot().find("child2")
    assert annotations.annotation(child1, TYPE_ANNOTATION_KEY) == "inline"
    assert annotations.annotation(child2, TYPE_ANNOTATION_KEY) == "inline"

def test_annotation_conflict():
    tree = etree.parse(StringIO("<root/>"))
    annotations = Annotations()
    # First annotate as block
    annotations.annotate(tree.getroot(), TYPE_ANNOTATION_KEY, "block")
    # Now try to annotate as inline, should raise conflict
    try:
        annotate_explicit_inline_elements(tree, annotations, lambda e: True)
    except AnnotationConflictError as e:
        assert "previously marked as block" in str(e)
    else:
        assert False, "AnnotationConflictError not raised"

