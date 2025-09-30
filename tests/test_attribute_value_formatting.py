"""Tests for attribute value formatting functionality."""

import re
from inspect import cleandoc

from markuplift import Formatter, Html5Formatter, wrap_css_properties
from markuplift.predicates import tag_name, has_class, attribute_matches, any_element, pattern


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

    with pytest.raises(TypeError, match="attribute_name must be str, re.Pattern, or callable, got int"):
        attribute_matches(123)  # Invalid type

    with pytest.raises(TypeError, match="attribute_name cannot be None"):
        attribute_matches(None)  # None not allowed for name

    with pytest.raises(TypeError, match="attribute_name must be str, re.Pattern, or callable, got list"):
        attribute_matches([])  # List not allowed


def test_invalid_value_type_error():
    """Test that invalid value types raise TypeError."""
    import pytest
    from markuplift.predicates import attribute_matches

    with pytest.raises(TypeError, match="attribute_value must be str, re.Pattern, or callable, or None, got int"):
        attribute_matches("class", 123)  # Invalid type

    with pytest.raises(TypeError, match="attribute_value must be str, re.Pattern, or callable, or None, got list"):
        attribute_matches("class", [])  # List not allowed


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

    with pytest.raises(TypeError, match="attribute_name must be str, re.Pattern, or callable, got int"):
        tag_name("div").with_attribute(123)

    with pytest.raises(TypeError, match="attribute_value must be str, re.Pattern, or callable, or None, got int"):
        tag_name("div").with_attribute("class", 123)


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

    with pytest.raises(TypeError, match="attribute_name cannot be None"):
        predicate_factory.with_attribute(None)

    with pytest.raises(TypeError, match="attribute_value must be str, re.Pattern, or callable, or None, got list"):
        predicate_factory.with_attribute("class", [])


def test_type_safety_edge_cases():
    """Test various edge cases for type safety."""
    from markuplift.predicates import attribute_matches, any_element

    # Test that boolean values are rejected
    import pytest

    with pytest.raises(TypeError, match="attribute_name must be str, re.Pattern, or callable, got bool"):
        attribute_matches(True)

    with pytest.raises(TypeError, match="attribute_value must be str, re.Pattern, or callable, or None, got bool"):
        attribute_matches("class", False)

    # Test that dict/tuple values are rejected
    with pytest.raises(TypeError, match="attribute_name must be str, re.Pattern, or callable, got dict"):
        attribute_matches({})

    with pytest.raises(TypeError, match="attribute_value must be str, re.Pattern, or callable, or None, got tuple"):
        attribute_matches("class", ())

    # Test any_element chaining with invalid types
    with pytest.raises(TypeError, match="attribute_name must be str, re.Pattern, or callable, got float"):
        any_element().with_attribute(3.14)  # Float not allowed



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

