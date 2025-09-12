from inspect import cleandoc

from markuplift import Formatter
from markuplift.formatter import is_block_or_root


def test_comments_preserved():
    example = cleandoc("""
        <root>
            <block>
                <!-- This is a comment -->
                <inline>Text</inline>
                <!-- Another comment -->
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
                <!-- This is a comment -->
                <inline>Text</inline>
                <!-- Another comment -->
            </block>
        </root>
    """)
    assert actual == expected
