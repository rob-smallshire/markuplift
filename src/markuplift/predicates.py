"""Element predicate factories for XML/HTML matching.

This module provides a comprehensive collection of ElementPredicateFactory functions
that create optimized element matching predicates. All factories follow the same pattern:
they take configuration parameters and return a function that takes a document root
and returns an ElementPredicate function.

The factory pattern ensures that expensive operations (like XPath evaluation) are
performed only once per document rather than once per element, providing significant
performance benefits.

Factory Categories:
    Basic Matching: matches_xpath, tag_equals, tag_in
    Attributes: has_attribute, attribute_equals, attribute_count_*
    Node Types: is_comment, is_processing_instruction, is_element
    Content: has_significant_content, has_mixed_content, has_child_elements
    HTML Domain: html_block_elements, html_inline_elements, etc.
    Combinators: any_of, all_of, not_matching

Attribute Chaining Support:
    Predicate factories decorated with @supports_attributes allow chaining of attribute
    queries on the selected elements using .with_attribute() syntax with flexible matchers:

        # String matching
        has_attribute("class").with_attribute("style", "color: red")
        html_block_elements().with_attribute("data-config")

        # Regex matching
        tag_in("div", "p").with_attribute("role", re.compile(r"button|link"))

        # Function matching
        html_block_elements().with_attribute("style", lambda v: v.count(';') >= 3)
        tag_in("input", "textarea").with_attribute("class", lambda v: "form" in v)

    These decorated factories return PredicateFactory instances that wrap ElementPredicateFactory
    callables, maintaining full backward compatibility while adding chaining capabilities.

Standard Predicates:
    never_match: A standard ElementPredicate that always returns False
    never_matches: A standard ElementPredicateFactory that creates never-matching predicates
"""

from lxml import etree
import re
from re import Pattern
from typing import Union, Optional, Callable

# Import type aliases
from markuplift.types import (
    ElementPredicate,
    ElementPredicateFactory,
    AttributePredicate,
    AttributePredicateFactory,
    NameMatcher,
    ValueMatcher,
)


# HTML5 element sets for predicate factories
# These constants define canonical sets of HTML elements by category

_HTML_INLINE_ELEMENTS = frozenset({
    "a", "abbr", "b", "bdi", "bdo", "br", "cite", "code", "data", "dfn",
    "em", "i", "kbd", "mark", "q", "ruby", "s", "samp", "small", "span",
    "strong", "sub", "sup", "time", "u", "var", "wbr",
})

_HTML_VOID_ELEMENTS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})

_HTML_WHITESPACE_SIGNIFICANT_ELEMENTS = frozenset({
    "pre", "style", "script", "textarea", "code"
})

_HTML_METADATA_ELEMENTS = frozenset({
    "head", "title", "base", "link", "meta", "style", "script", "noscript"
})

_CSS_BLOCK_ELEMENTS = frozenset({
    "address", "article", "aside", "blockquote", "canvas", "dd", "div",
    "dl", "dt", "fieldset", "figcaption", "figure", "footer", "form",
    "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "li", "main",
    "nav", "noscript", "ol", "p", "section", "table", "tfoot", "ul", "video",
})

_HTML_BLOCK_STRUCTURE_ELEMENTS = frozenset({
    "html", "head", "body", "title", "meta", "link", "script",
    "tbody", "thead", "tr", "details", "dialog", "hgroup", "pre",
})


class PredicateError(Exception):
    """Exception raised for errors in predicate configuration or evaluation.

    This exception is raised when there are issues with predicate factory
    parameters or configuration, such as invalid XPath expressions.
    """

    pass


def _create_matcher(
    value: Union[str, Pattern[str], Callable[[str], bool], None], matcher_name: str, allow_none: bool = False
) -> Callable[[str], bool]:
    """Create optimized matcher function for string/pattern/function matching.

    This helper function creates efficient matcher functions at predicate factory
    creation time, avoiding repeated type checking during predicate evaluation.

    Args:
        value: String for exact match, Pattern for regex, callable for custom logic, or None
        matcher_name: Description for error messages ("attribute_name" or "attribute_value")
        allow_none: Whether None values are permitted

    Returns:
        Callable that takes a string and returns bool

    Raises:
        TypeError: If value is not the expected type
        RuntimeError: If callable matcher raises an exception or returns non-bool

    Examples:
        name_matcher = _create_matcher("style", "attribute_name", allow_none=False)
        value_matcher = _create_matcher(re.compile(r"color:.*"), "attribute_value", allow_none=False)
        function_matcher = _create_matcher(lambda v: v.count(';') >= 3, "attribute_value", allow_none=False)
        optional_matcher = _create_matcher(None, "attribute_value", allow_none=True)
    """
    if value is None:
        if allow_none:
            return lambda s: True  # Match anything
        else:
            raise TypeError(f"{matcher_name} cannot be None")
    elif isinstance(value, str):
        return lambda s: s == value
    elif isinstance(value, Pattern):
        return lambda s: bool(value.match(s))
    elif callable(value):
        # Wrap user function to handle exceptions and validate return type
        def safe_matcher(s):
            try:
                result = value(s)
                if not isinstance(result, bool):
                    raise TypeError(f"Matcher function must return bool, got {type(result).__name__}")
                return result
            except Exception as e:
                raise RuntimeError(f"Error in {matcher_name} matcher function: {e}") from e

        return safe_matcher
    else:
        allowed = "str, re.Pattern, or callable" + (", or None" if allow_none else "")  # type: ignore[unreachable]
        raise TypeError(f"{matcher_name} must be {allowed}, got {type(value).__name__}")


class PredicateFactory:
    """Base class for chainable predicate factories.

    This class wraps ElementPredicateFactory functions to provide chainable
    methods for attribute selection. All existing predicate functions will
    return instances of this class while maintaining backward compatibility
    as callable objects.

    The chainable methods allow natural syntax like:
        has_class("widget").with_attribute("style")
        tag_name("img").with_attribute("src", re.compile(r"^https://"))
    """

    _factory_func: ElementPredicateFactory

    def __new__(cls, factory_func: ElementPredicateFactory):
        """Create a new PredicateFactory, or return existing instance if already wrapped.

        This optimization avoids double-wrapping when a PredicateFactory instance
        is passed to PredicateFactory() again.

        Args:
            factory_func: Function or PredicateFactory that creates ElementPredicate

        Returns:
            PredicateFactory instance (either new or existing)
        """
        if isinstance(factory_func, cls):
            # Already a PredicateFactory, return it as-is
            return factory_func

        # Create new instance for functions or other callable types
        instance = super().__new__(cls)
        instance._factory_func = factory_func
        return instance

    def __call__(self, root: etree._Element) -> ElementPredicate:
        """Make this object callable like the original ElementPredicateFactory.

        Args:
            root: The document root element

        Returns:
            ElementPredicate function for testing elements
        """
        return self._factory_func(root)

    def with_attribute(self, name: NameMatcher, value: Optional[ValueMatcher] = None) -> AttributePredicateFactory:
        """Chain to create attribute predicate for specific attribute.

        Args:
            name: Attribute name matcher - can be:
                - str: Exact attribute name match
                - re.Pattern: Regex pattern for attribute name
                - Callable[[str], bool]: Custom function to test attribute name
            value: Optional attribute value matcher - can be:
                - str: Exact attribute value match
                - re.Pattern: Regex pattern for attribute value
                - Callable[[str], bool]: Custom function to test attribute value
                - None: Match any value (default)

        Returns:
            AttributePredicateFactory that matches elements passing this predicate
            and having the specified attribute name/value

        Raises:
            TypeError: If name or value is not the expected type
            RuntimeError: If custom matcher function raises exception or returns non-bool

        Examples:
            # String matching
            has_class("widget").with_attribute("style")

            # Regex matching
            tag_name("img").with_attribute("src", re.compile(r"^https://"))
            matches_xpath("//div").with_attribute(re.compile(r"data-.*"))

            # Function matching
            html_block_elements().with_attribute("style", lambda v: v.count(';') >= 3)
            tag_in("div", "p").with_attribute("class", lambda v: "btn" in v and "primary" in v)
        """
        # Create optimized matcher functions once at setup time
        name_matcher = _create_matcher(name, "attribute_name", allow_none=False)
        value_matcher = _create_matcher(value, "attribute_value", allow_none=True)

        def attribute_factory(root: etree._Element) -> AttributePredicate:
            element_predicate = self._factory_func(root)

            def predicate(element: etree._Element, attr_name: str, attr_value: str) -> bool:
                # Must match element predicate first and then use pre-compiled matchers
                return element_predicate(element) and name_matcher(attr_name) and value_matcher(attr_value)

            return predicate

        return attribute_factory


def supports_attributes(func: Callable[..., ElementPredicateFactory]) -> Callable[..., PredicateFactory]:
    """Decorator to add attribute chaining support to ElementPredicateFactory functions.

    This decorator wraps functions that return ElementPredicateFactory instances,
    enabling them to support the .with_attribute() chaining syntax. The decorated
    function maintains full backward compatibility while gaining attribute predicate
    capabilities.

    Args:
        func: Function that returns an ElementPredicateFactory

    Returns:
        Function that returns a PredicateFactory with attribute chaining support

    Examples:
        @supports_attributes
        def has_significant_content() -> ElementPredicateFactory:
            # existing implementation

        # Now supports chaining:
        has_significant_content().with_attribute("class", "important")
        has_significant_content().with_attribute("data-config")
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs) -> PredicateFactory:
        # Call the original function to get the ElementPredicateFactory
        element_predicate_factory = func(*args, **kwargs)
        # Wrap it in PredicateFactory to enable chaining
        return PredicateFactory(element_predicate_factory)

    return wrapper


def _validate_tag_name(tag: str) -> None:
    """Validate that a tag name is valid for XML.

    Args:
        tag: The tag name to validate

    Raises:
        PredicateError: If the tag name is invalid
    """
    if not tag:
        raise PredicateError("Tag name cannot be empty")

    # Use lxml to validate by attempting to create an element
    try:
        etree.Element(tag)
    except ValueError as e:
        raise PredicateError(f"Invalid tag name '{tag}': {e}") from e


def _validate_attribute_name(attr: str) -> None:
    """Validate that an attribute name is valid for XML.

    Args:
        attr: The attribute name to validate

    Raises:
        PredicateError: If the attribute name is invalid
    """
    if not attr:
        raise PredicateError("Attribute name cannot be empty")

    # Use lxml to validate by attempting to set an attribute
    try:
        elem: etree._Element = etree.Element("test")
        elem.set(attr, "value")
    except ValueError as e:
        raise PredicateError(f"Invalid attribute name '{attr}': {e}") from e


@supports_attributes
def matches_xpath(xpath_expr: str) -> ElementPredicateFactory:
    """Match elements using XPath expressions.

    Only supports XPath expressions that return element nodes.

    Args:
        xpath_expr: XPath expression that must return element nodes

    Returns:
        A chainable predicate factory that creates optimized XPath-based predicates

    Raises:
        PredicateError: If XPath is invalid or returns non-element results
    """
    # Validate XPath syntax immediately using a temporary element
    try:
        temp_element: etree._Element = etree.Element("temp")
        temp_element.xpath(xpath_expr)
    except etree.XPathEvalError as e:
        raise PredicateError(f"Invalid XPath expression '{xpath_expr}': {e}") from e

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        try:
            xpath_results = root.xpath(xpath_expr)

            # Handle non-iterable results (single values like count(), boolean())
            if not isinstance(xpath_results, list):
                raise PredicateError(
                    f"XPath '{xpath_expr}' returned non-element results: {{{type(xpath_results).__name__}}}. "
                    f"Only element-returning XPath expressions are supported."
                )

            # Validate that list results contain only elements
            if xpath_results and not all(isinstance(item, etree._Element) for item in xpath_results):
                non_element_types = {
                    type(item).__name__ for item in xpath_results if not isinstance(item, etree._Element)
                }
                raise PredicateError(
                    f"XPath '{xpath_expr}' returned non-element results: {non_element_types}. "
                    f"Only element-returning XPath expressions are supported."
                )

            matches = set(xpath_results)

        except etree.XPathEvalError as e:
            raise PredicateError(f"XPath evaluation failed '{xpath_expr}': {e}") from e

        def element_predicate(element: etree._Element) -> bool:
            return element in matches

        return element_predicate

    return create_document_predicate


@supports_attributes
def tag_equals(tag: str) -> ElementPredicateFactory:
    """Match elements with a specific tag name.

    Args:
        tag: Tag name to match

    Returns:
        A chainable predicate factory that matches elements with the specified tag

    Raises:
        PredicateError: If the tag name is invalid
    """
    _validate_tag_name(tag)

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            return element.tag == tag

        return element_predicate

    return create_document_predicate


@supports_attributes
def tag_name(tag: str) -> ElementPredicateFactory:
    """Match elements with a specific tag name (alias for tag_equals).

    This is a more readable alias for tag_equals that works well in chaining:
    tag_name("div").with_attribute("class")

    Args:
        tag: Tag name to match

    Returns:
        A chainable predicate factory that matches elements with the specified tag

    Raises:
        PredicateError: If the tag name is invalid
    """
    return tag_equals(tag)


@supports_attributes
def has_class(class_name: str) -> ElementPredicateFactory:
    """Match elements that have a specific CSS class.

    This is a convenient function for matching elements by CSS class,
    which is commonly used in HTML formatting.

    Args:
        class_name: CSS class name to match (exact match)

    Returns:
        A chainable predicate factory that matches elements with the specified class

    Examples:
        has_class("widget")
        has_class("btn-primary").with_attribute("onclick")
    """

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            classes = element.get("class", "").split()
            return class_name in classes

        return element_predicate

    return create_document_predicate


@supports_attributes
def tag_in(*tags: str) -> ElementPredicateFactory:
    """Match elements with any of the specified tag names.

    Args:
        *tags: Tag names to match

    Returns:
        An element predicate factory that matches elements with any of the specified tags

    Raises:
        PredicateError: If any tag name is invalid or if no tags are provided

    Examples:
        Basic usage:
            tag_in("div", "p", "span")
            tag_in("h1", "h2", "h3")

        With chaining (enabled by @supports_attributes):
            tag_in("div", "section").with_attribute("class", "container")
            tag_in("img", "video").with_attribute("src")
    """
    if not tags:
        raise PredicateError("At least one tag name must be provided")

    for tag in tags:
        _validate_tag_name(tag)

    tag_set = set(tags)

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            return element.tag in tag_set

        return element_predicate

    return create_document_predicate


@supports_attributes
def has_attribute(attr: str) -> ElementPredicateFactory:
    """Match elements that have a specific attribute.

    Args:
        attr: Attribute name to check for

    Returns:
        An element predicate factory that matches elements having the specified attribute

    Raises:
        PredicateError: If the attribute name is invalid

    Examples:
        Basic usage:
            has_attribute("class")
            has_attribute("data-config")

        With chaining (enabled by @supports_attributes):
            has_attribute("class").with_attribute("role", "button")
            has_attribute("data-*").with_attribute("style", re.compile(r"color:.*"))
    """
    _validate_attribute_name(attr)

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            return attr in element.attrib

        return element_predicate

    return create_document_predicate


@supports_attributes
def attribute_equals(attr: str, value: str) -> ElementPredicateFactory:
    """Match elements with a specific attribute value.

    Args:
        attr: Attribute name to check
        value: Expected attribute value

    Returns:
        A chainable predicate factory that matches elements with the specified attribute value

    Raises:
        PredicateError: If the attribute name is invalid

    Examples:
        Basic usage:
            attribute_equals("class", "button")
            attribute_equals("data-type", "primary")

        With chaining (enabled by @supports_attributes):
            # Match elements with class="button" that also have a style attribute
            attribute_equals("class", "button").with_attribute("style")

            # Match elements with specific role that have data attributes
            attribute_equals("role", "button").with_attribute("data-action")
    """
    _validate_attribute_name(attr)

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            return element.get(attr) == value

        return element_predicate

    return create_document_predicate


def attribute_count_min(min_count: int) -> ElementPredicateFactory:
    """Match elements with at least a minimum number of attributes.

    Args:
        min_count: Minimum number of attributes required

    Returns:
        An element predicate factory that matches elements with at least min_count attributes

    Raises:
        PredicateError: If min_count is negative
    """
    if min_count < 0:
        raise PredicateError(f"Minimum count must be non-negative, got {min_count}")

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            return len(element.attrib) >= min_count

        return element_predicate

    return create_document_predicate


def attribute_count_max(max_count: int) -> ElementPredicateFactory:
    """Match elements with at most a maximum number of attributes.

    Args:
        max_count: Maximum number of attributes allowed

    Returns:
        An element predicate factory that matches elements with at most max_count attributes

    Raises:
        PredicateError: If max_count is negative
    """
    if max_count < 0:
        raise PredicateError(f"Maximum count must be non-negative, got {max_count}")

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            return len(element.attrib) <= max_count

        return element_predicate

    return create_document_predicate


def attribute_count_between(min_count: int, max_count: int) -> ElementPredicateFactory:
    """Match elements with attribute count in a specific range.

    Args:
        min_count: Minimum number of attributes required
        max_count: Maximum number of attributes allowed

    Returns:
        An element predicate factory that matches elements with attribute count in the specified range

    Raises:
        PredicateError: If min_count or max_count is negative, or if min_count > max_count
    """
    if min_count < 0:
        raise PredicateError(f"Minimum count must be non-negative, got {min_count}")
    if max_count < 0:
        raise PredicateError(f"Maximum count must be non-negative, got {max_count}")
    if min_count > max_count:
        raise PredicateError(f"Minimum count ({min_count}) cannot be greater than maximum count ({max_count})")

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            attr_count = len(element.attrib)
            return min_count <= attr_count <= max_count

        return element_predicate

    return create_document_predicate


def is_comment() -> ElementPredicateFactory:
    """Match comment nodes.

    Returns:
        An element predicate factory that matches comment nodes
    """

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            return isinstance(element, etree._Comment)

        return element_predicate

    return create_document_predicate


def is_processing_instruction(target: str = None) -> ElementPredicateFactory:
    """Match processing instruction nodes.

    Args:
        target: Optional target to filter by (e.g., "xml-stylesheet")

    Returns:
        An element predicate factory that matches processing instruction nodes

    Raises:
        PredicateError: If target is an empty string
    """
    if target == "":
        raise PredicateError("Processing instruction target cannot be empty (use None for any target)")

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            if not isinstance(element, etree._ProcessingInstruction):
                return False
            if target is None:
                return True
            return element.target == target

        return element_predicate

    return create_document_predicate


def is_element() -> ElementPredicateFactory:
    """Match regular elements (not comments or processing instructions).

    Returns:
        An element predicate factory that matches regular elements
    """

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            return isinstance(element, etree._Element) and not isinstance(
                element, (etree._Comment, etree._ProcessingInstruction)
            )

        return element_predicate

    return create_document_predicate


# Content-based predicates
@supports_attributes
def has_significant_content() -> ElementPredicateFactory:
    """Match elements with non-whitespace text content.

    Returns:
        An element predicate factory that matches elements containing significant text
    """
    from markuplift.utilities import has_direct_significant_text

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            return has_direct_significant_text(element)

        return element_predicate

    return create_document_predicate


@supports_attributes
def has_no_significant_content() -> ElementPredicateFactory:
    """Match empty or whitespace-only elements.

    Returns:
        A chainable predicate factory that matches elements with no significant content

    Examples:
        Basic usage:
            has_no_significant_content()

        With chaining (enabled by @supports_attributes):
            # Match empty elements that have placeholder attributes
            has_no_significant_content().with_attribute("placeholder")

            # Match empty elements with specific classes
            has_no_significant_content().with_attribute("class", "empty")
    """
    from markuplift.utilities import has_direct_significant_text

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            return not has_direct_significant_text(element)

        return element_predicate

    return create_document_predicate


@supports_attributes
def has_mixed_content() -> ElementPredicateFactory:
    """Match elements containing both text and child elements.

    Returns:
        A chainable predicate factory that matches elements in mixed content

    Examples:
        Basic usage:
            has_mixed_content()

        With chaining (enabled by @supports_attributes):
            # Match mixed content elements with specific classes
            has_mixed_content().with_attribute("class", "rich-text")

            # Match mixed content elements with data attributes
            has_mixed_content().with_attribute("data-content-type", "mixed")
    """
    from markuplift.utilities import is_in_mixed_content

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            return is_in_mixed_content(element)

        return element_predicate

    return create_document_predicate


@supports_attributes
def has_child_elements() -> ElementPredicateFactory:
    """Match elements that contain child elements.

    Returns:
        A chainable predicate factory that matches elements with child elements

    Examples:
        Basic usage:
            has_child_elements()

        With chaining (enabled by @supports_attributes):
            # Match container elements that have child elements and specific classes
            has_child_elements().with_attribute("class", "container")

            # Match elements with children that have role attributes
            has_child_elements().with_attribute("role", "group")
    """

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            return len(element) > 0

        return element_predicate

    return create_document_predicate


# Domain-specific predicates
@supports_attributes
def html_block_elements() -> ElementPredicateFactory:
    """Match HTML block elements including both CSS block elements and structural elements.

    This predicate builds on css_block_elements() and adds HTML document structure
    elements and semantic elements that should be treated as block-level for formatting,
    even if they don't have CSS display: block by default.

    Returns:
        An element predicate factory that matches HTML block elements

    Examples:
        Basic usage:
            html_block_elements()

        With chaining (enabled by @supports_attributes):
            html_block_elements().with_attribute("class", "container")
            html_block_elements().with_attribute("role", re.compile(r"main|banner"))
    """
    return any_of(
        css_block_elements(),
        tag_in(*_HTML_BLOCK_STRUCTURE_ELEMENTS),
    )


@supports_attributes
def html_inline_elements() -> ElementPredicateFactory:
    """Match common HTML inline elements.

    Returns:
        An element predicate factory that matches common HTML inline elements
    """
    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            return element.tag in _HTML_INLINE_ELEMENTS

        return element_predicate

    return create_document_predicate


@supports_attributes
def html_void_elements() -> ElementPredicateFactory:
    """Match HTML void elements (self-closing).

    Returns:
        A chainable predicate factory that matches HTML void elements

    Examples:
        Basic usage:
            html_void_elements()

        With chaining (enabled by @supports_attributes):
            html_void_elements().with_attribute("src")
            html_void_elements().with_attribute("alt", re.compile(r".*logo.*"))
    """
    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            return element.tag in _HTML_VOID_ELEMENTS

        return element_predicate

    return create_document_predicate


@supports_attributes
def html_whitespace_significant_elements() -> ElementPredicateFactory:
    """Match elements where whitespace is significant.

    Returns:
        A chainable predicate factory that matches elements like pre, style, script where whitespace is significant

    Examples:
        Basic usage:
            html_whitespace_significant_elements()

        With chaining (enabled by @supports_attributes):
            html_whitespace_significant_elements().with_attribute("class")
            html_whitespace_significant_elements().with_attribute("id", "main-code")
    """
    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            return element.tag in _HTML_WHITESPACE_SIGNIFICANT_ELEMENTS

        return element_predicate

    return create_document_predicate


def html_normalize_whitespace() -> ElementPredicateFactory:
    """Match elements where whitespace should be normalized, excluding whitespace-significant elements and their descendants.

    This predicate is specifically designed for HTML formatting where whitespace normalization
    should NOT apply to elements like <pre>, <style>, <script>, <textarea>, <code> or any
    of their descendants. This ensures that syntax-highlighted code in <pre> blocks, inline
    code snippets, and other whitespace-sensitive content preserve their exact formatting.

    Returns:
        A predicate factory that matches elements where whitespace should be normalized

    Examples:
        Basic usage:
            # Use as default for Html5Formatter
            formatter = Html5Formatter(normalize_whitespace_when=html_normalize_whitespace())

        Custom combination:
            # Normalize whitespace except in pre and custom elements
            from markuplift.predicates import all_of, not_matching, tag_in
            normalize_when = all_of(
                html_normalize_whitespace(),
                not_matching(tag_in("custom-preserve"))
            )

    Note:
        This is the default for Html5Formatter, ensuring that whitespace in <pre> blocks
        and their descendants (like syntax-highlighted <span> elements) is preserved exactly.
    """
    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            # Check if element itself is whitespace-significant
            if element.tag in _HTML_WHITESPACE_SIGNIFICANT_ELEMENTS:
                return False

            # Check if any ancestor is whitespace-significant
            for ancestor in element.iterancestors():
                if ancestor.tag in _HTML_WHITESPACE_SIGNIFICANT_ELEMENTS:
                    return False

            return True

        return element_predicate

    return create_document_predicate


@supports_attributes
def html_metadata_elements() -> ElementPredicateFactory:
    """Match HTML metadata elements (head section).

    Returns:
        A chainable predicate factory that matches HTML head elements

    Examples:
        Basic usage:
            html_metadata_elements()

        With chaining (enabled by @supports_attributes):
            html_metadata_elements().with_attribute("charset")
            html_metadata_elements().with_attribute("name", "viewport")
    """
    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        def element_predicate(element: etree._Element) -> bool:
            return element.tag in _HTML_METADATA_ELEMENTS

        return element_predicate

    return create_document_predicate


@supports_attributes
def css_block_elements() -> ElementPredicateFactory:
    """Match HTML elements that browsers render as display: block by default.

    This predicate factory matches elements based on their default CSS display property
    as defined by browser user agent stylesheets, not MarkupLift's source formatting concepts.
    These elements create their own formatting context and are safe for whitespace stripping.

    Returns:
        An element predicate factory that matches elements with CSS display: block

    Examples:
        Basic usage:
            css_block_elements()

        With chaining (enabled by @supports_attributes):
            css_block_elements().with_attribute("class", "container")
            css_block_elements().with_attribute("id", re.compile(r"main|content"))
    """
    return tag_in(*_CSS_BLOCK_ELEMENTS)


# Combinator predicates
@supports_attributes
def any_of(*predicate_factories: ElementPredicateFactory) -> ElementPredicateFactory:
    """Match elements that satisfy any of the given predicates (OR logic).

    Args:
        *predicate_factories: Predicate factories to combine

    Returns:
        A chainable predicate factory that matches elements matching any of the input predicates

    Examples:
        Basic usage:
            # Match elements that are either div OR span tags
            any_of(tag_equals("div"), tag_equals("span"))

            # Match elements with class OR id attributes
            any_of(has_attribute("class"), has_attribute("id"))

        With chaining (enabled by @supports_attributes):
            # Match div or span elements that have a data attribute
            any_of(tag_equals("div"), tag_equals("span")).with_attribute("data-id")

            # Match block or inline elements with specific role
            any_of(html_block_elements(), html_inline_elements()).with_attribute("role", "button")
    """

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        predicates = [factory(root) for factory in predicate_factories]

        def element_predicate(element: etree._Element) -> bool:
            return any(pred(element) for pred in predicates)

        return element_predicate

    return create_document_predicate


@supports_attributes
def all_of(*predicate_factories: ElementPredicateFactory) -> ElementPredicateFactory:
    """Match elements that satisfy all of the given predicates (AND logic).

    Args:
        *predicate_factories: Predicate factories to combine

    Returns:
        A chainable predicate factory that matches elements matching all of the input predicates

    Examples:
        Basic usage:
            # Match div elements that also have a class attribute
            all_of(tag_equals("div"), has_attribute("class"))

            # Match elements with specific class AND data-type values
            all_of(
                attribute_equals("class", "button"),
                attribute_equals("data-type", "primary")
            )

        With chaining (enabled by @supports_attributes):
            # Match div elements with class that also have a style attribute
            all_of(tag_equals("div"), has_attribute("class")).with_attribute("style")

            # Match block elements with significant content that have data attributes
            all_of(html_block_elements(), has_significant_content()).with_attribute("data-id")
    """

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        predicates = [factory(root) for factory in predicate_factories]

        def element_predicate(element: etree._Element) -> bool:
            return all(pred(element) for pred in predicates)

        return element_predicate

    return create_document_predicate


@supports_attributes
def not_matching(predicate_factory: ElementPredicateFactory) -> ElementPredicateFactory:
    """Match elements that do NOT satisfy the given predicate (NOT logic).

    Args:
        predicate_factory: Predicate factory to negate

    Returns:
        A chainable predicate factory that matches elements NOT matching the input predicate

    Examples:
        Basic usage:
            # Match elements that are NOT div tags
            not_matching(tag_equals("div"))

            # Match elements that do NOT have a class attribute
            not_matching(has_attribute("class"))

            # Complex: Match elements that are NOT (div AND have class)
            not_matching(all_of(tag_equals("div"), has_attribute("class")))

        With chaining (enabled by @supports_attributes):
            # Match non-div elements that have a data attribute
            not_matching(tag_equals("div")).with_attribute("data-id")

            # Match elements that aren't block elements but have style attributes
            not_matching(html_block_elements()).with_attribute("style")
    """

    def create_document_predicate(root: etree._Element) -> ElementPredicate:
        predicate = predicate_factory(root)

        def element_predicate(element: etree._Element) -> bool:
            return not predicate(element)

        return element_predicate

    return create_document_predicate


# Standard predicates
def never_match(element: etree._Element) -> bool:
    """A standard predicate that never matches any element.

    This replaces the common pattern of lambda e: False throughout the codebase.

    Args:
        element: The XML element to test (ignored)

    Returns:
        Always returns False
    """
    return False


def never_matches(root: etree._Element) -> ElementPredicate:
    """A standard predicate factory that creates predicates that never match.

    This replaces the common pattern of lambda root: lambda e: False.

    Args:
        root: The document root element (ignored)

    Returns:
        An ElementPredicate that always returns False
    """
    return never_match


# Direct attribute functions for "any element" scenarios
def attribute_matches(name: NameMatcher, value: Optional[ValueMatcher] = None) -> AttributePredicateFactory:
    """Match attributes on any element by name and optionally by value.

    This function creates AttributePredicateFactory instances that match
    attributes regardless of which element they're on. Use this for
    general attribute matching across all elements.

    Note: This is different from has_attribute() which returns an ElementPredicateFactory
    for matching elements that have a specific attribute.

    Args:
        name: Attribute name matcher - can be:
            - str: Exact attribute name match
            - re.Pattern: Regex pattern for attribute name
            - Callable[[str], bool]: Custom function to test attribute name
        value: Optional attribute value matcher - can be:
            - str: Exact attribute value match
            - re.Pattern: Regex pattern for attribute value
            - Callable[[str], bool]: Custom function to test attribute value
            - None: Match any value (default)

    Returns:
        AttributePredicateFactory that matches the specified attribute

    Examples:
        # String matching
        attribute_matches("style")
        attribute_matches("class", "btn-primary")

        # Regex matching
        attribute_matches("href", re.compile(r".*\\.css$"))
        attribute_matches(re.compile(r"data-.*"), re.compile(r"^\\{.*\\}$"))

        # Function matching
        attribute_matches("style", lambda v: v.count(';') >= 3)  # Complex CSS
        attribute_matches("class", lambda v: "btn" in v)         # Button classes
        attribute_matches(lambda n: n.startswith("data-"), lambda v: len(v) > 10)  # Long data attrs
    """
    # Create matchers at factory creation time for better performance
    name_matcher = _create_matcher(name, "attribute_name", allow_none=False)
    value_matcher = _create_matcher(value, "attribute_value", allow_none=True)

    def factory(root: etree._Element) -> AttributePredicate:
        def predicate(element: etree._Element, attr_name: str, attr_value: str) -> bool:
            return name_matcher(attr_name) and value_matcher(attr_value)

        return predicate

    return factory


@supports_attributes
def any_element() -> ElementPredicateFactory:
    """Match all elements - useful with .with_attribute() chaining.

    This creates an ElementPredicateFactory that matches every element, which is
    primarily useful for chaining with attribute selection methods.

    Returns:
        ElementPredicateFactory that matches all elements

    Examples:
        # These are equivalent
        attribute_matches("style")
        any_element().with_attribute("style")

        # Useful for consistency in configuration
        any_element().with_attribute("data-config", re.compile(r"^\\{.*\\}$"))
    """
    return lambda root: lambda element: True


def pattern(regex: str) -> Pattern[str]:
    """Create a compiled regex pattern for attribute matching.

    This is a convenience function for users who prefer not to import
    the re module directly. The returned Pattern objects can be used
    anywhere NameMatcher or ValueMatcher is expected.

    Args:
        regex: Regular expression string to compile

    Returns:
        Compiled regex pattern

    Examples:
        attribute_matches("href", pattern(r".*\\.css$"))
        attribute_matches(pattern(r"data-.*"))
        tag_name("div").with_attribute("class", pattern(r".*btn.*"))
    """
    return re.compile(regex)
