from io import StringIO
from lxml import etree
from markuplift.annotation import (
    TYPE_ANNOTATION_KEY,
    Annotations,
    annotate_explicit_block_elements,
    annotate_explicit_inline_elements,
    annotate_elements_in_mixed_content_as_inline,
    annotate_inline_descendants_as_inline,
)
from markuplift.types import ElementType


def parse(xml):
    return etree.parse(StringIO(xml))


def test_descendants_of_inline_element_are_annotated_inline():
    tree = parse("""
    <root>
        <inline>
            <child/>
            <!-- comment -->
            <?pi data?>
        </inline>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_inline_elements(tree, annotations, lambda e: e.tag == "inline")
    annotate_inline_descendants_as_inline(tree, annotations)
    inline = tree.getroot().find("inline")
    child = inline.find("child")
    comment = inline.getchildren()[1]
    pi = inline.getchildren()[2]
    assert annotations.annotation(child, TYPE_ANNOTATION_KEY) == ElementType.INLINE
    assert annotations.annotation(comment, TYPE_ANNOTATION_KEY) == ElementType.INLINE
    assert annotations.annotation(pi, TYPE_ANNOTATION_KEY) == ElementType.INLINE


def test_descendants_already_block_remain_block():
    tree = parse("""
    <root>
        <inline>
            <child/>
            <!-- comment -->
            <?pi data?>
        </inline>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_inline_elements(tree, annotations, lambda e: e.tag == "inline")
    # Mark child and comment as block
    inline = tree.getroot().find("inline")
    child = inline.find("child")
    comment = inline.getchildren()[1]
    annotate_explicit_block_elements(tree, annotations, lambda e: e is child or e is comment)
    annotate_inline_descendants_as_inline(tree, annotations)
    assert annotations.annotation(child, TYPE_ANNOTATION_KEY) == ElementType.BLOCK
    assert annotations.annotation(comment, TYPE_ANNOTATION_KEY) == ElementType.BLOCK
    pi = inline.getchildren()[2]
    assert annotations.annotation(pi, TYPE_ANNOTATION_KEY) == ElementType.INLINE


def test_mixed_content_descendants():
    tree = parse("""
    <root>
        <inline>
            Text<child/>Text<!-- comment -->Text<?pi data?>
        </inline>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_inline_elements(tree, annotations, lambda e: e.tag == "inline")
    annotate_elements_in_mixed_content_as_inline(tree, annotations)
    annotate_inline_descendants_as_inline(tree, annotations)
    inline = tree.getroot().find("inline")
    child = inline.find("child")
    comment = inline.getchildren()[1]
    pi = inline.getchildren()[2]
    assert annotations.annotation(child, TYPE_ANNOTATION_KEY) == ElementType.INLINE
    assert annotations.annotation(comment, TYPE_ANNOTATION_KEY) == ElementType.INLINE
    assert annotations.annotation(pi, TYPE_ANNOTATION_KEY) == ElementType.INLINE


def test_deeply_nested_inline_with_block_descendant():
    tree = parse("""
    <root>
        <inline>
            <level1>
                <level2>
                    <block/>
                </level2>
            </level1>
        </inline>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_inline_elements(tree, annotations, lambda e: e.tag == "inline")
    block = tree.getroot().find("inline").find("level1").find("level2").find("block")
    annotate_explicit_block_elements(tree, annotations, lambda e: e is block)
    annotate_inline_descendants_as_inline(tree, annotations)
    assert annotations.annotation(block, TYPE_ANNOTATION_KEY) == ElementType.BLOCK
    # All ancestors should be inline
    level2 = tree.getroot().find("inline").find("level1").find("level2")
    level1 = tree.getroot().find("inline").find("level1")
    assert annotations.annotation(level2, TYPE_ANNOTATION_KEY) == ElementType.INLINE
    assert annotations.annotation(level1, TYPE_ANNOTATION_KEY) == ElementType.INLINE


def test_root_marked_inline_only_some_descendants_block():
    tree = parse("""
    <root>
        <child1/>
        <child2/>
        <!-- comment -->
        <?pi data?>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_inline_elements(tree, annotations, lambda e: e.tag == "root")
    child2 = tree.getroot().find("child2")
    comment = tree.getroot().getchildren()[2]
    annotate_explicit_block_elements(tree, annotations, lambda e: e is child2 or e is comment)
    annotate_inline_descendants_as_inline(tree, annotations)
    child1 = tree.getroot().find("child1")
    pi = tree.getroot().getchildren()[3]
    assert annotations.annotation(child1, TYPE_ANNOTATION_KEY) == ElementType.INLINE
    assert annotations.annotation(child2, TYPE_ANNOTATION_KEY) == ElementType.BLOCK
    assert annotations.annotation(comment, TYPE_ANNOTATION_KEY) == ElementType.BLOCK
    assert annotations.annotation(pi, TYPE_ANNOTATION_KEY) == ElementType.INLINE


def test_block_prevents_inline_propagation_to_its_children():
    tree = parse("""
    <root>
        <inline>
            <block>
                <child/>
                <!-- comment -->
                <?pi data?>
            </block>
        </inline>
    </root>
    """)
    annotations = Annotations()
    # Mark <inline> as inline
    annotate_explicit_inline_elements(tree, annotations, lambda e: e.tag == "inline")
    # Mark <block> as block
    block = tree.getroot().find("inline").find("block")
    annotate_explicit_block_elements(tree, annotations, lambda e: e is block)
    # Propagate inline to descendants
    annotate_inline_descendants_as_inline(tree, annotations)
    child = block.find("child")
    comment = block.getchildren()[1]
    pi = block.getchildren()[2]
    # Children of block should NOT be marked as inline
    assert annotations.annotation(child, TYPE_ANNOTATION_KEY) is None
    assert annotations.annotation(comment, TYPE_ANNOTATION_KEY) is None
    assert annotations.annotation(pi, TYPE_ANNOTATION_KEY) is None
    # Block itself remains block
    assert annotations.annotation(block, TYPE_ANNOTATION_KEY) == ElementType.BLOCK
