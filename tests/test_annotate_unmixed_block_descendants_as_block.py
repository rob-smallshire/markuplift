from io import StringIO
from lxml import etree
from markuplift.annotation import (
    TYPE_ANNOTATION_KEY, BLOCK_TYPE_ANNOTATION, INLINE_TYPE_ANNOTATION,
    Annotations,
    annotate_explicit_block_elements,
    annotate_explicit_inline_elements,
    annotate_unmixed_block_descendants_as_block,
)

def parse(xml):
    return etree.parse(StringIO(xml))

def test_basic_propagation_element_only():
    tree = parse("""
    <root>
        <block>
            <child1/>
            <child2/>
        </block>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_block_elements(tree, annotations, lambda e: e.tag == "block")
    annotate_unmixed_block_descendants_as_block(tree, annotations)
    block = tree.getroot().find("block")
    child1 = block.find("child1")
    child2 = block.find("child2")
    assert annotations.annotation(child1, TYPE_ANNOTATION_KEY) == BLOCK_TYPE_ANNOTATION
    assert annotations.annotation(child2, TYPE_ANNOTATION_KEY) == BLOCK_TYPE_ANNOTATION


def test_mixed_content_prevents_block_annotation():
    tree = parse("""
    <root>
        <block>
            Text<child1/>Text<child2/>
        </block>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_block_elements(tree, annotations, lambda e: e.tag == "block")
    annotate_unmixed_block_descendants_as_block(tree, annotations)
    block = tree.getroot().find("block")
    child1 = block.find("child1")
    child2 = block.find("child2")
    assert annotations.annotation(child1, TYPE_ANNOTATION_KEY) is None
    assert annotations.annotation(child2, TYPE_ANNOTATION_KEY) is None

def test_whitespace_only_text_is_element_only():
    tree = parse("""
    <root>
        <block>
            \n   <child1/>   \n   <child2/>   \n
        </block>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_block_elements(tree, annotations, lambda e: e.tag == "block")
    annotate_unmixed_block_descendants_as_block(tree, annotations)
    block = tree.getroot().find("block")
    child1 = block.find("child1")
    child2 = block.find("child2")
    assert annotations.annotation(child1, TYPE_ANNOTATION_KEY) == BLOCK_TYPE_ANNOTATION
    assert annotations.annotation(child2, TYPE_ANNOTATION_KEY) == BLOCK_TYPE_ANNOTATION

def test_deeply_nested_with_mixed_content():
    tree = parse("""
    <root>
        <block>
            <level1>
                <level2>
                    Text<child/>
                </level2>
            </level1>
        </block>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_block_elements(tree, annotations, lambda e: e.tag == "block")
    annotate_unmixed_block_descendants_as_block(tree, annotations)
    block = tree.getroot().find("block")
    level1 = block.find("level1")
    level2 = level1.find("level2")
    child = level2.find("child")
    # level2 should be marked as a block since it is element-only content within its parent.
    # The presence of mixed content within it does not affect its block/inline status.
    assert annotations.annotation(level2, TYPE_ANNOTATION_KEY) == BLOCK_TYPE_ANNOTATION
    # child should NOT be marked as block due to mixed content
    assert annotations.annotation(child, TYPE_ANNOTATION_KEY) is None
    # level1 is element-only, so should be a block
    assert annotations.annotation(level1, TYPE_ANNOTATION_KEY) == BLOCK_TYPE_ANNOTATION

def test_comments_and_pis_element_only():
    tree = parse("""
    <root>
        <block>
            <child/>
            <!-- comment -->
            <?pi data?>
        </block>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_block_elements(tree, annotations, lambda e: e.tag == "block")
    annotate_unmixed_block_descendants_as_block(tree, annotations)
    block = tree.getroot().find("block")
    child = block.find("child")
    comment = block.getchildren()[1]
    pi = block.getchildren()[2]
    assert annotations.annotation(child, TYPE_ANNOTATION_KEY) == BLOCK_TYPE_ANNOTATION
    assert annotations.annotation(comment, TYPE_ANNOTATION_KEY) == BLOCK_TYPE_ANNOTATION
    assert annotations.annotation(pi, TYPE_ANNOTATION_KEY) == BLOCK_TYPE_ANNOTATION

def test_comments_and_pis_mixed_content():
    tree = parse("""
    <root>
        <block>
            Text<!-- comment -->Text<?pi data?>Text<child/>
        </block>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_block_elements(tree, annotations, lambda e: e.tag == "block")
    annotate_unmixed_block_descendants_as_block(tree, annotations)
    block = tree.getroot().find("block")
    child = block.find("child")
    comment = block.getchildren()[1]
    pi = block.getchildren()[2]
    assert annotations.annotation(child, TYPE_ANNOTATION_KEY) is None
    assert annotations.annotation(comment, TYPE_ANNOTATION_KEY) is None
    assert annotations.annotation(pi, TYPE_ANNOTATION_KEY) is None

def test_block_with_no_children():
    tree = parse("""
    <root>
        <block/>
    </root>
    """)
    annotations = Annotations()
    annotate_explicit_block_elements(tree, annotations, lambda e: e.tag == "block")
    annotate_unmixed_block_descendants_as_block(tree, annotations)
    block = tree.getroot().find("block")
    assert annotations.annotation(block, TYPE_ANNOTATION_KEY) == BLOCK_TYPE_ANNOTATION

