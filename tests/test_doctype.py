from inspect import cleandoc

from helpers.predicates import is_inline, is_block_or_root
from markuplift import Formatter


def test_no_doctype():
    example = cleandoc("""
        <root>
            <block><inline>Mixed content</inline></block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
        inline_predicate=is_inline,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block><inline>Mixed content</inline></block>
        </root>
    """)
    assert actual == expected


def test_with_doctype_from_string():
    example = "\n" + cleandoc("""
        <!DOCTYPE root>
        <root>
            <block><inline>Mixed content</inline></block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
        inline_predicate=is_inline,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <!DOCTYPE root>
        <root>
          <block><inline>Mixed content</inline></block>
        </root>
    """)
    assert actual == expected


def test_override_doctype():
    example = "\n" + cleandoc("""
        <!DOCTYPE root>
        <root>
            <block><inline>Mixed content</inline></block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
        inline_predicate=is_inline,
    )
    actual = formatter.format_str(
        example,
        doctype='<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">')
    expected = cleandoc("""
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        <root>
          <block><inline>Mixed content</inline></block>
        </root>
    """)
    assert actual == expected