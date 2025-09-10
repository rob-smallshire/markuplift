from inspect import cleandoc

from markuplift import Formatter
from markuplift.formatter import is_block_or_root


def test_element_with_simple_text_content():
    example = cleandoc("""
        <root>
            <block>Some text</block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
    )
    actual = formatter.format_doc(example)
    expected = cleandoc("""
        <root>
          <block>Some text</block>
        </root>
    """)
    assert actual == expected


def test_element_with_text_content_containing_angled_brackets():
    example = cleandoc("""
        <root>
            <block>Some text with &lt; and &gt; characters</block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
    )
    actual = formatter.format_doc(example)
    expected = cleandoc("""
        <root>
          <block>Some text with &lt; and &gt; characters</block>
        </root>
    """)
    assert actual == expected


def test_element_with_simple_tail_content():
    example = cleandoc("""
        <root>
            <block>Some text<inline>with inline</inline> and tail text</block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
    )
    actual = formatter.format_doc(example)
    expected = cleandoc("""
        <root>
          <block>Some text<inline>with inline</inline> and tail text</block>
        </root>
    """)
    assert actual == expected


def test_element_with_tail_content_containing_angled_brackets():
    example = cleandoc("""
        <root>
            <block>Some text<inline>with &lt;inline&gt;</inline> and tail text with &lt; and &gt; characters</block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
    )
    actual = formatter.format_doc(example)
    expected = cleandoc("""
        <root>
          <block>Some text<inline>with &lt;inline&gt;</inline> and tail text with &lt; and &gt; characters</block>
        </root>
    """)
    assert actual == expected