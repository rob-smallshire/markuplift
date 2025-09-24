from inspect import cleandoc

from pytest import mark

from helpers.predicates import is_inline, is_block_or_root
from markuplift import DocumentFormatter
from markuplift.utilities import tagname


def test_comments_with_block_siblings_only():
    """Comments interleaved with block elements should format as blocks."""
    example = cleandoc("""
        <root>
            <container>
                <!-- Comment before first block -->
                <block>Block content 1</block>
                <!-- Comment between blocks -->
                <block>Block content 2</block>
                <!-- Comment after last block -->
            </container>
        </root>
    """)
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        inline_predicate=is_inline,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <container>
            <!-- Comment before first block -->
            <block>Block content 1</block>
            <!-- Comment between blocks -->
            <block>Block content 2</block>
            <!-- Comment after last block -->
          </container>
        </root>
    """)
    assert actual == expected


def test_comments_with_mixed_inline_block_siblings():
    example = cleandoc("""
        <root>
            <container>
                <!-- Comment before mixed content -->
                <block>Block content</block>
                <inline>Inline text</inline>
                <!-- Comment in mixed content -->
            </container>
        </root>
    """)
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        inline_predicate=is_inline,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <container>
                <!-- Comment before mixed content -->
            <block>Block content</block>
                <inline>Inline text</inline>
                <!-- Comment in mixed content -->
            </container>
        </root>
    """)
    assert actual == expected


def test_comments_with_true_mixed_content():
    """Comments with actual text content and block elements should use hybrid formatting."""
    example = cleandoc("""
        <root>
            <container>
                <!-- Comment before text -->
                Some text content
                <block>Block element</block>
                More text
                <!-- Comment after text -->
              </container>
        </root>
    """)
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        inline_predicate=is_inline,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <container>
                <!-- Comment before text -->
                Some text content
            <block>Block element</block>
                More text
                <!-- Comment after text -->
              </container>
        </root>
    """)
    assert actual == expected


def test_hybrid_mixed_content_xhtml_list():
    """XHTML list with mixed content: inline elements flow, block elements get block formatting."""
    example = cleandoc("""
        <li>
            This is some text with <em>emphasis</em> and <strong>bold</strong>. <ul>
                <li>Nested list item 1</li>
                <li>Nested list item 2</li>
            </ul>
            More text after the nested list.</li>
    """)
    formatter = DocumentFormatter(
        block_predicate=lambda e: e.tag in ("ul", "li"),
        inline_predicate=lambda e: e.tag in ("em", "strong", "span"),
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <li>
            This is some text with <em>emphasis</em> and <strong>bold</strong>.
          <ul>
            <li>Nested list item 1</li>
            <li>Nested list item 2</li>
          </ul>
        More text after the nested list.</li>
    """)
    assert actual == expected


def test_processing_instructions_with_block_siblings():
    """Processing instructions interleaved with block elements should format as blocks."""
    example = cleandoc("""
        <root>
            <container>
                <?xml-stylesheet type="text/xsl" href="style.xsl"?>
                <block>Block content 1</block>
                <?processing instruction?>
                <block>Block content 2</block>
            </container>
        </root>
    """)
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        inline_predicate=is_inline,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <container>
            <?xml-stylesheet type="text/xsl" href="style.xsl"?>
            <block>Block content 1</block>
            <?processing instruction?>
            <block>Block content 2</block>
          </container>
        </root>
    """)
    assert actual == expected


def test_processing_instructions_with_mixed_content():
    """Processing instructions with inline elements should format as inline (mixed content)."""
    example = cleandoc("""
        <root>
            <container>
                <?php echo "Hello"; ?><inline>Inline text</inline>
                <?processing instruction?>
            </container>
        </root>
    """)
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        inline_predicate=is_inline,
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <container>
                <?php echo "Hello"; ?><inline>Inline text</inline>
                <?processing instruction?>
            </container>
        </root>
    """)
    assert actual == expected


def test_comments_preserved_with_whitespace_normalization():
    """Comments with inline siblings should format as inline"""
    example = cleandoc("""
        <root>
            <block>
                <!-- This is a comment -->
                <inline>Text</inline>
                <!-- Another comment -->
            </block>
        </root>
    """)
    formatter = DocumentFormatter(
        block_predicate=is_block_or_root,
        inline_predicate=is_inline,
        normalize_whitespace_predicate=lambda e: tagname(e) == "block"
    )
    actual = formatter.format_str(example)
    expected = cleandoc("""
        <root>
          <block> <!-- This is a comment --> <inline>Text</inline> <!-- Another comment --> </block>
        </root>
    """)
    assert actual == expected
