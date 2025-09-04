from inspect import cleandoc

import markuplift

def test_formatter():
    example = cleandoc("""
        <root><block><block>text</block></block></root>
    """)
    actual = markuplift.format_doc(example)
    expected = cleandoc("""
        <root>
          <block>
            <block>text</block>
          </block>
        </root>
    """)
    assert actual == expected


def test_formatter_with_inline():
    example = cleandoc("""
        <root><inline><inline>content</inline></inline></root>
    """)
    actual = markuplift.format_doc(example)
    expected = cleandoc("""
        <root><inline><inline>content</inline></inline></root>
    """)
    assert actual == expected


def test_formatter_block_and_inline():
    example = cleandoc("""
        <root><block><inline>text</inline></block></root>
    """)
    actual = markuplift.format_doc(example)
    expected = cleandoc("""
        <root>
          <block><inline>text</inline></block>
        </root>
    """)
    assert actual == expected


def test_formatter_inline_and_block():
    example = cleandoc("""
        <root><inline><block>text</block></inline></root>
    """)
    actual = markuplift.format_doc(example)
    expected = cleandoc("""
        <root><inline>
          <block>text</block>
        </inline></root>
    """)
    assert actual == expected
