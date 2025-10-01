"""Tests for attribute value formatting functionality."""

import re
from inspect import cleandoc
from lxml import etree

from markuplift import (
    Formatter,
    Html5Formatter,
    wrap_css_properties,
    css_formatter,
    sort_css_properties,
    prioritize_css_properties,
    defer_css_properties,
    css_property_order,
    reorder_css_properties,
)
from markuplift.predicates import tag_name, has_class, attribute_matches, any_element, pattern


def _allowed_types_message(allow_none: bool = False) -> str:
    """Generate the expected error message for allowed types in _create_matcher.

    This matches the dynamic error message generation in predicates._create_matcher
    to avoid fragile hard-coded strings in tests.
    """
    allowed_types = [str.__name__, etree.QName.__name__, re.Pattern.__name__, "callable"]
    if allow_none:
        allowed_types.append("None")
    return ", ".join(allowed_types[:-1]) + ", or " + allowed_types[-1]


def test_basic_attribute_formatting():
    """Test basic attribute formatting with exact string matching."""
    xml = '<div style="color: red; background: blue;">content</div>'

    def css_formatter(value, formatter, level):
        # Add spaces around colons
        return value.replace(":", ": ")

    formatter = Formatter(
        block_when=tag_name("div"), reformat_attribute_when={attribute_matches("style"): css_formatter}
    )

    result = formatter.format_str(xml)
    expected = '<div style="color:  red; background:  blue;">content</div>'
    assert result == expected


def test_chainable_attribute_formatting():
    """Test attribute formatting with chainable predicates."""
    xml = '<div class="widget" style="margin:0;padding:5px;">content</div>'

    def css_formatter(value, formatter, level):
        return value.replace(";", "; ")

    formatter = Formatter(
        block_when=tag_name("div"), reformat_attribute_when={has_class("widget").with_attribute("style"): css_formatter}
    )

    result = formatter.format_str(xml)
    expected = '<div class="widget" style="margin:0; padding:5px; ">content</div>'
    assert result == expected


def test_regex_pattern_attribute_names():
    """Test attribute formatting with regex patterns for attribute names."""
    xml = """
    <div data-config="{'theme':'dark'}" data-options="{'animate':true}">content</div>
    """

    def json_formatter(value, formatter, level):
        # Add spaces after colons and commas
        return value.replace(":", ": ").replace(",", ", ")

    formatter = Formatter(
        block_when=tag_name("div"), reformat_attribute_when={attribute_matches(re.compile(r"data-.*")): json_formatter}
    )

    result = formatter.format_str(xml.strip())
    expected = "<div data-config=\"{'theme': 'dark'}\" data-options=\"{'animate': true}\">content</div>"
    assert result == expected


def test_regex_pattern_attribute_values():
    """Test attribute formatting with regex patterns for attribute values."""
    xml = """
    <div>
        <a href="styles.css">CSS link</a>
        <a href="script.js">JS link</a>
        <a href="page.html">HTML link</a>
    </div>
    """

    def css_link_formatter(value, formatter, level):
        return f"assets/css/{value}"

    formatter = Formatter(
        block_when=tag_name("div"),
        reformat_attribute_when={tag_name("a").with_attribute("href", re.compile(r".*\.css$")): css_link_formatter},
    )

    result = formatter.format_str(xml.strip())
    expected = cleandoc("""
        <div>
          <a href="assets/css/styles.css">CSS link</a>
          <a href="script.js">JS link</a>
          <a href="page.html">HTML link</a>
        </div>
    """)
    assert result == expected


def test_multiple_attribute_formatters():
    """Test multiple attribute formatters with first-match-wins behavior."""
    xml = '<div class="btn-primary" onclick="doSomething()">Button</div>'

    def class_formatter(value, formatter, level):
        return value.replace("-", "_")

    def js_formatter(value, formatter, level):
        return value.replace("()", "(event)")

    formatter = Formatter(
        block_when=tag_name("div"),
        reformat_attribute_when={
            attribute_matches("class"): class_formatter,
            attribute_matches("onclick"): js_formatter,
        },
    )

    result = formatter.format_str(xml)
    expected = '<div class="btn_primary" onclick="doSomething(event)">Button</div>'
    assert result == expected


def test_pattern_convenience_function():
    """Test the pattern() convenience function."""
    xml = '<link rel="stylesheet" href="main.css" type="text/css" />'

    def css_formatter(value, formatter, level):
        return f"optimized/{value}"

    formatter = Formatter(
        reformat_attribute_when={tag_name("link").with_attribute("href", pattern(r".*\.css$")): css_formatter}
    )

    result = formatter.format_str(xml)
    expected = '<link rel="stylesheet" href="optimized/main.css" type="text/css" />'
    assert result == expected


def test_any_element_with_attribute():
    """Test any_element() with attribute chaining."""
    xml = """
    <div style="color: red;">
        <span style="font-weight: bold;">
            <p style="margin: 0;">Text</p>
        </span>
    </div>
    """

    def css_formatter(value, formatter, level):
        return value.replace(": ", ":")

    formatter = Formatter(
        block_when=any_element(), reformat_attribute_when={any_element().with_attribute("style"): css_formatter}
    )

    result = formatter.format_str(xml.strip())
    expected = cleandoc("""
        <div style="color:red;">
          <span style="font-weight:bold;">
            <p style="margin:0;">Text</p>
          </span>
        </div>
    """)
    assert result == expected


def test_complex_chaining_scenario():
    """Test complex chaining with multiple predicates and formatters."""
    xml = """
    <article>
        <div class="code-block" data-language="javascript">
            <pre data-config='{"theme":"dark","lineNumbers":true}'>
                function test() { return true; }
            </pre>
        </div>
        <div class="text-block" style="margin-top: 1rem;">
            <p>Some text content</p>
        </div>
    </article>
    """

    def json_formatter(value, formatter, level):
        # Format JSON with proper spacing
        return value.replace(":", ": ").replace(",", ", ").replace('{"', '{ "').replace('"}', '" }')

    def css_formatter(value, formatter, level):
        # Ensure proper spacing in CSS
        return value.replace("-", " - ").replace(":", ": ")

    formatter = Formatter(
        block_when=any_element(),
        reformat_attribute_when={
            tag_name("pre").with_attribute("data-config", re.compile(r"^\{.*\}$")): json_formatter,
            has_class("text-block").with_attribute("style"): css_formatter,
        },
    )

    result = formatter.format_str(xml.strip())
    # JSON formatting should be applied to pre element's data-config
    # Note: XML escaping strategy uses smart quoting that avoids escaping when possible
    assert '{ "theme": "dark", "lineNumbers": true}' in result
    # CSS formatting should be applied to div's style
    assert "margin - top:  1rem" in result


def test_attribute_formatting_with_text_formatting():
    """Test that attribute formatting works alongside text formatting."""
    xml = '<code style="font-family: monospace;">function() { return true; }</code>'

    def css_formatter(value, formatter, level):
        return value.replace(": ", ":")

    def js_formatter(text, formatter, level):
        return text.replace("{ ", "{\n  ").replace(" }", "\n}")

    formatter = Formatter(
        block_when=tag_name("code"),
        reformat_attribute_when={attribute_matches("style"): css_formatter},
        reformat_text_when={tag_name("code"): js_formatter},
    )

    result = formatter.format_str(xml)
    expected = '<code style="font-family:monospace;">function() {\n  return true;\n}</code>'
    assert result == expected


def test_no_formatters_applied():
    """Test that attributes are unchanged when no formatters match."""
    xml = '<div title="test" class="example">content</div>'

    formatter = Formatter(
        block_when=tag_name("div"),
        reformat_attribute_when={attribute_matches("nonexistent"): lambda v, f, l: v.upper()},
    )

    result = formatter.format_str(xml)
    expected = '<div title="test" class="example">content</div>'
    assert result == expected


def test_first_match_wins():
    """Test that only the first matching formatter is applied."""
    xml = '<div class="test">content</div>'

    def formatter1(value, formatter, level):
        return f"FIRST_{value}"

    def formatter2(value, formatter, level):
        return f"SECOND_{value}"

    formatter = Formatter(
        block_when=tag_name("div"),
        reformat_attribute_when={
            attribute_matches("class"): formatter1,
            any_element().with_attribute("class"): formatter2,
        },
    )

    result = formatter.format_str(xml)
    expected = '<div class="FIRST_test">content</div>'
    assert result == expected


def test_empty_attribute_values():
    """Test formatting of empty attribute values."""
    xml = '<div class="" style="">content</div>'

    def non_empty_formatter(value, formatter, level):
        return "formatted" if not value else value.upper()

    formatter = Formatter(
        block_when=tag_name("div"),
        reformat_attribute_when={
            attribute_matches("class"): non_empty_formatter,
            attribute_matches("style"): non_empty_formatter,
        },
    )

    result = formatter.format_str(xml)
    expected = '<div class="formatted" style="formatted">content</div>'
    assert result == expected


def test_namespace_attributes():
    """Test attribute formatting with namespaced elements."""
    xml = """
    <root xmlns:custom="http://example.com">
        <custom:element custom:data="value" regular="attr">content</custom:element>
    </root>
    """

    def formatter(value, formatter, level):
        return value.upper()

    formatter_obj = Formatter(
        block_when=any_element(),
        reformat_attribute_when={
            # This will match both namespaced and regular attributes
            attribute_matches(re.compile(r".*data.*")): formatter,
        },
    )

    result = formatter_obj.format_str(xml.strip())
    # Should format the custom:data attribute (appears as just "data" after parsing)
    assert 'data="VALUE"' in result


def test_indentation_context_in_formatter():
    """Test that formatters receive correct indentation context."""
    xml = """
    <div>
        <nested>
            <deep style="margin: 0;">content</deep>
        </nested>
    </div>
    """

    def indent_aware_formatter(value, formatter, level):
        # Add indentation-based prefix
        prefix = "  " * level
        return f"{prefix}{value}"

    formatter_obj = Formatter(
        block_when=any_element(), reformat_attribute_when={attribute_matches("style"): indent_aware_formatter}
    )

    result = formatter_obj.format_str(xml.strip())
    # The deep element should be at indentation level 2, so style should have 4 spaces prefix
    assert 'style="    margin: 0;"' in result


def test_wrapped_attributes_indentation_context():
    """Test that attribute formatters receive correct indentation level when attributes are wrapped.

    When wrap_attributes_predicate is enabled, attributes are placed on separate lines with
    an additional level of indentation. Attribute formatters should receive this extra level
    so they can format multi-line content correctly.
    """
    html = '<div><button class="primary" style="color: red; background: blue; border: 1px solid black; padding: 10px;">Click me</button></div>'

    def multiline_css_formatter(value, formatter, level):
        """Format CSS properties on separate lines with proper indentation.

        The level parameter represents the indentation level of the attribute itself.
        CSS properties should be indented one level deeper than the attribute.
        """
        properties = [prop.strip() for prop in value.split(";") if prop.strip()]
        if len(properties) <= 2:
            # Keep short styles inline
            return value

        # CSS properties should be one level deeper than the attribute
        property_indent = formatter.one_indent * (level + 1)
        # Closing quote aligns with the attribute
        closing_indent = formatter.one_indent * level

        formatted_props = [f"\n{property_indent}{prop};" for prop in properties]
        return "".join(formatted_props) + f"\n{closing_indent}"

    formatter_obj = Html5Formatter(
        wrap_attributes_when=tag_name("button"),
        reformat_attribute_when={attribute_matches("style"): multiline_css_formatter},
    )

    result = formatter_obj.format_str(html.strip())
    # With wrapped attributes:
    # - button is at physical_level=1
    # - attributes get level=2 (physical_level + 1 for wrapping)
    # - CSS properties get level=3 (attribute level + 1), giving 6 spaces indentation
    expected = '<!DOCTYPE html>\n<div>\n  <button\n    class="primary"\n    style="\n      color: red;\n      background: blue;\n      border: 1px solid black;\n      padding: 10px;\n    "\n  >Click me</button>\n</div>\n'
    assert result == expected


def test_wrapped_attributes_with_single_line_css():
    """Test that short CSS styles remain inline even with wrapped attributes."""
    html = '<div><button class="btn" style="color: red;">Click</button></div>'

    def smart_css_formatter(value, formatter, level):
        """Only expand long CSS, keep short styles inline."""
        properties = [prop.strip() for prop in value.split(";") if prop.strip()]
        if len(properties) <= 2:
            return value

        property_indent = formatter.one_indent * (level + 1)
        closing_indent = formatter.one_indent * level
        formatted_props = [f"\n{property_indent}{prop};" for prop in properties]
        return "".join(formatted_props) + f"\n{closing_indent}"

    formatter_obj = Html5Formatter(
        wrap_attributes_when=tag_name("button"),
        reformat_attribute_when={attribute_matches("style"): smart_css_formatter},
    )

    result = formatter_obj.format_str(html.strip())
    expected = '<!DOCTYPE html>\n<div>\n  <button\n    class="btn"\n    style="color: red;"\n  >Click</button>\n</div>\n'
    assert result == expected


def test_deeply_nested_wrapped_attributes_indentation():
    """Test indentation context is correct for wrapped attributes at various nesting levels."""
    html = '<div><section><article><button style="a: 1; b: 2; c: 3; d: 4;">Deep button</button></article></section></div>'

    def multiline_css_formatter(value, formatter, level):
        properties = [prop.strip() for prop in value.split(";") if prop.strip()]
        if len(properties) <= 2:
            return value

        property_indent = formatter.one_indent * (level + 1)
        closing_indent = formatter.one_indent * level
        formatted_props = [f"\n{property_indent}{prop};" for prop in properties]
        return "".join(formatted_props) + f"\n{closing_indent}"

    formatter_obj = Html5Formatter(
        wrap_attributes_when=tag_name("button"),
        reformat_attribute_when={attribute_matches("style"): multiline_css_formatter},
    )

    result = formatter_obj.format_str(html.strip())
    # button is at physical_level=3, with wrapped attrs level=4, CSS properties at level=5 (10 spaces)
    expected = '<!DOCTYPE html>\n<div>\n  <section>\n    <article>\n      <button\n        style="\n          a: 1;\n          b: 2;\n          c: 3;\n          d: 4;\n        "\n      >Deep button</button>\n    </article>\n  </section>\n</div>\n'
    assert result == expected


def test_invalid_name_type_error():
    """Test that invalid name types raise TypeError."""
    import pytest
    from markuplift.predicates import attribute_matches

    allowed = _allowed_types_message(allow_none=False)
    with pytest.raises(TypeError, match=f"attribute_name must be {re.escape(allowed)}, got int"):
        attribute_matches(123)  # Invalid type

    with pytest.raises(TypeError, match="attribute_name cannot be None"):
        attribute_matches(None)  # None not allowed for name

    with pytest.raises(TypeError, match=f"attribute_name must be {re.escape(allowed)}, got list"):
        attribute_matches([])  # List not allowed


def test_invalid_value_type_error():
    """Test that invalid value types raise TypeError."""
    import pytest
    from markuplift.predicates import attribute_matches

    allowed_with_none = _allowed_types_message(allow_none=True)
    with pytest.raises(TypeError, match=f"attribute_value must be {re.escape(allowed_with_none)}, got int"):
        attribute_matches("class", 123)  # type: ignore[arg-type]  # Invalid type

    with pytest.raises(TypeError, match=f"attribute_value must be {re.escape(allowed_with_none)}, got list"):
        attribute_matches("class", [])  # type: ignore[arg-type]  # List not allowed


def test_empty_string_name_and_value():
    """Test handling of empty string names and values."""
    xml = '<div class="" data-empty="">content</div>'

    def formatter(value, formatter, level):
        return "EMPTY" if not value else f"NOT_EMPTY_{value}"

    formatter_obj = Formatter(
        block_when=tag_name("div"),
        reformat_attribute_when={
            attribute_matches(""): formatter,  # Empty string name
            attribute_matches("class", ""): formatter,  # Empty string value
        },
    )

    result = formatter_obj.format_str(xml)
    # Should not match empty string attribute name (no attributes have empty names)
    # Should match class="" because value is empty string
    assert 'class="EMPTY"' in result


def test_predicate_factory_with_attribute_error_cases():
    """Test error cases in PredicateFactory.with_attribute method."""
    import pytest
    from markuplift.predicates import tag_name

    allowed = _allowed_types_message(allow_none=False)
    allowed_with_none = _allowed_types_message(allow_none=True)

    with pytest.raises(TypeError, match=f"attribute_name must be {re.escape(allowed)}, got int"):
        tag_name("div").with_attribute(123)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match=f"attribute_value must be {re.escape(allowed_with_none)}, got int"):
        tag_name("div").with_attribute("class", 123)  # type: ignore[arg-type]


def test_regex_compilation_safety():
    """Test that regex patterns are handled safely."""
    import re
    from markuplift.predicates import attribute_matches, pattern

    # Test that pre-compiled patterns work
    compiled_pattern = re.compile(r"test.*")
    factory = attribute_matches(compiled_pattern)
    assert callable(factory)

    # Test pattern convenience function
    pattern_obj = pattern(r"test.*")
    assert isinstance(pattern_obj, re.Pattern)

    # Test invalid regex pattern (should be handled by re.compile)
    import pytest

    with pytest.raises(re.error):
        pattern("[invalid")  # Invalid regex


def test_chaining_with_invalid_types():
    """Test that chaining with invalid types raises appropriate errors."""
    import pytest
    from markuplift.predicates import has_class

    predicate_factory = has_class("test")
    allowed_with_none = _allowed_types_message(allow_none=True)

    with pytest.raises(TypeError, match="attribute_name cannot be None"):
        predicate_factory.with_attribute(None)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match=f"attribute_value must be {re.escape(allowed_with_none)}, got list"):
        predicate_factory.with_attribute("class", [])  # type: ignore[arg-type]


def test_type_safety_edge_cases():
    """Test various edge cases for type safety."""
    from markuplift.predicates import attribute_matches, any_element

    # Test that boolean values are rejected
    import pytest

    allowed = _allowed_types_message(allow_none=False)
    allowed_with_none = _allowed_types_message(allow_none=True)

    with pytest.raises(TypeError, match=f"attribute_name must be {re.escape(allowed)}, got bool"):
        attribute_matches(True)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match=f"attribute_value must be {re.escape(allowed_with_none)}, got bool"):
        attribute_matches("class", False)  # type: ignore[arg-type]

    # Test that dict/tuple values are rejected
    with pytest.raises(TypeError, match=f"attribute_name must be {re.escape(allowed)}, got dict"):
        attribute_matches({})  # type: ignore[arg-type]

    with pytest.raises(TypeError, match=f"attribute_value must be {re.escape(allowed_with_none)}, got tuple"):
        attribute_matches("class", ())  # type: ignore[arg-type]

    # Test any_element chaining with invalid types
    with pytest.raises(TypeError, match=f"attribute_name must be {re.escape(allowed)}, got float"):
        any_element().with_attribute(3.14)  # type: ignore[arg-type]  # Float not allowed



def test_wrap_css_properties_public_api():
    """Test the public API wrap_css_properties function."""
    html = '<div><button class="primary" style="color: red; background: blue; border: 1px solid black; padding: 10px;">Click me</button></div>'

    formatter_obj = Html5Formatter(
        wrap_attributes_when=tag_name("button"),
        reformat_attribute_when={attribute_matches("style"): wrap_css_properties()},
    )

    result = formatter_obj.format_str(html.strip())
    # Default when_more_than=0, so all multi-property styles wrap (1+ properties)
    expected = cleandoc("""
        <!DOCTYPE html>
        <div>
          <button
            class="primary"
            style="
              color: red;
              background: blue;
              border: 1px solid black;
              padding: 10px;
            "
          >Click me</button>
        </div>
    """) + "\n"
    assert result == expected


def test_wrap_css_properties_with_custom_threshold():
    """Test wrap_css_properties with custom when_more_than threshold."""
    html = '<div><button style="color: red; background: blue;">Click</button></div>'

    # With when_more_than=1, this should wrap (2 properties > 1)
    formatter_obj = Html5Formatter(
        wrap_attributes_when=tag_name("button"),
        reformat_attribute_when={attribute_matches("style"): wrap_css_properties(when_more_than=1)},
    )

    result = formatter_obj.format_str(html.strip())
    expected = cleandoc("""
        <!DOCTYPE html>
        <div>
          <button
            style="
              color: red;
              background: blue;
            "
          >Click</button>
        </div>
    """) + "\n"
    assert result == expected


def test_wrap_css_properties_wraps_single_property():
    """Test that wrap_css_properties wraps even single properties by default."""
    html = '<div><button style="color: red;">Click</button></div>'

    # With default when_more_than=0, even single properties wrap (1 > 0)
    formatter_obj = Html5Formatter(
        wrap_attributes_when=tag_name("button"),
        reformat_attribute_when={attribute_matches("style"): wrap_css_properties()},
    )

    result = formatter_obj.format_str(html.strip())
    expected = cleandoc("""
        <!DOCTYPE html>
        <div>
          <button
            style="
              color: red;
            "
          >Click</button>
        </div>
    """) + "\n"
    assert result == expected


def test_wrap_css_properties_stays_inline_with_threshold():
    """Test that wrap_css_properties can keep short styles inline with custom threshold."""
    html = '<div><button style="color: red;">Click</button></div>'

    # With when_more_than=1, single property stays inline (1 <= 1)
    formatter_obj = Html5Formatter(
        wrap_attributes_when=tag_name("button"),
        reformat_attribute_when={attribute_matches("style"): wrap_css_properties(when_more_than=1)},
    )

    result = formatter_obj.format_str(html.strip())
    expected = cleandoc("""
        <!DOCTYPE html>
        <div>
          <button
            style="color: red;"
          >Click</button>
        </div>
    """) + "\n"
    assert result == expected


# CSS property reordering tests


def test_sort_css_properties():
    """Test alphabetical sorting of CSS properties."""
    html = '<div style="z-index: 1; color: red; background: blue; margin: 10px;">content</div>'

    formatter_obj = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("style"): reorder_css_properties(sort_css_properties())
        }
    )

    result = formatter_obj.format_str(html.strip())
    expected = '<!DOCTYPE html>\n<div style="background: blue; color: red; margin: 10px; z-index: 1;">content</div>\n'
    assert result == expected


def test_prioritize_css_properties():
    """Test prioritizing specific CSS properties to appear first."""
    html = '<div style="color: red; width: 100px; background: blue; display: flex; padding: 5px;">content</div>'

    formatter_obj = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("style"): reorder_css_properties(
                prioritize_css_properties("display", "width")
            )
        }
    )

    result = formatter_obj.format_str(html.strip())
    # display and width should be first, rest in original order
    expected = '<!DOCTYPE html>\n<div style="display: flex; width: 100px; color: red; background: blue; padding: 5px;">content</div>\n'
    assert result == expected


def test_defer_css_properties():
    """Test deferring specific CSS properties to appear last."""
    html = '<div style="z-index: 10; color: red; width: 100px; opacity: 0.5;">content</div>'

    formatter_obj = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("style"): reorder_css_properties(
                defer_css_properties("opacity", "z-index")
            )
        }
    )

    result = formatter_obj.format_str(html.strip())
    # color and width first (original order), then opacity and z-index
    expected = '<!DOCTYPE html>\n<div style="color: red; width: 100px; z-index: 10; opacity: 0.5;">content</div>\n'
    assert result == expected


def test_css_property_order():
    """Test semantic ordering of CSS properties."""
    html = '<div style="color: red; display: flex; margin: 10px; position: relative; font-size: 14px; background: blue;">content</div>'

    formatter_obj = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("style"): reorder_css_properties(css_property_order())
        }
    )

    result = formatter_obj.format_str(html.strip())
    # Layout (display, position) → Box model (margin) → Typography (color, font-size - alphabetical) → Visual (background)
    expected = '<!DOCTYPE html>\n<div style="display: flex; position: relative; margin: 10px; color: red; font-size: 14px; background: blue;">content</div>\n'
    assert result == expected


def test_css_variables_dependency_ordering():
    """Test that CSS variables are ordered by dependency (topological sort)."""
    html = '<div style="color: var(--text); --text: var(--primary); --primary: red;">content</div>'

    formatter_obj = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("style"): reorder_css_properties(css_property_order())
        }
    )

    result = formatter_obj.format_str(html.strip())
    # Variables should be ordered: --primary (no deps), --text (depends on --primary), color (uses --text)
    expected = '<!DOCTYPE html>\n<div style="--primary: red; --text: var(--primary); color: var(--text);">content</div>\n'
    assert result == expected


def test_css_variables_complex_dependencies():
    """Test CSS variables with multiple levels of dependencies."""
    html = '<div style="--level3: var(--level2); --level1: blue; --level2: var(--level1); background: var(--level3);">content</div>'

    formatter_obj = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("style"): reorder_css_properties(css_property_order())
        }
    )

    result = formatter_obj.format_str(html.strip())
    # Should order: --level1, --level2, --level3, then background
    expected = '<!DOCTYPE html>\n<div style="--level1: blue; --level2: var(--level1); --level3: var(--level2); background: var(--level3);">content</div>\n'
    assert result == expected


def test_css_variables_with_fallbacks():
    """Test CSS variables with fallback values in var() calls."""
    html = '<div style="--secondary: green; color: var(--primary, var(--secondary)); --primary: red;">content</div>'

    formatter_obj = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("style"): reorder_css_properties(css_property_order())
        }
    )

    result = formatter_obj.format_str(html.strip())
    # Variables first (--secondary, --primary), then color
    # Note: fallback detection might not catch --secondary in the fallback, but --primary should be detected
    result_has_vars_first = "--secondary" in result.split("color:")[0] and "--primary" in result.split("color:")[0]
    assert result_has_vars_first


def test_css_variables_cycle_detection():
    """Test that circular dependencies fall back to original order."""
    html = '<div style="--a: var(--b); --b: var(--a); color: red;">content</div>'

    formatter_obj = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("style"): reorder_css_properties(css_property_order())
        }
    )

    result = formatter_obj.format_str(html.strip())
    # With a cycle, should preserve original order for variables but still separate from normal props
    # Variables should come first, then normal properties
    assert "--a:" in result.split("color:")[0]
    assert "--b:" in result.split("color:")[0]


def test_css_variables_no_dependencies():
    """Test CSS variables with no dependencies are kept in original order."""
    html = '<div style="--color1: red; --color2: blue; --color3: green; background: white;">content</div>'

    formatter_obj = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("style"): reorder_css_properties(css_property_order())
        }
    )

    result = formatter_obj.format_str(html.strip())
    # All variables should come before background, order among themselves preserved
    vars_section = result.split("background:")[0]
    assert "--color1:" in vars_section
    assert "--color2:" in vars_section
    assert "--color3:" in vars_section


def test_enhanced_property_ordering():
    """Test the enhanced property ordering with box-sizing and box-shadow."""
    html = '<div style="box-shadow: 0 0 5px; color: red; box-sizing: border-box; display: block; width: 100px;">content</div>'

    formatter_obj = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("style"): reorder_css_properties(css_property_order())
        }
    )

    result = formatter_obj.format_str(html.strip())
    # Layout (display) → Box model (box-sizing, width - alphabetical) → Visual (box-shadow, color - alphabetical)
    expected = '<!DOCTYPE html>\n<div style="display: block; box-sizing: border-box; width: 100px; color: red; box-shadow: 0 0 5px;">content</div>\n'
    assert result == expected


def test_alphabetical_sorting_within_categories():
    """Test that unlisted properties are sorted alphabetically within their category."""
    html = '<div style="cursor: pointer; visibility: hidden; overflow: auto;">content</div>'

    formatter_obj = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("style"): reorder_css_properties(css_property_order())
        }
    )

    result = formatter_obj.format_str(html.strip())
    # All these are unlisted, should be alphabetical
    expected = '<!DOCTYPE html>\n<div style="cursor: pointer; overflow: auto; visibility: hidden;">content</div>\n'
    assert result == expected


def test_css_variables_before_normal_properties():
    """Test that all CSS variables appear before normal properties."""
    html = '<div style="color: red; --bg: blue; margin: 10px; --text: black; display: flex;">content</div>'

    formatter_obj = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("style"): reorder_css_properties(css_property_order())
        }
    )

    result = formatter_obj.format_str(html.strip())
    # Extract the style attribute value
    style_match = result.split('style="')[1].split('"')[0]

    # Find positions of variables and normal properties
    var_positions = [style_match.find("--bg"), style_match.find("--text")]
    normal_positions = [style_match.find("color:"), style_match.find("margin:"), style_match.find("display:")]

    # All variables should come before all normal properties
    max_var_pos = max(p for p in var_positions if p >= 0)
    min_normal_pos = min(p for p in normal_positions if p >= 0)

    assert max_var_pos < min_normal_pos


def test_css_formatter_fluent_api():
    """Test CssFormatter fluent API without .build()."""
    html = '<div style="z-index: 1; color: red; background: blue; margin: 10px;">content</div>'

    formatter_obj = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("style"): (
                css_formatter()
                .reorder(sort_css_properties())
                .wrap_when(lambda props: len(props) > 2)
            )
        }
    )

    result = formatter_obj.format_str(html.strip())
    # Should be sorted and wrapped (4 properties > 2)
    expected = cleandoc("""
        <!DOCTYPE html>
        <div style="
          background: blue;
          color: red;
          margin: 10px;
          z-index: 1;
        ">content</div>
    """) + "\n"
    assert result == expected


def test_css_formatter_reorder_only():
    """Test CssFormatter with reordering but no wrapping."""
    html = '<div style="z-index: 1; color: red; background: blue;">content</div>'

    formatter_obj = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("style"): css_formatter().reorder(sort_css_properties())
        }
    )

    result = formatter_obj.format_str(html.strip())
    # Should be sorted but inline (no wrap_when specified)
    expected = '<!DOCTYPE html>\n<div style="background: blue; color: red; z-index: 1;">content</div>\n'
    assert result == expected


def test_css_formatter_wrap_only():
    """Test CssFormatter with wrapping but no reordering."""
    html = '<div style="z-index: 1; color: red; background: blue;">content</div>'

    formatter_obj = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("style"): css_formatter().wrap_when(lambda props: len(props) > 2)
        }
    )

    result = formatter_obj.format_str(html.strip())
    # Should be wrapped but not reordered (original order preserved)
    expected = cleandoc("""
        <!DOCTYPE html>
        <div style="
          z-index: 1;
          color: red;
          background: blue;
        ">content</div>
    """) + "\n"
    assert result == expected


def test_wrap_css_properties_with_reorderer():
    """Test wrap_css_properties with reorderer argument (new breaking change API)."""
    html = '<div style="z-index: 1; color: red; background: blue; margin: 10px;">content</div>'

    formatter_obj = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("style"): wrap_css_properties(
                sort_css_properties(),
                when_more_than=2
            )
        }
    )

    result = formatter_obj.format_str(html.strip())
    # Should be sorted and wrapped (4 properties > 2)
    expected = cleandoc("""
        <!DOCTYPE html>
        <div style="
          background: blue;
          color: red;
          margin: 10px;
          z-index: 1;
        ">content</div>
    """) + "\n"
    assert result == expected


def test_multiple_reorderers_composition():
    """Test composing multiple reorderers together."""
    html = '<div style="z-index: 1; width: 100px; color: red; display: flex; background: blue; margin: 10px;">content</div>'

    formatter_obj = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("style"): reorder_css_properties(
                prioritize_css_properties("display"),  # display first
                defer_css_properties("z-index"),       # z-index last
            )
        }
    )

    result = formatter_obj.format_str(html.strip())
    # display first, z-index last, rest in original order
    expected = '<!DOCTYPE html>\n<div style="display: flex; width: 100px; color: red; background: blue; margin: 10px; z-index: 1;">content</div>\n'
    assert result == expected


def test_css_property_case_insensitive():
    """Test that CSS property matching is case-insensitive."""
    html = '<div style="Z-INDEX: 1; Color: red; BACKGROUND: blue; Display: flex;">content</div>'

    formatter_obj = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("style"): reorder_css_properties(
                prioritize_css_properties("display", "background")
            )
        }
    )

    result = formatter_obj.format_str(html.strip())
    # Case-insensitive matching: Display and BACKGROUND should be prioritized
    expected = '<!DOCTYPE html>\n<div style="Display: flex; BACKGROUND: blue; Z-INDEX: 1; Color: red;">content</div>\n'
    assert result == expected


def test_css_formatter_with_wrapped_attributes():
    """Test CssFormatter with wrapped HTML attributes."""
    html = '<button class="btn" style="z-index: 1; color: red; background: blue; margin: 5px;">Click</button>'

    formatter_obj = Html5Formatter(
        wrap_attributes_when=tag_name("button"),
        reformat_attribute_when={
            attribute_matches("style"): (
                css_formatter()
                .reorder(sort_css_properties())
                .wrap_when(lambda props: len(props) > 2)
            )
        }
    )

    result = formatter_obj.format_str(html.strip())
    expected = cleandoc("""
        <!DOCTYPE html>
        <button
          class="btn"
          style="
            background: blue;
            color: red;
            margin: 5px;
            z-index: 1;
          "
        >Click</button>
    """) + "\n"
    assert result == expected

