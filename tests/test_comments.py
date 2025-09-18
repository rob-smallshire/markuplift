from inspect import cleandoc

from pytest import mark

from helpers.predicates import is_inline, is_block_or_root
from markuplift import Formatter



@mark.skip(reason="Comments are not yet supported")
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
        inline_predicate=is_inline,
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
