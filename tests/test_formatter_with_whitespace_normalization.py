from inspect import cleandoc

from helpers.predicates import is_block_or_root
from markuplift import DocumentFormatter


def test_normalize_text_whitespace():
    example = cleandoc("""
        <root>
            <block>Some text which
            contains newlines to support the fact that it has
            been wrapped.
            </block>
        </root>
    """)
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        normalize_whitespace_predicate=lambda e: e.tag == "block",
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block>Some text which contains newlines to support the fact that it has been wrapped. </block>
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
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        normalize_whitespace_predicate=lambda e: e.tag == "block",
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block>Some text<inline>with inline</inline> and tail text which contains newlines to support the fact that it has been wrapped. </block>
        </root>
    """)
    assert actual == expected


def test_preserving_whitespace_in_a_pre_element():
    example = """<root>
    <pre>
the wind of Fuji
I've brought on my fan
a gift from Edo
    </pre>
</root>"""
    formatter = DocumentFormatter(
        block_predicate=lambda e: e.tag in {"root", "pre"},
        preserve_whitespace_predicate=lambda e: e.tag == "pre",
    )
    actual = formatter.format_str(example)
    expected = """<root>
  <pre>
the wind of Fuji
I've brought on my fan
a gift from Edo
    </pre>
</root>"""
    assert actual == expected


def test_preserve_whitespace_in_a_pre_element_with_nested_elements():
    example = """<root>
    <pre>
the wind of Fuji
I've brought on my fan
<a href="https://example.com">a gift
from Edo</a>
    </pre>
</root>"""
    formatter = DocumentFormatter(
        block_predicate=lambda e: e.tag in {"root", "pre"},
        preserve_whitespace_predicate=lambda e: e.tag == "pre",
    )
    actual = formatter.format_str(example)
    expected = """<root>
  <pre>
the wind of Fuji
I've brought on my fan
<a href="https://example.com">a gift
from Edo</a>
    </pre>
</root>"""
    assert actual == expected


def test_xml_space_preserve_overrides_normalization():
    """Test that xml:space='preserve' takes priority over normalize_whitespace_predicate."""
    example = cleandoc("""
        <root>
            <normalized>Text with    extra   spaces
            and newlines</normalized>
            <preserved xml:space="preserve">Text with    extra   spaces
            and newlines</preserved>
        </root>
    """)

    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        normalize_whitespace_predicate=lambda e: e.tag in ("normalized", "preserved"),
    )

    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <normalized>Text with extra spaces and newlines</normalized>
          <preserved xml:space="preserve">Text with    extra   spaces
            and newlines</preserved>
        </root>
    """)
    assert actual == expected


def test_xml_space_default_allows_normalization():
    """Test that xml:space='default' allows normalization to proceed."""
    example = cleandoc("""
        <root>
            <container xml:space="preserve">
                <child xml:space="default">Text with    extra   spaces
                and newlines</child>
            </container>
        </root>
    """)

    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        normalize_whitespace_predicate=lambda e: e.tag == "child",
    )

    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <container xml:space="preserve">
                <child xml:space="default">Text with extra spaces and newlines</child>
            </container>
        </root>
    """)
    assert actual == expected


def test_character_entities_normalized():
    """Test that character entities resolving to whitespace are normalized."""
    example = cleandoc("""
        <root>
            <p>Text&#32;with&#9;character&#10;entities</p>
        </root>
    """)

    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        normalize_whitespace_predicate=lambda e: e.tag == "p",
    )

    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <p>Text with character entities</p>
        </root>
    """)
    assert actual == expected


def test_leading_trailing_whitespace_preservation():
    """Test that leading and trailing whitespace in text nodes is preserved for semantic significance."""
    example = cleandoc("""
        <root>
            <p>   Text with    internal   spaces   </p>
        </root>
    """)

    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        normalize_whitespace_predicate=lambda e: e.tag == "p",
    )

    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <p> Text with internal spaces </p>
        </root>
    """)
    assert actual == expected


def test_explicit_inline_with_normalization():
    """Test that explicit inline elements preserve spatial relationships with normalized characters."""
    example = cleandoc("""
        <root>
            <div>    Text with    extra spaces
            <em>   emphasized   text   </em>
            more    text    here</div>
        </root>
    """)

    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        inline_predicate=lambda e: e.tag == "em",
        strip_whitespace_predicate=lambda e: e.tag == "div",
    )

    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <div>Text with extra spaces <em>   emphasized   text   </em> more text here</div>
        </root>
    """)
    assert actual == expected


def test_normalization_with_mixed_element_scenario():
    """Test normalization in Mixed Element scenario with both explicit block and inline elements."""
    example = cleandoc("""
        <root>
            <container>    Text with    extra spaces
                <block>Block    content    here</block>
                <inline>Inline    content</inline>
                More    text</container>
        </root>
    """)

    formatter = DocumentFormatter(
        block_predicate=lambda e: e.tag in ("root", "block"),
        inline_predicate=lambda e: e.tag == "inline",
        normalize_whitespace_predicate=lambda e: e.tag == "container",
    )

    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <container> Text with extra spaces
            <block>Block    content    here</block>
         <inline>Inline    content</inline> More text</container>
        </root>
    """)
    assert actual == expected


def test_whitespace_only_text_nodes():
    """Test that whitespace-only text nodes are replaced with single space."""
    example = cleandoc("""
        <root>
            <p>Text<span>content</span>


            <span>more</span>end</p>
        </root>
    """)

    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        normalize_whitespace_predicate=lambda e: e.tag == "p",
    )

    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <p>Text<span>content</span> <span>more</span>end</p>
        </root>
    """)
    assert actual == expected
