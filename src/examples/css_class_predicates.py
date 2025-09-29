"""Custom CSS class predicate examples for MarkupLift.

This module demonstrates how to create custom element predicates
that match elements based on CSS class attributes.
"""

from markuplift.predicates import PredicateError
from markuplift.types import ElementPredicateFactory, ElementPredicate


def has_css_class(class_name: str) -> ElementPredicateFactory:
    """Factory for predicate matching elements with a specific CSS class.

    This demonstrates the triple-nested function pattern used by MarkupLift
    for efficient document-specific predicate optimization.

    Args:
        class_name: The CSS class name to match (without spaces)

    Returns:
        ElementPredicateFactory that creates optimized predicates

    Raises:
        PredicateError: If class_name is empty or contains spaces

    Example:
        >>> formatter = Formatter(
        ...     preserve_whitespace_when=has_css_class("code-block")
        ... )
    """
    # Level 1: Configuration and validation
    if not class_name or not class_name.strip():
        raise PredicateError("CSS class name cannot be empty")
    if " " in class_name:
        raise PredicateError("CSS class name cannot contain spaces")

    clean_class = class_name.strip()

    def create_document_predicate(root) -> ElementPredicate:
        # Level 2: Document-specific preparation - find all matching elements once
        matching_elements = set()
        for element in root.iter():
            class_attr = element.get("class", "")
            if class_attr and clean_class in class_attr.split():
                matching_elements.add(element)

        def element_predicate(element) -> bool:
            # Level 3: Fast membership test
            return element in matching_elements

        return element_predicate

    return create_document_predicate
