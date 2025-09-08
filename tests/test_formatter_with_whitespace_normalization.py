from inspect import cleandoc

from markuplift import Formatter
from markuplift.formatter import is_block_or_root


def test_normalize_text_whitespace():
    example = cleandoc("""
        <root>
            <block>Some text which
            contains newlines to support the fact that it has
            been wrapped.
            </block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
        normalize_whitespace_predicate=lambda e: e.tag == "block",
    )
    actual = formatter.format_doc(example)
    expected = cleandoc("""
        <root>
          <block>Some text which contains newlines to support the fact that it has been wrapped.</block>
        </root>
    """)
    assert actual == expected


def test_normalize_tail_whitespace():
    example = cleandoc("""
        <root>
            <block>Some text<inline>with inline</inline>
            and tail text which
            contains newlines to support the fact that it has
            been wrapped.
            </block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
        normalize_whitespace_predicate=lambda e: e.tag == "block",
    )
    actual = formatter.format_doc(example)
    expected = cleandoc("""
        <root>
          <block>Some text<inline>with inline</inline> and tail text which contains newlines to support the fact that it has been wrapped.</block>
        </root>
    """)
    assert actual == expected
