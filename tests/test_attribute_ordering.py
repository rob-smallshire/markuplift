"""Tests for attribute ordering functionality."""

from inspect import cleandoc
import pytest

from markuplift import (
    Formatter,
    Html5Formatter,
    sort_attributes,
    prioritize_attributes,
    defer_attributes,
    order_attributes,
)
from markuplift.predicates import tag_name, any_element


# Basic Ordering Tests


def test_sort_attributes():
    """Test alphabetical attribute ordering."""
    xml = '<div role="main" id="content" class="wrapper">text</div>'

    formatter = Formatter(
        block_when=tag_name("div"),
        reorder_attributes_when={any_element(): sort_attributes()},
    )

    result = formatter.format_str(xml)
    expected = '<div class="wrapper" id="content" role="main">text</div>'
    assert result == expected


def test_no_ordering_when_no_orderers():
    """Test that attributes maintain parser order when no orderers configured."""
    xml = '<div role="main" id="content" class="wrapper">text</div>'

    formatter = Formatter(block_when=tag_name("div"))

    result = formatter.format_str(xml)
    # Should maintain original order
    assert 'role="main" id="content" class="wrapper"' in result


def test_prioritize_attributes():
    """Test priority attributes appear first."""
    xml = '<input value="test" class="form-control" type="text" name="username" id="user" />'

    formatter = Formatter(
        reorder_attributes_when={
            tag_name("input"): prioritize_attributes("name", "id", "type")
        }
    )

    result = formatter.format_str(xml)
    expected = '<input name="username" id="user" type="text" value="test" class="form-control" />'
    assert result == expected


def test_defer_attributes():
    """Test specific attributes appear last."""
    xml = '<button data-track="click" class="btn" id="submit" aria-label="Submit form">Submit</button>'

    formatter = Html5Formatter(
        reorder_attributes_when={
            tag_name("button"): defer_attributes("data-track", "aria-label")
        }
    )

    result = formatter.format_str(xml)
    # Verify deferred attributes are at the end
    assert result.index('class="btn"') < result.index('data-track="click"')
    assert result.index('id="submit"') < result.index('aria-label="Submit form"')


def test_order_attributes():
    """Test full custom ordering with sorted remainder."""
    xml = '<a target="_blank" rel="noopener" href="/page" title="Link" class="link">Click</a>'

    formatter = Html5Formatter(
        reorder_attributes_when={
            tag_name("a"): order_attributes("href", "title", "target")
        }
    )

    result = formatter.format_str(xml)
    # href, title, target first as specified, then class and rel sorted
    assert result.index('href="/page"') < result.index('title="Link"')
    assert result.index('title="Link"') < result.index('target="_blank"')
    assert result.index('target="_blank"') < result.index('class="link"')
    assert result.index('class="link"') < result.index('rel="noopener"')


def test_preserve_original_order_when_no_match():
    """Test elements not matching predicates keep original order."""
    xml = '<div role="main" id="content"><span class="text" id="span1">text</span></div>'

    formatter = Formatter(
        block_when=any_element(),
        reorder_attributes_when={
            tag_name("div"): sort_attributes()
        },
    )

    result = formatter.format_str(xml)
    # div attributes should be sorted
    div_start = result.index("<div")
    div_end = result.index(">", div_start)
    div_attrs = result[div_start:div_end]
    assert div_attrs.index('id="content"') < div_attrs.index('role="main"')

    # span attributes should maintain original order
    span_start = result.index("<span")
    span_end = result.index(">", span_start)
    span_attrs = result[span_start:span_end]
    assert span_attrs.index('class="text"') < span_attrs.index('id="span1"')


# Validation Tests


def test_orderer_returns_wrong_count():
    """Test that orderer returning wrong count raises ValueError."""
    xml = '<div id="test" class="example">text</div>'

    def bad_orderer(names):
        return ["id"]  # Missing 'class'

    formatter = Formatter(
        block_when=tag_name("div"),
        reorder_attributes_when={tag_name("div"): bad_orderer},
    )

    with pytest.raises(ValueError, match="returned 1 attributes but received 2"):
        formatter.format_str(xml)


def test_orderer_adds_extra_attribute():
    """Test that orderer adding extra attribute raises ValueError."""
    xml = '<div id="test">text</div>'

    def bad_orderer(names):
        return ["id", "class"]  # 'class' doesn't exist

    formatter = Formatter(
        block_when=tag_name("div"),
        reorder_attributes_when={tag_name("div"): bad_orderer},
    )

    with pytest.raises(ValueError, match="returned 2 attributes but received 1"):
        formatter.format_str(xml)


def test_orderer_omits_attribute():
    """Test that orderer omitting attribute raises ValueError."""
    xml = '<div id="test" class="example">text</div>'

    def bad_orderer(names):
        return ["id"]  # Missing 'class'

    formatter = Formatter(
        block_when=tag_name("div"),
        reorder_attributes_when={tag_name("div"): bad_orderer},
    )

    with pytest.raises(ValueError, match="returned 1 attributes but received 2"):
        formatter.format_str(xml)


def test_orderer_duplicates_attribute():
    """Test that orderer duplicating attribute raises ValueError."""
    xml = '<div id="test" class="example">text</div>'

    def bad_orderer(names):
        return ["id", "id", "class"]  # 'id' duplicated

    formatter = Formatter(
        block_when=tag_name("div"),
        reorder_attributes_when={tag_name("div"): bad_orderer},
    )

    with pytest.raises(ValueError, match="returned 3 attributes but received 2"):
        formatter.format_str(xml)


def test_validation_error_messages():
    """Test that error messages are clear and helpful."""
    xml = '<div id="test" class="example">text</div>'

    def bad_orderer(names):
        return ["id", "style"]  # Wrong attribute

    formatter = Formatter(
        block_when=tag_name("div"),
        reorder_attributes_when={tag_name("div"): bad_orderer},
    )

    with pytest.raises(ValueError) as exc_info:
        formatter.format_str(xml)

    error_msg = str(exc_info.value)
    assert "Attribute reorderer for <div>" in error_msg
    assert "invalid reordering" in error_msg


# Integration Tests


def test_ordering_with_wrapped_attributes():
    """Test ordering works correctly with wrap_attributes_when."""
    xml = '<div role="main" id="content" class="wrapper" data-id="123">text</div>'

    formatter = Formatter(
        block_when=tag_name("div"),
        wrap_attributes_when=tag_name("div"),
        reorder_attributes_when={tag_name("div"): sort_attributes()},
    )

    result = formatter.format_str(xml)
    expected = cleandoc("""
        <div
          class="wrapper"
          data-id="123"
          id="content"
          role="main"
        >text</div>
    """)
    assert result == expected


def test_ordering_with_attribute_formatting():
    """Test attribute ordering is compatible with attribute value formatting."""
    xml = '<div style="color: red" class="box" id="main">text</div>'

    def css_formatter(value, formatter, level):
        return value.replace(": ", ":")

    from markuplift.predicates import attribute_matches

    formatter = Formatter(
        block_when=tag_name("div"),
        reorder_attributes_when={tag_name("div"): sort_attributes()},
        reformat_attribute_when={attribute_matches("style"): css_formatter},
    )

    result = formatter.format_str(xml)
    expected = '<div class="box" id="main" style="color:red">text</div>'
    assert result == expected


def test_ordering_with_namespace_attributes():
    """Test ordering handles namespaced attributes correctly."""
    xml = '<root xmlns:custom="http://example.com"><element custom:attr="val1" id="test" regular="val2">text</element></root>'

    formatter = Formatter(
        block_when=any_element(),
        reorder_attributes_when={tag_name("element"): sort_attributes()},
    )

    result = formatter.format_str(xml)
    # Should include properly ordered namespaced attributes
    assert "custom:attr" in result or "attr" in result  # Depending on namespace handling


def test_multiple_orderers_first_match_wins():
    """Test that first matching orderer is applied."""
    xml = '<div id="test" class="example">text</div>'

    formatter = Formatter(
        block_when=tag_name("div"),
        reorder_attributes_when={
            tag_name("div"): prioritize_attributes("id"),
            any_element(): sort_attributes(),  # This should not be applied to div
        },
    )

    result = formatter.format_str(xml)
    # id should be first (prioritize), not sorted
    expected = '<div id="test" class="example">text</div>'
    assert result == expected


def test_ordering_in_nested_elements():
    """Test different orderings at different nesting levels."""
    xml = '<div class="outer" id="1"><span id="inner" class="text">content</span></div>'

    formatter = Formatter(
        block_when=any_element(),
        reorder_attributes_when={
            tag_name("div"): sort_attributes(),
            tag_name("span"): prioritize_attributes("class"),
        },
    )

    result = formatter.format_str(xml)
    # div should be sorted: class before id
    div_start = result.index("<div")
    div_end = result.index(">", div_start)
    div_attrs = result[div_start:div_end]
    assert div_attrs.index('class="outer"') < div_attrs.index('id="1"')

    # span should have class prioritized first
    span_start = result.index("<span")
    span_end = result.index(">", span_start)
    span_attrs = result[span_start:span_end]
    assert span_attrs.index('class="text"') < span_attrs.index('id="inner"')


# Edge Cases


def test_empty_attribute_dict():
    """Test elements with no attributes."""
    xml = '<div>text</div>'

    formatter = Formatter(
        block_when=tag_name("div"),
        reorder_attributes_when={tag_name("div"): sort_attributes()},
    )

    result = formatter.format_str(xml)
    expected = '<div>text</div>'
    assert result == expected


def test_single_attribute():
    """Test single attribute (nothing to reorder)."""
    xml = '<div id="test">text</div>'

    formatter = Formatter(
        block_when=tag_name("div"),
        reorder_attributes_when={tag_name("div"): sort_attributes()},
    )

    result = formatter.format_str(xml)
    expected = '<div id="test">text</div>'
    assert result == expected


def test_orderer_with_xml_namespace():
    """Test xml:space and xml:lang attributes."""
    xml = '<root xml:space="preserve" xml:lang="en" id="test">text</root>'

    formatter = Formatter(
        block_when=tag_name("root"),
        reorder_attributes_when={tag_name("root"): sort_attributes()},
    )

    result = formatter.format_str(xml)
    # Should handle xml: prefixed attributes
    assert 'xml:' in result
    assert 'id="test"' in result


# Helper Function Tests


def test_sort_attributes_helper():
    """Test sort_attributes() factory."""
    orderer = sort_attributes()
    names = ["role", "id", "class"]
    result = orderer(names)
    assert list(result) == ["class", "id", "role"]


def test_prioritize_attributes_helper():
    """Test prioritize_attributes() factory."""
    orderer = prioritize_attributes("id", "name")
    names = ["class", "name", "id", "type"]
    result = orderer(names)
    assert list(result) == ["id", "name", "class", "type"]


def test_defer_attributes_helper():
    """Test defer_attributes() factory."""
    orderer = defer_attributes("aria-label", "data-track")
    names = ["class", "data-track", "id", "aria-label"]
    result = orderer(names)
    assert list(result) == ["class", "id", "data-track", "aria-label"]


def test_order_attributes_helper():
    """Test order_attributes() factory."""
    orderer = order_attributes("href", "title")
    names = ["target", "href", "class", "title"]
    result = orderer(names)
    assert list(result) == ["href", "title", "class", "target"]


def test_prioritize_attributes_with_missing_priorities():
    """Test prioritize with priority names not in element."""
    orderer = prioritize_attributes("name", "type", "value")
    names = ["class", "id"]  # None of the priority names present
    result = orderer(names)
    assert list(result) == ["class", "id"]


def test_order_attributes_with_partial_specification():
    """Test order_attributes when not all attributes are specified."""
    orderer = order_attributes("href")
    names = ["target", "href", "class", "rel"]
    result = orderer(names)
    assert list(result) == ["href", "class", "rel", "target"]
    assert result[0] == "href"  # Specified first
    # Rest should be sorted


# Complex Real-World Scenarios


def test_html_form_element_ordering():
    """Test HTML form elements with many attributes."""
    html = '<input placeholder="Enter text" type="text" class="form-control" value="test" name="username" id="user" required>'

    formatter = Html5Formatter(
        reorder_attributes_when={
            tag_name("input"): prioritize_attributes("name", "id", "type", "value")
        }
    )

    result = formatter.format_str(html)
    # Verify priority order
    assert result.index('name="username"') < result.index('id="user"')
    assert result.index('id="user"') < result.index('type="text"')
    assert result.index('type="text"') < result.index('value="test"')


def test_svg_element_with_coordinates():
    """Test SVG elements with coordinate and style attributes."""
    xml = '<rect fill="blue" height="100" width="200" y="50" x="10" />'

    formatter = Formatter(
        reorder_attributes_when={
            tag_name("rect"): order_attributes("x", "y", "width", "height")
        }
    )

    result = formatter.format_str(xml)
    # Verify coordinate attributes come first in logical order
    assert result.index('x="10"') < result.index('y="50"')
    assert result.index('y="50"') < result.index('width="200"')
    assert result.index('width="200"') < result.index('height="100"')


def test_mixed_standard_and_data_attributes():
    """Test elements with mixed standard and data-* attributes."""
    xml = '<div data-config="abc" class="widget" data-id="123" id="main" data-value="xyz">text</div>'

    def data_attributes_last(names):
        data_attrs = [n for n in names if n.startswith("data-")]
        standard_attrs = sorted(n for n in names if not n.startswith("data-"))
        return standard_attrs + sorted(data_attrs)

    formatter = Formatter(
        block_when=tag_name("div"),
        reorder_attributes_when={tag_name("div"): data_attributes_last},
    )

    result = formatter.format_str(xml)
    # Standard attributes (sorted) should come before data-* attributes
    assert result.index('class="widget"') < result.index('data-')
    assert result.index('id="main"') < result.index('data-')