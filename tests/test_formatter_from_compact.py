from inspect import cleandoc

import markuplift
from markuplift.formatter import Formatter, is_block_or_root


def test_formatter_from_compact():
    example = cleandoc("""
        <root><block><block>text</block></block></root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root
    )
    actual = formatter.format_doc(example)
    expected = cleandoc("""
        <root>
          <block>
            <block>text</block>
          </block>
        </root>
    """)
    assert actual == expected


def test_formatter_with_inline_from_compact():
    example = cleandoc("""
        <root><inline><inline>content</inline></inline></root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root
    )
    actual = formatter.format_doc(example)
    expected = cleandoc("""
        <root><inline><inline>content</inline></inline></root>
    """)
    assert actual == expected


def test_formatter_block_and_inline_from_compact():
    example = cleandoc("""
        <root><block><inline>text</inline></block></root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root
    )
    actual = formatter.format_doc(example)
    expected = cleandoc("""
        <root>
          <block><inline>text</inline></block>
        </root>
    """)
    assert actual == expected


def test_formatter_inline_and_block_from_compact():
    example = cleandoc("""
        <root><inline><block>text</block></inline></root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root
    )
    actual = formatter.format_doc(example)
    expected = cleandoc("""
        <root><inline><block>text</block></inline></root>
    """)
    assert actual == expected


def test_formatter_mixed_from_compact():
    example = cleandoc("""
        <root><block>before inline <inline>inline content</inline> after inline</block></root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root
    )
    actual = formatter.format_doc(example)
    expected = cleandoc("""
        <root>
          <block>before inline <inline>inline content</inline> after inline</block>
        </root>
    """)
    assert actual == expected


def test_formatter_mixed_multiple_from_compact():
    example = cleandoc("""
        <root><block>before inline <inline>inline content</inline> after inline <inline>more inline content</inline> end</block></root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root
    )
    actual = formatter.format_doc(example)
    expected = cleandoc("""
        <root>
          <block>before inline <inline>inline content</inline> after inline <inline>more inline content</inline> end</block>
        </root>
    """)
    assert actual == expected


def test_formatter_mixed_multiple_blocks_and_inlines_from_compact():
    example = cleandoc("""
        <root><block>before inline <inline>inline content</inline> after inline <inline>more inline content</inline> end</block><block>second block with <inline>inline content</inline></block></root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root
    )
    actual = formatter.format_doc(example)
    expected = cleandoc("""
        <root>
          <block>before inline <inline>inline content</inline> after inline <inline>more inline content</inline> end</block>
          <block>second block with <inline>inline content</inline></block>
        </root>
    """)
    assert actual == expected


def test_block_tail_text_suppresses_newline_indent_from_compact():
    example = cleandoc("""
        <root><block>first block</block>some tail text<block>second block</block></root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root
    )
    actual = formatter.format_doc(example)
    expected = cleandoc("""
        <root><block>first block</block>some tail text<block>second block</block></root>
    """)
    assert actual == expected


def test_inline_root_from_compact():
    example = cleandoc("""
        <inline>some inline content</inline>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root
    )
    actual = formatter.format_doc(example)
    expected = cleandoc("""
        <inline>some inline content</inline>
    """)
    assert actual == expected


