from io import StringIO
from lxml import etree
from markuplift.annotation import TYPE_ANNOTATION_KEY, Annotations, annotate_elements_in_mixed_content_as_inline
from markuplift.types import ElementType

def parse(xml):
    return etree.parse(StringIO(xml))

def test_no_mixed_content():
    tree = parse("""
    <root>
        <block/>
        <inline/>
        <!-- comment -->
        <?pi data?>
    </root>
    """)
    annotations = Annotations()
    annotate_elements_in_mixed_content_as_inline(tree, annotations)
    for elem in tree.getroot():
        assert annotations.annotation(elem, TYPE_ANNOTATION_KEY) is None

def test_mixed_content_with_text():
    tree = parse("""
    <root>
        Text before<block/>Text after<inline/> <!-- comment --> <?pi data?>
    </root>
    """)
    annotations = Annotations()
    annotate_elements_in_mixed_content_as_inline(tree, annotations)
    for elem in tree.getroot():
        assert annotations.annotation(elem, TYPE_ANNOTATION_KEY) == ElementType.INLINE

def test_mixed_content_with_whitespace_only():
    tree = parse("""
    <root>
        \n   <block/>   \n   <inline/> <!-- comment --> <?pi data?>
    </root>
    """)
    annotations = Annotations()
    annotate_elements_in_mixed_content_as_inline(tree, annotations)
    for elem in tree.getroot():
        assert annotations.annotation(elem, TYPE_ANNOTATION_KEY) is None

def test_mixed_content_with_some_block_annotated():
    tree = parse("""
    <root>
        Text<block/>Text<inline/> <!-- comment --> <?pi data?>
    </root>
    """)
    annotations = Annotations()
    block = tree.getroot().find("block")
    annotations.annotate(block, TYPE_ANNOTATION_KEY, ElementType.BLOCK)
    annotate_elements_in_mixed_content_as_inline(tree, annotations)
    # block remains block, others become inline
    assert annotations.annotation(block, TYPE_ANNOTATION_KEY) == ElementType.BLOCK
    for elem in tree.getroot():
        if elem is not block:
            assert annotations.annotation(elem, TYPE_ANNOTATION_KEY) == ElementType.INLINE

def test_mixed_content_with_comment_and_pi_annotated_block():
    tree = parse("""
    <root>
        Text<!-- comment -->Text<?pi data?>Text<block/>Text<inline/>
    </root>
    """)
    annotations = Annotations()
    comment = tree.getroot()[0]  # comment node
    pi = tree.getroot()[1]       # PI node
    block = tree.getroot()[2]    # block node
    annotations.annotate(comment, TYPE_ANNOTATION_KEY, ElementType.BLOCK)
    annotations.annotate(pi, TYPE_ANNOTATION_KEY, ElementType.BLOCK)
    annotate_elements_in_mixed_content_as_inline(tree, annotations)
    assert annotations.annotation(comment, TYPE_ANNOTATION_KEY) == ElementType.BLOCK
    assert annotations.annotation(pi, TYPE_ANNOTATION_KEY) == ElementType.BLOCK
    assert annotations.annotation(block, TYPE_ANNOTATION_KEY) == ElementType.INLINE
    assert annotations.annotation(tree.getroot()[3], TYPE_ANNOTATION_KEY) == ElementType.INLINE

def test_elements_interleaved_with_non_significant_text():
    tree = parse("""
    <root>
        \n   <em>Text</em>   <!-- comment -->\n<?pi data?>   \n
    </root>
    """)
    # Note the 'Text' inside <em> makes it mixed content is not a direct child of root, so <em>
    # doesn't count as being within mixed content
    annotations = Annotations()
    annotate_elements_in_mixed_content_as_inline(tree, annotations)
    # block is after whitespace, so not mixed; inline is after text, so mixed
    em = tree.getroot()[0]
    comment = tree.getroot()[1]
    pi = tree.getroot()[2]
    assert annotations.annotation(em, TYPE_ANNOTATION_KEY) == None
    assert annotations.annotation(comment, TYPE_ANNOTATION_KEY) == None
    assert annotations.annotation(pi, TYPE_ANNOTATION_KEY) == None


def test_elements_interleaved_with_significant_text():
    tree = parse("""
    <root>
        \n   <em>Text</em>Tail   <!-- comment -->\n<?pi data?>   \n
    </root>
    """)
    # Note the 'Text' inside <em> makes it mixed content is not a direct child of root, so <em>
    # doesn't count as being within mixed content, but the tail 'Tail' makes the <em> and its
    # siblings part of mixed content
    annotations = Annotations()
    annotate_elements_in_mixed_content_as_inline(tree, annotations)
    # block is after whitespace, so not mixed; inline is after text, so mixed
    em = tree.getroot()[0]
    comment = tree.getroot()[1]
    pi = tree.getroot()[2]
    assert annotations.annotation(em, TYPE_ANNOTATION_KEY) == ElementType.INLINE
    assert annotations.annotation(comment, TYPE_ANNOTATION_KEY) == ElementType.INLINE
    assert annotations.annotation(pi, TYPE_ANNOTATION_KEY) == ElementType.INLINE
