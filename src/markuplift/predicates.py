"""Predicate factories for XML/HTML element matching.

This module provides a collection of predicate factory functions that create
optimized element matching predicates. All factories follow the same pattern:
they take configuration parameters and return a function that takes a document
root and returns an optimized predicate function.

The factory pattern ensures that expensive operations (like XPath evaluation)
are performed only once per document rather than once per element, providing
significant performance benefits.
"""

from lxml import etree
import click

# Import type aliases
from markuplift.types import ElementPredicateFactory


def matches_xpath(xpath_expr: str) -> ElementPredicateFactory:
    """Match elements using XPath expressions.

    Args:
        xpath_expr: XPath expression to evaluate

    Returns:
        An element predicate factory that creates optimized XPath-based predicates
    """
    def create_document_predicate(root: etree._Element):
        try:
            # Evaluate XPath once and store results as a set for O(1) lookups
            matches = set(root.xpath(xpath_expr))
        except etree.XPathEvalError as e:
            raise click.ClickException(f"Invalid XPath expression '{xpath_expr}': {e}")

        def element_predicate(element: etree._Element) -> bool:
            return element in matches

        return element_predicate

    return create_document_predicate


def tag_equals(tag: str) -> ElementPredicateFactory:
    """Match elements with a specific tag name.

    Args:
        tag: Tag name to match

    Returns:
        An element predicate factory that matches elements with the specified tag
    """
    def create_document_predicate(root: etree._Element):
        def element_predicate(element: etree._Element) -> bool:
            return element.tag == tag
        return element_predicate

    return create_document_predicate


def tag_in(*tags: str) -> ElementPredicateFactory:
    """Match elements with any of the specified tag names.

    Args:
        *tags: Tag names to match

    Returns:
        An element predicate factory that matches elements with any of the specified tags
    """
    tag_set = set(tags)

    def create_document_predicate(root: etree._Element):
        def element_predicate(element: etree._Element) -> bool:
            return element.tag in tag_set
        return element_predicate

    return create_document_predicate


def has_attribute(attr: str) -> ElementPredicateFactory:
    """Match elements that have a specific attribute.

    Args:
        attr: Attribute name to check for

    Returns:
        An element predicate factory that matches elements having the specified attribute
    """
    def create_document_predicate(root: etree._Element):
        def element_predicate(element: etree._Element) -> bool:
            if not attr:  # Handle empty attribute name
                return False
            try:
                return attr in element.attrib
            except ValueError:  # lxml raises ValueError for invalid attribute names
                return False
        return element_predicate

    return create_document_predicate


def attribute_equals(attr: str, value: str) -> ElementPredicateFactory:
    """Match elements with a specific attribute value.

    Args:
        attr: Attribute name to check
        value: Expected attribute value

    Returns:
        An element predicate factory that matches elements with the specified attribute value
    """
    def create_document_predicate(root: etree._Element):
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
    """
    def create_document_predicate(root: etree._Element):
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
    """
    def create_document_predicate(root: etree._Element):
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
    """
    def create_document_predicate(root: etree._Element):
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
    def create_document_predicate(root: etree._Element):
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
    """
    def create_document_predicate(root: etree._Element):
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
    def create_document_predicate(root: etree._Element):
        def element_predicate(element: etree._Element) -> bool:
            return isinstance(element, etree._Element) and not isinstance(element, (etree._Comment, etree._ProcessingInstruction))
        return element_predicate

    return create_document_predicate


# Content-based predicates
def has_significant_content() -> ElementPredicateFactory:
    """Match elements with non-whitespace text content.

    Returns:
        An element predicate factory that matches elements containing significant text
    """
    from markuplift.utilities import has_direct_significant_text

    def create_document_predicate(root: etree._Element):
        def element_predicate(element: etree._Element) -> bool:
            return has_direct_significant_text(element)
        return element_predicate

    return create_document_predicate


def has_no_significant_content() -> ElementPredicateFactory:
    """Match empty or whitespace-only elements.

    Returns:
        An element predicate factory that matches elements with no significant content
    """
    from markuplift.utilities import has_direct_significant_text

    def create_document_predicate(root: etree._Element):
        def element_predicate(element: etree._Element) -> bool:
            return not has_direct_significant_text(element)
        return element_predicate

    return create_document_predicate


def has_mixed_content() -> ElementPredicateFactory:
    """Match elements containing both text and child elements.

    Returns:
        An element predicate factory that matches elements in mixed content
    """
    from markuplift.utilities import is_in_mixed_content

    def create_document_predicate(root: etree._Element):
        def element_predicate(element: etree._Element) -> bool:
            return is_in_mixed_content(element)
        return element_predicate

    return create_document_predicate


def has_child_elements() -> ElementPredicateFactory:
    """Match elements that contain child elements.

    Returns:
        An element predicate factory that matches elements with child elements
    """
    def create_document_predicate(root: etree._Element):
        def element_predicate(element: etree._Element) -> bool:
            return len(element) > 0
        return element_predicate

    return create_document_predicate


# Domain-specific predicates
def html_block_elements() -> ElementPredicateFactory:
    """Match common HTML block elements.

    Returns:
        An element predicate factory that matches common HTML block elements
    """
    BLOCK_ELEMENTS = {
        "address", "article", "aside", "blockquote", "details", "dialog", "dd", "div",
        "dl", "dt", "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2",
        "h3", "h4", "h5", "h6", "header", "hgroup", "hr", "li", "main", "nav", "ol",
        "p", "pre", "section", "table", "tbody", "tfoot", "thead", "tr", "ul"
    }

    def create_document_predicate(root: etree._Element):
        def element_predicate(element: etree._Element) -> bool:
            return element.tag in BLOCK_ELEMENTS
        return element_predicate

    return create_document_predicate


def html_inline_elements() -> ElementPredicateFactory:
    """Match common HTML inline elements.

    Returns:
        An element predicate factory that matches common HTML inline elements
    """
    INLINE_ELEMENTS = {
        "a", "abbr", "b", "bdi", "bdo", "br", "cite", "code", "data", "dfn", "em",
        "i", "kbd", "mark", "q", "ruby", "s", "samp", "small", "span", "strong", "sub",
        "sup", "time", "u", "var", "wbr"
    }

    def create_document_predicate(root: etree._Element):
        def element_predicate(element: etree._Element) -> bool:
            return element.tag in INLINE_ELEMENTS
        return element_predicate

    return create_document_predicate


def html_void_elements() -> ElementPredicateFactory:
    """Match HTML void elements (self-closing).

    Returns:
        An element predicate factory that matches HTML void elements
    """
    VOID_ELEMENTS = {
        "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "param", "source", "track", "wbr"
    }

    def create_document_predicate(root: etree._Element):
        def element_predicate(element: etree._Element) -> bool:
            return element.tag in VOID_ELEMENTS
        return element_predicate

    return create_document_predicate


def whitespace_significant_elements() -> ElementPredicateFactory:
    """Match elements where whitespace is significant.

    Returns:
        An element predicate factory that matches elements like pre, style, script where whitespace is significant
    """
    WHITESPACE_SIGNIFICANT = {"pre", "style", "script", "textarea", "code"}

    def create_document_predicate(root: etree._Element):
        def element_predicate(element: etree._Element) -> bool:
            return element.tag in WHITESPACE_SIGNIFICANT
        return element_predicate

    return create_document_predicate


def html_metadata_elements() -> ElementPredicateFactory:
    """Match HTML metadata elements (head section).

    Returns:
        An element predicate factory that matches HTML head elements
    """
    METADATA_ELEMENTS = {"head", "title", "base", "link", "meta", "style", "script", "noscript"}

    def create_document_predicate(root: etree._Element):
        def element_predicate(element: etree._Element) -> bool:
            return element.tag in METADATA_ELEMENTS
        return element_predicate

    return create_document_predicate


# Combinator predicates
def any_of(*predicate_factories: ElementPredicateFactory) -> ElementPredicateFactory:
    """Match elements that satisfy any of the given predicates (OR logic).

    Args:
        *predicate_factories: Predicate factories to combine

    Returns:
        An element predicate factory that matches elements matching any of the input predicates

    Example:
        # Match elements that are either div OR span tags
        factory = any_of(tag_equals("div"), tag_equals("span"))

        # Match elements with class OR id attributes
        factory = any_of(has_attribute("class"), has_attribute("id"))
    """
    def create_document_predicate(root: etree._Element):
        predicates = [factory(root) for factory in predicate_factories]

        def element_predicate(element: etree._Element) -> bool:
            return any(pred(element) for pred in predicates)
        return element_predicate

    return create_document_predicate


def all_of(*predicate_factories: ElementPredicateFactory) -> ElementPredicateFactory:
    """Match elements that satisfy all of the given predicates (AND logic).

    Args:
        *predicate_factories: Predicate factories to combine

    Returns:
        An element predicate factory that matches elements matching all of the input predicates

    Example:
        # Match div elements that also have a class attribute
        factory = all_of(tag_equals("div"), has_attribute("class"))

        # Match elements with specific class AND data-type values
        factory = all_of(
            attribute_equals("class", "button"),
            attribute_equals("data-type", "primary")
        )
    """
    def create_document_predicate(root: etree._Element):
        predicates = [factory(root) for factory in predicate_factories]

        def element_predicate(element: etree._Element) -> bool:
            return all(pred(element) for pred in predicates)
        return element_predicate

    return create_document_predicate


def not_matching(predicate_factory: ElementPredicateFactory) -> ElementPredicateFactory:
    """Match elements that do NOT satisfy the given predicate (NOT logic).

    Args:
        predicate_factory: Predicate factory to negate

    Returns:
        An element predicate factory that matches elements NOT matching the input predicate

    Example:
        # Match elements that are NOT div tags
        factory = not_matching(tag_equals("div"))

        # Match elements that do NOT have a class attribute
        factory = not_matching(has_attribute("class"))

        # Complex: Match elements that are NOT (div AND have class)
        factory = not_matching(all_of(tag_equals("div"), has_attribute("class")))
    """
    def create_document_predicate(root: etree._Element):
        predicate = predicate_factory(root)

        def element_predicate(element: etree._Element) -> bool:
            return not predicate(element)
        return element_predicate

    return create_document_predicate