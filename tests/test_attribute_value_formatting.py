"""Tests for attribute value formatting functionality."""

import re
from inspect import cleandoc

from markuplift import Formatter
from markuplift.predicates import tag_name, has_class, attribute_matches, any_element, pattern


def test_basic_attribute_formatting():
    """Test basic attribute formatting with exact string matching."""
    xml = '<div style="color: red; background: blue;">content</div>'

    def css_formatter(value, formatter, level):
        # Add spaces around colons
        return value.replace(":", ": ")

    formatter = Formatter(
        block_when=tag_name("div"),
        reformat_attribute_when={
            attribute_matches("style"): css_formatter
        }
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
        block_when=tag_name("div"),
        reformat_attribute_when={
            has_class("widget").with_attribute("style"): css_formatter
        }
    )

    result = formatter.format_str(xml)
    expected = '<div class="widget" style="margin:0; padding:5px; ">content</div>'
    assert result == expected


def test_regex_pattern_attribute_names():
    """Test attribute formatting with regex patterns for attribute names."""
    xml = '''
    <div data-config="{'theme':'dark'}" data-options="{'animate':true}">content</div>
    '''

    def json_formatter(value, formatter, level):
        # Add spaces after colons and commas
        return value.replace(":", ": ").replace(",", ", ")

    formatter = Formatter(
        block_when=tag_name("div"),
        reformat_attribute_when={
            attribute_matches(re.compile(r"data-.*")): json_formatter
        }
    )

    result = formatter.format_str(xml.strip())
    expected = '<div data-config="{\'theme\': \'dark\'}" data-options="{\'animate\': true}">content</div>'
    assert result == expected


def test_regex_pattern_attribute_values():
    """Test attribute formatting with regex patterns for attribute values."""
    xml = '''
    <div>
        <a href="styles.css">CSS link</a>
        <a href="script.js">JS link</a>
        <a href="page.html">HTML link</a>
    </div>
    '''

    def css_link_formatter(value, formatter, level):
        return f"assets/css/{value}"

    formatter = Formatter(
        block_when=tag_name("div"),
        reformat_attribute_when={
            tag_name("a").with_attribute("href", re.compile(r".*\.css$")): css_link_formatter
        }
    )

    result = formatter.format_str(xml.strip())
    expected = cleandoc('''
        <div>
          <a href="assets/css/styles.css">CSS link</a>
          <a href="script.js">JS link</a>
          <a href="page.html">HTML link</a>
        </div>
    ''')
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
        }
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
        reformat_attribute_when={
            tag_name("link").with_attribute("href", pattern(r".*\.css$")): css_formatter
        }
    )

    result = formatter.format_str(xml)
    expected = '<link rel="stylesheet" href="optimized/main.css" type="text/css" />'
    assert result == expected


def test_any_element_with_attribute():
    """Test any_element() with attribute chaining."""
    xml = '''
    <div style="color: red;">
        <span style="font-weight: bold;">
            <p style="margin: 0;">Text</p>
        </span>
    </div>
    '''

    def css_formatter(value, formatter, level):
        return value.replace(": ", ":")

    formatter = Formatter(
        block_when=any_element(),
        reformat_attribute_when={
            any_element().with_attribute("style"): css_formatter
        }
    )

    result = formatter.format_str(xml.strip())
    expected = cleandoc('''
        <div style="color:red;">
          <span style="font-weight:bold;">
            <p style="margin:0;">Text</p>
          </span>
        </div>
    ''')
    assert result == expected


def test_complex_chaining_scenario():
    """Test complex chaining with multiple predicates and formatters."""
    xml = '''
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
    '''

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
        }
    )

    result = formatter.format_str(xml.strip())
    # JSON formatting should be applied to pre element's data-config
    assert '{ "theme": "dark", "lineNumbers": true}' in result
    # CSS formatting should be applied to div's style
    assert 'margin - top:  1rem' in result


def test_attribute_formatting_with_text_formatting():
    """Test that attribute formatting works alongside text formatting."""
    xml = '<code style="font-family: monospace;">function() { return true; }</code>'

    def css_formatter(value, formatter, level):
        return value.replace(": ", ":")

    def js_formatter(text, formatter, level):
        return text.replace("{ ", "{\n  ").replace(" }", "\n}")

    formatter = Formatter(
        block_when=tag_name("code"),
        reformat_attribute_when={
            attribute_matches("style"): css_formatter
        },
        reformat_text_when={
            tag_name("code"): js_formatter
        }
    )

    result = formatter.format_str(xml)
    expected = '<code style="font-family:monospace;">function() {\n  return true;\n}</code>'
    assert result == expected


def test_no_formatters_applied():
    """Test that attributes are unchanged when no formatters match."""
    xml = '<div title="test" class="example">content</div>'

    formatter = Formatter(
        block_when=tag_name("div"),
        reformat_attribute_when={
            attribute_matches("nonexistent"): lambda v, f, l: v.upper()
        }
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
        }
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
        }
    )

    result = formatter.format_str(xml)
    expected = '<div class="formatted" style="formatted">content</div>'
    assert result == expected


def test_namespace_attributes():
    """Test attribute formatting with namespaced elements."""
    xml = '''
    <root xmlns:custom="http://example.com">
        <custom:element custom:data="value" regular="attr">content</custom:element>
    </root>
    '''

    def formatter(value, formatter, level):
        return value.upper()

    formatter_obj = Formatter(
        block_when=any_element(),
        reformat_attribute_when={
            # This will match both namespaced and regular attributes
            attribute_matches(re.compile(r".*data.*")): formatter,
        }
    )

    result = formatter_obj.format_str(xml.strip())
    # Should format the custom:data attribute (appears as just "data" after parsing)
    assert 'data="VALUE"' in result


def test_indentation_context_in_formatter():
    """Test that formatters receive correct indentation context."""
    xml = '''
    <div>
        <nested>
            <deep style="margin: 0;">content</deep>
        </nested>
    </div>
    '''

    def indent_aware_formatter(value, formatter, level):
        # Add indentation-based prefix
        prefix = "  " * level
        return f"{prefix}{value}"

    formatter_obj = Formatter(
        block_when=any_element(),
        reformat_attribute_when={
            attribute_matches("style"): indent_aware_formatter
        }
    )

    result = formatter_obj.format_str(xml.strip())
    # The deep element should be at indentation level 2, so style should have 4 spaces prefix
    assert 'style="    margin: 0;"' in result


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
        }
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
    import re
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