"""Attribute formatting strategies and formatters for different document types.

This module provides:
1. Strategy pattern implementations for attribute formatting (HTML5, XML)
2. Reusable text content formatters for common attribute value formatting needs

The strategy pattern enables composition where built-in formatting logic
(like HTML5 boolean attribute minimization) is applied first, followed by
user-defined custom formatters, without conflicts or coordination issues.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from lxml import etree

from markuplift.types import AttributePredicate, AttributeValueFormatter


class AttributeFormattingStrategy(ABC):
    """Abstract base class for attribute formatting strategies.

    Strategies handle format-specific attribute formatting rules while
    supporting user customizations through layered composition.
    """

    @abstractmethod
    def format_attribute(
        self,
        element: etree._Element,
        attr_name: str,
        attr_value: str,
        user_formatters: Dict[AttributePredicate, AttributeValueFormatter],
        formatter: Any,
        level: int,
    ) -> tuple[str, bool]:
        """Format an attribute value using strategy-specific rules and user customizations.

        Args:
            element: The element containing the attribute
            attr_name: Name of the attribute being formatted
            attr_value: Current value of the attribute
            user_formatters: Dictionary of user-defined attribute formatters
            formatter: The formatter instance (for context)
            level: Current nesting level (for indentation)

        Returns:
            Tuple of (formatted_value, should_minimize)
            - formatted_value: The processed attribute value
            - should_minimize: True if attribute should be rendered without value (e.g., <input checked>)
        """
        pass


class NullAttributeStrategy(AttributeFormattingStrategy):
    """Default strategy that applies only user formatters with no built-in logic.

    This maintains the current behavior for the regular Formatter class,
    ensuring backward compatibility.
    """

    def format_attribute(
        self,
        element: etree._Element,
        attr_name: str,
        attr_value: str,
        user_formatters: Dict[AttributePredicate, AttributeValueFormatter],
        formatter: Any,
        level: int,
    ) -> tuple[str, bool]:
        """Apply only user-defined formatters, no built-in formatting logic."""
        value = attr_value

        # Apply user formatters
        for predicate, formatter_func in user_formatters.items():
            if predicate(element, attr_name, value):
                value = formatter_func(value, formatter, level)
                break

        # Never minimize in null strategy
        return value, False


class XmlAttributeStrategy(AttributeFormattingStrategy):
    """XML-specific attribute formatting strategy.

    Applies standard XML attribute formatting rules, then layers
    user customizations on top.
    """

    def format_attribute(
        self,
        element: etree._Element,
        attr_name: str,
        attr_value: str,
        user_formatters: Dict[AttributePredicate, AttributeValueFormatter],
        formatter: Any,
        level: int,
    ) -> tuple[str, bool]:
        """Apply XML formatting rules followed by user customizations."""
        # For XML, we don't have special built-in rules yet
        # This is where XML-specific logic would go in the future
        value = attr_value

        # Apply user formatters
        for predicate, formatter_func in user_formatters.items():
            if predicate(element, attr_name, value):
                value = formatter_func(value, formatter, level)
                break

        # XML never minimizes attributes
        return value, False


class Html5AttributeStrategy(AttributeFormattingStrategy):
    """HTML5-specific attribute formatting strategy.

    Applies HTML5 attribute formatting rules (like boolean attribute minimization)
    followed by user customizations.
    """

    # HTML5 boolean attributes that should be minimized
    BOOLEAN_ATTRIBUTES = {
        "async",
        "autofocus",
        "autoplay",
        "checked",
        "controls",
        "default",
        "defer",
        "disabled",
        "formnovalidate",
        "hidden",
        "ismap",
        "itemscope",
        "loop",
        "multiple",
        "muted",
        "nomodule",
        "novalidate",
        "open",
        "readonly",
        "required",
        "reversed",
        "selected",
    }

    def format_attribute(
        self,
        element: etree._Element,
        attr_name: str,
        attr_value: str,
        user_formatters: Dict[AttributePredicate, AttributeValueFormatter],
        formatter: Any,
        level: int,
    ) -> tuple[str, bool]:
        """Apply HTML5 formatting rules followed by user customizations."""
        value = attr_value
        should_minimize = False

        # Apply HTML5-specific formatting rules first
        if attr_name in self.BOOLEAN_ATTRIBUTES:
            value = self._format_boolean_attribute(attr_value)
            should_minimize = True  # HTML5 boolean attributes should be minimized

        # Apply user formatters on top
        for predicate, formatter_func in user_formatters.items():
            if predicate(element, attr_name, value):
                value = formatter_func(value, formatter, level)
                # Note: User formatters can change the value but minimization decision
                # is based on the original HTML5 boolean attribute status
                break

        return value, should_minimize

    def _format_boolean_attribute(self, attr_value: str) -> str:
        """Format boolean attributes according to HTML5 rules.

        HTML5 boolean attributes should be minimized:
        - checked="checked" → "" (minimized form)
        - disabled="true" → "" (minimized form)
        - hidden="" → "" (minimized form)

        Args:
            attr_value: The current attribute value

        Returns:
            Empty string for minimized boolean attributes
        """
        # In HTML5, presence of boolean attribute = true, absence = false
        # We minimize to empty string, which lxml will render as <input checked>
        return ""


# Reusable attribute value formatters


def wrap_css_properties(when_more_than: int = 0) -> AttributeValueFormatter:
    """Create a formatter that wraps CSS style attributes with multiple properties on separate lines.

    This formatter is useful for HTML style attributes that contain many CSS properties.
    Properties are indented one level deeper than the attribute itself, making long
    style attributes more readable.

    Args:
        when_more_than: Wrap CSS properties when count exceeds this value (exclusive).
                       For example, when_more_than=2 wraps styles with 3+ properties.
                       Default is 0 (wraps all multi-property styles with 1+ properties).

    Returns:
        An AttributeValueFormatter function that can be used with reformat_attribute_when

    Example:
        >>> from markuplift import Html5Formatter, wrap_css_properties
        >>> from markuplift.predicates import attribute_matches, tag_name
        >>>
        >>> formatter = Html5Formatter(
        ...     wrap_attributes_when=tag_name("button"),
        ...     reformat_attribute_when={
        ...         attribute_matches("style"): wrap_css_properties()  # wraps all styles
        ...     }
        ... )

    Note:
        When used with wrap_attributes_when, the formatter automatically receives
        the correct indentation level accounting for the wrapped attributes.
    """

    def format_css_value(value: str, formatter: Any, level: int) -> str:
        """Format CSS value with properties on separate lines if threshold is exceeded.

        Args:
            value: The CSS style attribute value (e.g., "color: red; background: blue;")
            formatter: The formatter instance providing indentation context
            level: The indentation level of the attribute (accounting for wrapped attributes)

        Returns:
            Formatted CSS value, either inline or multi-line depending on property count
        """
        # Parse CSS properties, removing empty entries
        properties = [prop.strip() for prop in value.split(";") if prop.strip()]

        # Keep short styles inline (when property count <= when_more_than)
        if len(properties) <= when_more_than:
            return value

        # Multi-line format: properties indented one level deeper than attribute
        property_indent = formatter.one_indent * (level + 1)
        # Closing quote aligns with the attribute itself
        closing_indent = formatter.one_indent * level

        formatted_props = [f"\n{property_indent}{prop};" for prop in properties]
        return "".join(formatted_props) + f"\n{closing_indent}"

    return format_css_value
