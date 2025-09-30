"""Tests for @supports_attributes decorator functionality."""

import re
from inspect import cleandoc

from markuplift import Formatter
from markuplift.predicates import (
    has_attribute,
    tag_in,
    html_block_elements,
    html_inline_elements,
    has_significant_content,
    PredicateFactory,
)


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
    assert has_class_predicate(p_element) is False  # p has no class attribute

    assert div_p_predicate(div_element) is True  # div matches tag_in
    assert div_p_predicate(p_element) is True  # p matches tag_in
    assert div_p_predicate(root) is False  # root doesn't match

    assert block_predicate(div_element) is True  # div is block element
    assert block_predicate(p_element) is True  # p is block element


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
        },
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
        },
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
            html_block_elements().with_attribute("style"): format_main_content,
        },
    )

    result = formatter.format_str(xml)
    assert 'style="0px"' in result


def test_non_decorated_functions_still_work():
    """Test that non-decorated functions still return ElementPredicateFactory and work normally."""
    from markuplift.predicates import is_element, attribute_count_min
    from lxml import etree

    # Test non-decorated functions still return ElementPredicateFactory (not PredicateFactory)
    # Note: attribute_equals is now decorated, so we use different functions for this test
    count_pred = attribute_count_min(1)
    element_pred = is_element()

    # Should be regular functions, not PredicateFactory instances
    assert not isinstance(count_pred, PredicateFactory)
    assert not isinstance(element_pred, PredicateFactory)

    # Should still work as ElementPredicateFactory
    xml = '<root><div class="test">content</div></root>'
    tree = etree.fromstring(xml)
    root = tree
    div = root.find(".//div")

    count_predicate = count_pred(root)
    element_predicate = element_pred(root)

    assert count_predicate(div) is True  # div has 1 attribute
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
        matches_xpath,
        tag_equals,
        tag_name,
        has_class,
        any_element,
        has_attribute,
        tag_in,
        html_block_elements,
        html_inline_elements,
        has_significant_content,
        css_block_elements,
        # Tier 1: HTML domain predicates
        html_void_elements,
        html_whitespace_significant_elements,
        html_metadata_elements,
        # Tier 2: Combinators
        any_of,
        all_of,
        not_matching,
        # Tier 3: Content predicates
        attribute_equals,
        has_no_significant_content,
        has_mixed_content,
        has_child_elements,
        PredicateFactory,
    )

    # All functions that support chaining should return PredicateFactory
    chaining_functions = [
        # Original functions
        matches_xpath("//div"),
        tag_equals("div"),
        tag_name("div"),
        has_class("test"),
        any_element(),
        has_attribute("class"),
        tag_in("div", "p"),
        html_block_elements(),
        html_inline_elements(),
        has_significant_content(),
        css_block_elements(),
        # Tier 1: HTML domain predicates
        html_void_elements(),
        html_whitespace_significant_elements(),
        html_metadata_elements(),
        # Tier 2: Combinators
        any_of(tag_equals("div"), tag_equals("span")),
        all_of(tag_equals("div"), has_attribute("class")),
        not_matching(tag_equals("div")),
        # Tier 3: Content predicates
        attribute_equals("class", "test"),
        has_no_significant_content(),
        has_mixed_content(),
        has_child_elements(),
    ]

    for func_result in chaining_functions:
        assert isinstance(func_result, PredicateFactory), f"Function {func_result} should return PredicateFactory"

        # All should support chaining
        chained = func_result.with_attribute("test")
        assert callable(chained), f"Chaining should work for {func_result}"

    print(f"All {len(chaining_functions)} chaining functions consistently use decorator pattern!")


def test_tier1_html_domain_predicates_with_chaining():
    """Test that Tier 1 HTML domain predicates work correctly with chaining."""
    xml = cleandoc("""
        <html>
            <head>
                <meta charset="utf-8" />
                <meta name="viewport" content="width=device-width" />
                <link rel="stylesheet" href="style.css" />
            </head>
            <body>
                <img src="logo.png" alt="Company Logo" class="logo" />
                <br class="spacer" />
                <pre class="code-block">formatted code</pre>
            </body>
        </html>
    """)

    from markuplift import Formatter
    from markuplift.predicates import (
        html_void_elements,
        html_whitespace_significant_elements,
        html_metadata_elements,
    )

    def uppercase_formatter(value, formatter, level):
        return value.upper()

    formatter = Formatter(
        reformat_attribute_when={
            # Match void elements with class attributes
            html_void_elements().with_attribute("class"): uppercase_formatter,
            # Match whitespace-significant elements with class attributes
            html_whitespace_significant_elements().with_attribute("class"): uppercase_formatter,
            # Match metadata elements with name attributes
            html_metadata_elements().with_attribute("name"): uppercase_formatter,
        }
    )

    result = formatter.format_str(xml)

    # Verify transformations
    assert 'class="SPACER"' in result  # void element with class
    assert 'class="CODE-BLOCK"' in result  # whitespace-significant with class
    assert 'name="VIEWPORT"' in result  # metadata element with name
    assert 'alt="Company Logo"' in result  # void element without matching predicate


def test_tier2_combinator_chaining():
    """Test that Tier 2 combinator predicates work correctly with chaining."""
    xml = cleandoc("""
        <root>
            <div class="widget" data-type="primary">Div with data</div>
            <span class="widget" data-type="secondary">Span with data</span>
            <p class="widget">Paragraph without data</p>
            <div class="other" data-type="tertiary">Other div</div>
        </root>
    """)

    from markuplift import Formatter
    from markuplift.predicates import any_of, all_of, not_matching, tag_equals, has_attribute

    def type_formatter(value, formatter, level):
        return value.replace("primary", "FIRST").replace("secondary", "SECOND")

    formatter = Formatter(
        reformat_attribute_when={
            # Match div OR span elements that have data-type attribute
            any_of(tag_equals("div"), tag_equals("span")).with_attribute("data-type"): type_formatter,
        }
    )

    result = formatter.format_str(xml)

    # Verify transformations
    assert 'data-type="FIRST"' in result  # div with data-type
    assert 'data-type="SECOND"' in result  # span with data-type
    # p doesn't have data-type, so not matched
    # Other div should be matched too
    assert 'data-type="tertiary"' in result  # other div (no transformation)


def test_tier3_content_predicate_chaining():
    """Test that Tier 3 content predicates work correctly with chaining."""
    xml = cleandoc("""
        <root>
            <div class="empty-container"></div>
            <div class="full-container">
                <p>Some text</p>
            </div>
            <span class="mixed" data-content="text">Text and <em>inline</em> elements</span>
        </root>
    """)

    from markuplift import Formatter
    from markuplift.predicates import (
        has_no_significant_content,
        has_child_elements,
        has_mixed_content,
        attribute_equals,
    )

    def class_formatter(value, formatter, level):
        return value.upper()

    formatter = Formatter(
        reformat_attribute_when={
            # Match empty elements with class attribute
            has_no_significant_content().with_attribute("class"): class_formatter,
            # Match elements with children that have class attribute
            has_child_elements().with_attribute("class"): class_formatter,
            # Match elements with class="button" that have data attributes
            attribute_equals("class", "button").with_attribute("data-action"): class_formatter,
        }
    )

    result = formatter.format_str(xml)

    # Verify transformations
    assert 'class="EMPTY-CONTAINER"' in result  # empty with class
    assert 'class="FULL-CONTAINER"' in result  # has children with class
