from inspect import cleandoc

from pytest import mark

from helpers.predicates import is_inline, is_block_or_root
from markuplift import DocumentFormatter


def test_formatter_from_indented():
    example = cleandoc("""
        <root>
            <block>
                <block>
                    text
                </block>
            </block>
        </root>
    """)
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block>
            <block>
                    text
                </block>
          </block>
        </root>
    """)
    assert actual == expected


def test_formatter_with_inline_from_indented():
    example = cleandoc("""
        <root>
            <inline><inline>content</inline></inline>
        </root>
    """)
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        inline_predicate=is_inline,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
            <inline><inline>content</inline></inline>
        </root>
    """)
    assert actual == expected


def test_formatter_block_and_inline_from_indented():
    example = cleandoc("""
        <root>
          <block>
            <inline>text</inline>
          </block>
        </root>
    """)
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block>
            <inline>text</inline>
          </block>
        </root>
    """)
    assert actual == expected


def test_formatter_inline_and_block_from_indented():
    example = cleandoc("""
        <root>
            <inline><block>text</block></inline>
        </root>
    """)
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        inline_predicate=is_inline,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
            <inline>
          <block>text</block>
          </inline>
        </root>
    """)
    assert actual == expected


def test_formatter_mixed_from_indented():
    example = cleandoc("""
        <root>
            <block>before inline <inline>inline content</inline> after inline</block>
        </root>
    """)
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block>before inline <inline>inline content</inline> after inline</block>
        </root>
    """)
    assert actual == expected


def test_formatter_mixed_multiple_from_indented():
    example = cleandoc("""
        <root>
            <block>before inline <inline>inline content</inline> after inline <inline>more inline content</inline> end</block>
        </root>
    """)
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block>before inline <inline>inline content</inline> after inline <inline>more inline content</inline> end</block>
        </root>
    """)
    assert actual == expected


def test_formatter_mixed_multiple_blocks_and_inlines_from_indented():
    example = cleandoc("""
        <root>
            <block>before inline <inline>inline content</inline> after inline <inline>more inline content</inline> end</block>
            <block>second block with <inline>inline content</inline></block>
        </root>
    """)
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block>before inline <inline>inline content</inline> after inline <inline>more inline content</inline> end</block>
          <block>second block with <inline>inline content</inline></block>
        </root>
    """)
    assert actual == expected


def test_block_tail_text():
    example = cleandoc("""
        <root>
            <block>first block</block>some text
            <block>second block</block>
        </root>
    """)
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        inline_predicate=is_inline,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block>first block</block>
        some text
          <block>second block</block>
        </root>
    """)
    assert actual == expected


def test_inline_root_from_indented():
    example = cleandoc("""
        <inline>some inline content</inline>
    """)
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <inline>some inline content</inline>
    """)
    assert actual == expected


