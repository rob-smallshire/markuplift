"""Tests for @supports_attributes decorator functionality."""

import re
from inspect import cleandoc

from markuplift import Formatter
from markuplift.predicates import (
    has_attribute, tag_in, html_block_elements, html_inline_elements, has_significant_content,
    supports_attributes, PredicateFactory
)
from markuplift.types import ElementPredicateFactory


def test_decorator_returns_predicate_factory():
    """Test that @supports_attributes decorator returns PredicateFactory instances."""
    # Test decorated functions return PredicateFactory
    assert isinstance(has_attribute("class"), PredicateFactory)
    assert isinstance(tag_in("div", "p"), PredicateFactory)
    assert isinstance(html_block_elements(), PredicateFactory)
    assert isinstance(html_inline_elements(), PredicateFactory)
    assert isinstance(has_significant_content(), PredicateFactory)


def test_backward_compatibility_as_callable():
    """Test that decorated functions still work as ElementPredicateFactory callables."""
    from lxml import etree

    # Create test document
    xml = '<root><div class="test">content</div><p>text</p></root>'
    tree = etree.fromstring(xml)
    root = tree

    # Test that decorated functions can still be called like ElementPredicateFactory
    has_class_predicate = has_attribute("class")(root)
    div_p_predicate = tag_in("div", "p")(root)
    block_predicate = html_block_elements()(root)

    # Test the predicates work correctly
    div_element = root.find(".//div")
    p_element = root.find(".//p")

    assert has_class_predicate(div_element) is True  # div has class attribute
    assert has_class_predicate(p_element) is False   # p has no class attribute

    assert div_p_predicate(div_element) is True      # div matches tag_in
    assert div_p_predicate(p_element) is True       # p matches tag_in
    assert div_p_predicate(root) is False           # root doesn't match

    assert block_predicate(div_element) is True     # div is block element
    assert block_predicate(p_element) is True       # p is block element


def test_chaining_functionality():
    """Test that chaining with .with_attribute() works correctly."""
    # Test basic chaining
    chained_factory = has_attribute("class").with_attribute("style")
    assert callable(chained_factory)

    # Test chaining with regex
    regex_chained = tag_in("div", "p").with_attribute("class", re.compile(r".*btn.*"))
    assert callable(regex_chained)

    # Test multiple chaining levels
    complex_chain = html_block_elements().with_attribute("role", "main")
    assert callable(complex_chain)


def test_chaining_in_formatter_usage():
    """Test that chained predicates work correctly in Formatter context."""
    xml = cleandoc("""
        <root>
            <div class="container" data-theme="dark">
                <p class="text-primary" style="color: blue;">Blue text</p>
                <p class="text-secondary">Regular text</p>
                <span class="btn-primary" role="button">Button</span>
            </div>
        </root>
    """)

    def style_formatter(value, formatter, level):
        return value.replace("blue", "red")

    formatter = Formatter(
        block_when=html_block_elements(),
        reformat_attribute_when={
            # Use chained predicate: match p tags that have style attribute
            tag_in("p").with_attribute("style"): style_formatter
        }
    )

    result = formatter.format_str(xml)
    assert 'style="color: red;"' in result  # Should be formatted
    assert 'class="text-secondary"' in result  # Other p should be unchanged


def test_chaining_with_regex_patterns():
    """Test chaining with regex patterns for both element and attribute selection."""
    xml = cleandoc("""
        <root>
            <div class="btn-primary" data-config="{'theme': 'dark'}">Button</div>
            <div class="btn-secondary" data-info="some data">Other Button</div>
            <p class="text-primary">Text</p>
        </root>
    """)

    def config_formatter(value, formatter, level):
        return value.replace("'", '"')  # Convert single quotes to double quotes

    formatter = Formatter(
        block_when=html_block_elements(),
        reformat_attribute_when={
            # Chain: div elements with data-config attributes containing JSON-like content
            tag_in("div").with_attribute("data-config", re.compile(r".*\{.*\}.*")): config_formatter
        }
    )

    result = formatter.format_str(xml)
    assert 'data-config=\'{"theme": "dark"}\'' in result  # Should be formatted (single quotes used)
    assert 'data-info="some data"' in result  # Should be unchanged


def test_decorator_preserves_function_metadata():
    """Test that @supports_attributes preserves function name and docstring."""
    # Test function name preservation
    assert has_attribute.__name__ == "has_attribute"
    assert tag_in.__name__ == "tag_in"

    # Test docstring preservation
    assert "Match elements that have a specific attribute" in has_attribute.__doc__
    assert "Match elements with any of the specified tag names" in tag_in.__doc__


def test_decorator_error_handling():
    """Test that decorated functions still handle errors correctly."""
    import pytest
    from markuplift.predicates import PredicateError

    # Test that validation errors still work
    with pytest.raises(PredicateError, match="At least one tag name must be provided"):
        tag_in()  # No tags provided should raise error


def test_multiple_chaining_levels():
    """Test that multiple levels of chaining work correctly."""
    xml = cleandoc("""
        <article>
            <div class="content" role="main" data-section="primary">
                <p style="margin: 0;">Content paragraph</p>
            </div>
            <div class="sidebar" role="complementary">
                <p>Sidebar paragraph</p>
            </div>
        </article>
    """)

    def format_main_content(value, formatter, level):
        return "0px"  # Remove margin

    formatter = Formatter(
        block_when=html_block_elements(),
        reformat_attribute_when={
            # Complex chain: div with role="main" that also has style attribute
            tag_in("div").with_attribute("role", "main"): lambda v, f, l: v,  # This won't match style
            # More specific: any element with both role and style
            html_block_elements().with_attribute("style"): format_main_content
        }
    )

    result = formatter.format_str(xml)
    assert 'style="0px"' in result


def test_non_decorated_functions_still_work():
    """Test that non-decorated functions still return ElementPredicateFactory and work normally."""
    from markuplift.predicates import attribute_equals, is_element
    from markuplift.types import ElementPredicateFactory
    from lxml import etree

    # Test non-decorated functions still return ElementPredicateFactory
    attr_eq = attribute_equals("class", "test")
    element_pred = is_element()

    # Should be regular functions, not PredicateFactory instances
    assert not isinstance(attr_eq, PredicateFactory)
    assert not isinstance(element_pred, PredicateFactory)

    # Should still work as ElementPredicateFactory
    xml = '<root><div class="test">content</div></root>'
    tree = etree.fromstring(xml)
    root = tree
    div = root.find(".//div")

    attr_predicate = attr_eq(root)
    element_predicate = element_pred(root)

    assert attr_predicate(div) is True
    assert element_predicate(div) is True


def test_decorator_with_complex_functions():
    """Test decorator works with functions that have complex signatures and validation."""
    # has_attribute has validation
    decorated_func = has_attribute("valid-attr")
    assert isinstance(decorated_func, PredicateFactory)

    # tag_in has varargs and validation
    decorated_varargs = tag_in("div", "p", "span")
    assert isinstance(decorated_varargs, PredicateFactory)

    # Functions should still validate their arguments
    import pytest
    from markuplift.predicates import PredicateError

    with pytest.raises(PredicateError):
        has_attribute("")  # Empty attribute name should fail


def test_chaining_type_safety():
    """Test that chaining maintains proper type safety and error handling."""
    import pytest

    # Valid chaining should work
    valid_chain = has_attribute("class").with_attribute("style", "color: red")
    assert callable(valid_chain)

    # Invalid attribute types should raise errors
    with pytest.raises(TypeError):
        has_attribute("class").with_attribute(123)  # Invalid type for attribute name

    with pytest.raises(TypeError):
        has_attribute("class").with_attribute("style", 123)  # Invalid type for attribute value


def test_all_chaining_functions_use_decorator_consistently():
    """Test that all functions supporting chaining use the @supports_attributes decorator consistently."""
    from markuplift.predicates import (
        matches_xpath, tag_equals, tag_name, has_class, any_element,
        has_attribute, tag_in, html_block_elements, html_inline_elements, has_significant_content,
        PredicateFactory
    )

    # All functions that support chaining should return PredicateFactory
    chaining_functions = [
        matches_xpath('//div'),
        tag_equals('div'),
        tag_name('div'),
        has_class('test'),
        any_element(),
        has_attribute('class'),
        tag_in('div', 'p'),
        html_block_elements(),
        html_inline_elements(),
        has_significant_content()
    ]

    for func_result in chaining_functions:
        assert isinstance(func_result, PredicateFactory), f"Function {func_result} should return PredicateFactory"

        # All should support chaining
        chained = func_result.with_attribute("test")
        assert callable(chained), f"Chaining should work for {func_result}"

    print(f"All {len(chaining_functions)} chaining functions consistently use decorator pattern!")