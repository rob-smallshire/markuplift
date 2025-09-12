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
    actual = formatter.format_str(example)
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
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block>Some text<inline>with inline</inline> and tail text which contains newlines to support the fact that it has been wrapped.</block>
        </root>
    """)
    assert actual == expected


def test_preserving_whitespace_in_a_pre_element():
    example = (
"""<root>
    <pre>
the wind of Fuji
I've brought on my fan
a gift from Edo
    </pre>
</root>""")
    formatter = Formatter(
        block_predicate=lambda e: e.tag in {"root", "pre"},
        preserve_whitespace_predicate=lambda e: e.tag == "pre",
    )
    actual = formatter.format_str(example)
    expected = (
"""<root>
  <pre>
the wind of Fuji
I've brought on my fan
a gift from Edo
    </pre>
</root>""")
    assert actual == expected


def test_preserve_whitespace_in_a_pre_element_with_nested_elements():
    example = (
"""<root>
    <pre>
the wind of Fuji
I've brought on my fan
<a href="https://example.com">a gift
from Edo</a>
    </pre>
</root>""")
    formatter = Formatter(
        block_predicate=lambda e: e.tag in {"root", "pre"},
        preserve_whitespace_predicate=lambda e: e.tag == "pre",
    )
    actual = formatter.format_str(example)
    expected = (
"""<root>
  <pre>
the wind of Fuji
I've brought on my fan
<a href="https://example.com">a gift
from Edo</a>
    </pre>
</root>""")
    assert actual == expected