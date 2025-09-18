from inspect import cleandoc

from helpers.predicates import is_block_or_root
from markuplift import Formatter


def test_element_with_no_attributes():
    example = cleandoc("""
        <root>
            <block>Some text</block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block>Some text</block>
        </root>
    """)
    assert actual == expected


def test_element_with_single_attribute():
    example = cleandoc("""
        <root>
            <block id="b1">Some text</block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block id="b1">Some text</block>
        </root>
    """)
    assert actual == expected


def test_element_with_multiple_attributes():
    example = cleandoc("""
        <root>
            <block id="b1" class="important">Some text</block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block id="b1" class="important">Some text</block>
        </root>
    """)
    assert actual == expected


def test_element_with_attributes_with_values_requiring_escaping():
    example = cleandoc("""
        <root>
            <block title="This &amp; That &lt;Example&gt;">Some text</block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block title="This &amp; That &lt;Example&gt;">Some text</block>
        </root>
    """)
    assert actual == expected


def test_element_with_attribute_containing_single_quote():
    example = cleandoc("""
        <root>
            <block data-info="It's a test">Some text</block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block data-info="It's a test">Some text</block>
        </root>
    """)
    assert actual == expected


def test_element_with_attribute_containing_double_quote():
    example = cleandoc("""
        <root>
            <block data-info='He said "Hello"'>Some text</block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block data-info='He said "Hello"'>Some text</block>
        </root>
    """)
    assert actual == expected


def test_element_with_attribute_containing_both_quotes():
    example = cleandoc("""
        <root>
            <block data-info='He said "It&apos;s a test"'>Some text</block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block data-info="He said &quot;It's a test&quot;">Some text</block>
        </root>
    """)
    assert actual == expected


def test_wrap_attributes_with_one_extra_indent():
    example = cleandoc("""
        <root>
            <block id="b1" class="important" data-info="He said &quot;It's a test&quot;">Some text</block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
        wrap_attributes_predicate=is_block_or_root,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block
            id="b1"
            class="important"
            data-info="He said &quot;It's a test&quot;"
          >Some text</block>
        </root>
    """)
    assert actual == expected


def test_wrap_attributes_with_one_extra_indent_with_nested_blocks():
    example = cleandoc("""
        <root>
            <block id="b1" class="important">
                <block id="b2" class="sub-important">Some text</block>
            </block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
        wrap_attributes_predicate=is_block_or_root,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block
            id="b1"
            class="important"
          >
            <block
              id="b2"
              class="sub-important"
            >Some text</block>
          </block>
        </root>
    """)
    assert actual == expected