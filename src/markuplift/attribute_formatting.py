"""Attribute formatting strategies for different document types.

This module provides strategy pattern implementations for attribute formatting,
allowing different document types (HTML5, XML) to handle attributes according
to their specific formatting requirements while enabling user customizations
to layer on top of built-in behavior.

The strategy pattern enables composition where built-in formatting logic
(like HTML5 boolean attribute minimization) is applied first, followed by
user-defined custom formatters, without conflicts or coordination issues.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from lxml import etree

from markuplift.types import AttributePredicate, TextContentFormatter


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
        user_formatters: Dict[AttributePredicate, TextContentFormatter],
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
        user_formatters: Dict[AttributePredicate, TextContentFormatter],
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
        user_formatters: Dict[AttributePredicate, TextContentFormatter],
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
        user_formatters: Dict[AttributePredicate, TextContentFormatter],
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
