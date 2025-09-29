"""Tests for callable function matcher support in attribute predicates."""

import re
import pytest
from inspect import cleandoc

from markuplift import Formatter
from markuplift.predicates import attribute_matches, html_block_elements, tag_in, any_element


def test_function_matcher_with_attribute_matches():
    """Test that attribute_matches works with function matchers."""
    xml = '<div style="color: red; background: blue; margin: 10px; padding: 5px;">Test</div>'

    def complex_style_checker(value):
        """Check if style has 4+ CSS properties."""
        return value.count(";") >= 3

    def uppercase_formatter(value, formatter, level):
        return value.upper()

    formatter = Formatter(
        block_when=lambda root: lambda el: el.tag == "div",
        reformat_attribute_when={attribute_matches("style", complex_style_checker): uppercase_formatter},
    )

    result = formatter.format_str(xml)
    # Should format because style has 4 properties (3+ semicolons)
    assert 'style="COLOR: RED; BACKGROUND: BLUE; MARGIN: 10PX; PADDING: 5PX;"' in result


def test_function_matcher_with_chaining():
    """Test that function matchers work with chaining syntax."""
    xml = cleandoc("""
        <div>
            <p class="btn-primary widget" style="color: red;">Simple</p>
            <p class="btn-secondary" style="color: blue; background: white; margin: 5px;">Complex</p>
        </div>
    """)

    def has_multiple_classes(value):
        """Check if class attribute has multiple classes."""
        return len(value.split()) > 1

    def complex_style(value):
        """Check if style has multiple properties."""
        return value.count(";") >= 2

    def add_prefix(value, formatter, level):
        return f"formatted-{value}"

    formatter = Formatter(
        block_when=lambda root: lambda el: el.tag in ["div", "p"],
        reformat_attribute_when={
            # Chain element predicate with function matcher
            tag_in("p").with_attribute("class", has_multiple_classes): add_prefix,
            tag_in("p").with_attribute("style", complex_style): add_prefix,
        },
    )

    result = formatter.format_str(xml)

    # First p has multiple classes, should be formatted
    assert 'class="formatted-btn-primary widget"' in result

    # Second p has complex style, should be formatted
    assert 'style="formatted-color: blue; background: white; margin: 5px;"' in result


def test_function_matcher_error_handling():
    """Test that function matchers handle errors properly."""

    def bad_matcher_non_bool(value):
        """Returns non-boolean value."""
        return "not a boolean"

    def bad_matcher_exception(value):
        """Raises an exception."""
        raise ValueError("Something went wrong")

    from lxml import etree

    # Test non-boolean return (wrapped in RuntimeError)
    with pytest.raises(
        RuntimeError, match="Error in attribute_value matcher function: Matcher function must return bool"
    ):
        attribute_predicate_factory = attribute_matches("class", bad_matcher_non_bool)
        root = etree.Element("root")
        attribute_predicate = attribute_predicate_factory(root)  # Get the attribute predicate
        # This should fail when we try to use the matcher
        element = etree.Element("div")
        element.set("class", "test")
        attribute_predicate(element, "class", "test")

    # Test exception handling
    with pytest.raises(RuntimeError, match="Error in attribute_value matcher function"):
        attribute_predicate_factory = attribute_matches("class", bad_matcher_exception)
        root = etree.Element("root")
        attribute_predicate = attribute_predicate_factory(root)
        element = etree.Element("div")
        element.set("class", "test")
        attribute_predicate(element, "class", "test")


def test_function_matcher_with_lambda():
    """Test various lambda function matchers."""
    xml = cleandoc("""
        <div>
            <input type="text" class="form-control required" maxlength="50"/>
            <input type="password" class="form-control" maxlength="100"/>
            <textarea class="form-text" rows="5"></textarea>
        </div>
    """)

    def add_marker(value, formatter, level):
        return f"[MATCHED]{value}"

    formatter = Formatter(
        block_when=lambda root: lambda el: el.tag == "div",
        reformat_attribute_when={
            # Match classes containing "required"
            any_element().with_attribute("class", lambda v: "required" in v): add_marker,
            # Match maxlength > 75
            any_element().with_attribute("maxlength", lambda v: int(v) > 75): add_marker,
            # Match attribute names starting with "max"
            any_element().with_attribute(lambda n: n.startswith("max"), lambda v: True): add_marker,
        },
    )

    result = formatter.format_str(xml)

    # Should match first input's class (contains "required")
    assert 'class="[MATCHED]form-control required"' in result

    # Should match second input's maxlength (100 > 75)
    assert 'maxlength="[MATCHED]100"' in result


def test_function_matcher_css_semicolon_counting():
    """Test the specific CSS semicolon counting use case."""
    xml = cleandoc("""
        <div>
            <p style="color: red;">Simple</p>
            <p style="color: blue; background: white;">Medium</p>
            <p style="color: green; background: black; margin: 10px; padding: 5px;">Complex</p>
        </div>
    """)

    def css_multiline_formatter(value, formatter, level):
        """Format CSS as multiline."""
        properties = [prop.strip() for prop in value.split(";") if prop.strip()]
        base_indent = formatter.one_indent * level
        property_indent = formatter.one_indent * (level + 1)
        formatted_props = [f"{property_indent}{prop}" for prop in properties]
        return "\n" + ";\n".join(formatted_props) + "\n" + base_indent

    def has_many_css_properties(value, min_props=4):
        """Check if CSS has many properties."""
        return value.count(";") >= min_props - 1

    formatter = Formatter(
        block_when=lambda root: lambda el: el.tag in ["div", "p"],
        reformat_attribute_when={
            # Only format complex styles (4+ properties)
            html_block_elements().with_attribute(
                "style", lambda v: has_many_css_properties(v, 4)
            ): css_multiline_formatter
        },
    )

    result = formatter.format_str(xml)

    # Simple and medium styles should remain inline
    assert 'style="color: red;"' in result
    assert 'style="color: blue; background: white;"' in result

    # Complex style should be multiline (contains encoded newlines)
    assert "&#10;" in result  # Contains encoded newlines (XML-strict)


def test_mixed_matcher_types():
    """Test mixing different matcher types in same formatter."""
    xml = cleandoc("""
        <div>
            <a href="https://example.com" class="btn-primary">Link 1</a>
            <a href="http://insecure.com" class="btn-secondary">Link 2</a>
            <span data-config="{'theme': 'dark'}" class="widget">Span</span>
        </div>
    """)

    def mark_formatted(value, formatter, level):
        return f"*{value}*"

    formatter = Formatter(
        block_when=lambda root: lambda el: el.tag == "div",
        reformat_attribute_when={
            # String matcher
            attribute_matches("href", "https://example.com"): mark_formatted,
            # Regex matcher
            attribute_matches("data-config", re.compile(r".*theme.*")): mark_formatted,
            # Function matcher
            attribute_matches("class", lambda v: v.startswith("btn")): mark_formatted,
        },
    )

    result = formatter.format_str(xml)

    # String match should work
    assert 'href="*https://example.com*"' in result

    # Regex match should work
    assert "data-config=\"*{'theme': 'dark'}*\"" in result

    # Function match should work
    assert 'class="*btn-primary*"' in result
    assert 'class="*btn-secondary*"' in result


def test_function_matcher_edge_cases():
    """Test edge cases for function matchers."""

    def always_true(value):
        return True

    def always_false(value):
        return False

    def empty_string_checker(value):
        return len(value) == 0

    xml = '<div class="" style="color: red;" data-empty="">Test</div>'

    def mark_matched(value, formatter, level):
        return f"[{value}]" if value else "[EMPTY]"

    formatter = Formatter(
        block_when=lambda root: lambda el: el.tag == "div",
        reformat_attribute_when={
            attribute_matches("class", empty_string_checker): mark_matched,
            attribute_matches("style", always_true): mark_matched,
            attribute_matches("data-empty", always_false): mark_matched,  # This won't match
        },
    )

    result = formatter.format_str(xml)

    # Empty class should match and be formatted
    assert 'class="[EMPTY]"' in result

    # Style should always match
    assert 'style="[color: red;]"' in result

    # data-empty should not match (always_false)
    assert 'data-empty=""' in result  # Unchanged


def test_function_matcher_type_validation():
    """Test that function matcher validates argument types properly."""

    # Test invalid type for name parameter
    with pytest.raises(TypeError, match="attribute_name must be str, re.Pattern, or callable"):
        attribute_matches(123, "value")

    # Test invalid type for value parameter
    with pytest.raises(TypeError, match="attribute_value must be str, re.Pattern, or callable, or None"):
        attribute_matches("name", 123)

    # Test valid function types work
    try:
        attribute_matches(lambda n: True, lambda v: True)
        attribute_matches("name", lambda v: True)
        attribute_matches(lambda n: True, "value")
    except TypeError:
        pytest.fail("Valid function types should not raise TypeError")


def test_backward_compatibility():
    """Test that existing string and regex matching still works."""
    xml = '<div class="btn-primary" style="color: red;" href="https://example.com">Test</div>'

    def mark_matched(value, formatter, level):
        return f"[{value}]"

    formatter = Formatter(
        block_when=lambda root: lambda el: el.tag == "div",
        reformat_attribute_when={
            # String matching (existing functionality)
            attribute_matches("class", "btn-primary"): mark_matched,
            # Regex matching (existing functionality)
            attribute_matches("href", re.compile(r"^https://")): mark_matched,
        },
    )

    result = formatter.format_str(xml)

    # Backward compatibility should work
    assert 'class="[btn-primary]"' in result
    assert 'href="[https://example.com]"' in result
