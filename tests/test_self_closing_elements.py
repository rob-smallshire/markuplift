from inspect import cleandoc

from markuplift import Formatter
from markuplift.formatter import is_block_or_root


def test_self_closing_already_single_tag():
    example = cleandoc("""
        <root>
            <block>
                <selfclosing />
            </block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block>
                <selfclosing />
            </block>
        </root>
    """)
    assert actual == expected


def test_self_closing_two_tags():
    example = cleandoc("""
        <root>
            <block>
                <selfclosing></selfclosing>
            </block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block>
                <selfclosing />
            </block>
        </root>
    """)
    assert actual == expected


def test_only_whitespace_in_tags():
    example = cleandoc("""
        <root>
            <block>
                <selfclosing>  </selfclosing>
            </block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block>
                <selfclosing>  </selfclosing>
            </block>
        </root>
    """)
    assert actual == expected


def test_only_whitespace_in_tags_with_whitespace_normalization():
    example = cleandoc("""
        <root>
            <block>
                <selfclosing>  </selfclosing>
            </block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
        normalize_whitespace_predicate=lambda e: e.tag == "selfclosing",
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block>
                <selfclosing />
            </block>
        </root>
    """)
    assert actual == expected


