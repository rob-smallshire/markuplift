from inspect import cleandoc

from helpers.predicates import is_inline, is_block_or_root
from markuplift import DocumentFormatter


def test_self_closing_already_single_tag():
    example = cleandoc("""
        <root>
            <block>
                <selfclosing />
            </block>
        </root>
    """)
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        inline_predicate=lambda e: e.tag == "selfclosing",
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
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        inline_predicate=lambda e: e.tag == "selfclosing",
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
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        inline_predicate=lambda e: e.tag == "selfclosing",
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
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        inline_predicate=lambda e: e.tag == "selfclosing",
        strip_whitespace_predicate=lambda e: e.tag == "selfclosing",
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


def test_self_closing_implicit_block():
    example = cleandoc("""
            <root>
                <block>
                    <selfclosing></selfclosing>
                </block>
            </root>
        """)
    formatter = DocumentFormatter(
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