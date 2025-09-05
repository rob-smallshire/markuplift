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


def test_formatter_mixed():
    example = cleandoc("""
        <root><block>before inline <inline>inline content</inline> after inline</block></root>
    """)
    actual = markuplift.format_doc(example)
    expected = cleandoc("""
        <root>
          <block>before inline <inline>inline content</inline> after inline</block>
        </root>
    """)
    assert actual == expected


def test_formatter_mixed_multiple():
    example = cleandoc("""
        <root><block>before inline <inline>inline content</inline> after inline <inline>more inline content</inline> end</block></root>
    """)
    actual = markuplift.format_doc(example)
    expected = cleandoc("""
        <root>
          <block>before inline <inline>inline content</inline> after inline <inline>more inline content</inline> end</block>
        </root>
    """)
    assert actual == expected


def test_formatter_mixed_multiple_blocks_and_inlines():
    example = cleandoc("""
        <root><block>before inline <inline>inline content</inline> after inline <inline>more inline content</inline> end</block><block>second block with <inline>inline content</inline></block></root>
    """)
    actual = markuplift.format_doc(example)
    expected = cleandoc("""
        <root>
          <block>before inline <inline>inline content</inline> after inline <inline>more inline content</inline> end</block>
          <block>second block with <inline>inline content</inline></block>
        </root>
    """)
    assert actual == expected


def test_block_tail_text_suppresses_newline_indent():
    example = cleandoc("""
        <root><block>first block</block>some text<block>second block</block></root>
    """)
    actual = markuplift.format_doc(example)
    expected = cleandoc("""
        <root>
          <block>first block</block>some text<block>second block</block>
        </root>
    """)
    assert actual == expected


def test_inline_root():
    example = cleandoc("""
        <inline>some inline content</inline>
    """)
    actual = markuplift.format_doc(example)
    expected = cleandoc("""
        <inline>some inline content</inline>
    """)
    assert actual == expected