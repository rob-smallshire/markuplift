from inspect import cleandoc

from markuplift import Formatter
from markuplift.formatter import is_block_or_root


def test_no_processing_instructions():
    example = cleandoc("""
        <root>
            <block><inline>Mixed content</inline></block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block><inline>Mixed content</inline></block>
        </root>
    """)
    assert actual == expected


def test_add_xml_declaration():
    example = cleandoc("""
        <root>
            <block><inline>Mixed content</inline></block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
    )
    actual = formatter.format_str(
        example,
        xml_declaration=True,
    )
    expected = cleandoc("""
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <root>
          <block><inline>Mixed content</inline></block>
        </root>
    """)
    assert actual == expected


def test_xml_declaration_processing_instruction_preserved():
    example = cleandoc("""
        <root>
            <block><?php echo "Hello, World!"; ?><inline>Mixed content</inline></block>
        </root>
    """)
    formatter = Formatter(
        block_predicate=is_block_or_root,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block><?php echo "Hello, World!"; ?><inline>Mixed content</inline></block>
        </root>
    """)
    assert actual == expected