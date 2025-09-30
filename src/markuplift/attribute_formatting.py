"""Attribute formatting strategies and formatters for different document types.

This module provides:
1. Strategy pattern implementations for attribute formatting (HTML5, XML)
2. Reusable text content formatters for common attribute value formatting needs
3. Reusable attribute reorderer factories for common attribute reordering needs

The strategy pattern enables composition where built-in formatting logic
(like HTML5 boolean attribute minimization) is applied first, followed by
user-defined custom formatters, without conflicts or coordination issues.
"""

from abc import ABC, abstractmethod
from graphlib import TopologicalSorter, CycleError
import re
from typing import Dict, Any, Sequence, Callable
from lxml import etree

from markuplift.types import (
    AttributePredicate,
    AttributeValueFormatter,
    AttributeReorderer,
    CssPropertyTransformer,
    CssPropertyReorderer,
)


class AttributeFormattingStrategy(ABC):
    """Abstract base class for attribute formatting strategies.
x
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


class CssFormatter:
    """Fluent builder for CSS property formatting with composable transformations.

    This class provides a fluent API for creating CSS attribute value formatters
    with support for property-level transformations, list-level reordering, and
    flexible wrapping control. The formatter can be used directly as an
    AttributeValueFormatter without needing a .build() method.

    The formatter applies transformations in this order:
    1. Parse CSS properties from the input string
    2. Apply property-level transformers (can add/remove/modify properties)
    3. Apply list-level reorderers (reorder the property list)
    4. Apply wrapping logic based on the wrap_when predicate
    5. Format and return the result

    Examples:
        >>> from markuplift import Html5Formatter, css_formatter
        >>> from markuplift.attribute_formatting import prioritize_css_properties
        >>> from markuplift.predicates import attribute_matches
        >>>
        >>> # Use directly as AttributeValueFormatter
        >>> formatter = Html5Formatter(
        ...     reformat_attribute_when={
        ...         attribute_matches("style"): (
        ...             css_formatter()
        ...             .reorder(prioritize_css_properties("display", "position"))
        ...             .wrap_when(lambda props: len(props) > 3)
        ...         )
        ...     }
        ... )
        >>>
        >>> # Reorder only (inline formatting)
        >>> css_formatter().reorder(sort_css_properties())
        >>>
        >>> # Wrap only (no reordering)
        >>> css_formatter().wrap_when(lambda props: len(props) > 2)
    """

    def __init__(self):
        """Initialize a new CssFormatter with default settings."""
        self._property_transformers: list[CssPropertyTransformer] = []
        self._reorderers: list[CssPropertyReorderer] = []
        self._wrap_predicate: Callable[[Sequence[str]], bool] | None = None

    def transform_properties(self, *transformers: CssPropertyTransformer) -> "CssFormatter":
        """Add property-level transformers for modifying individual CSS properties.

        Property transformers can add, remove, or modify CSS properties by taking
        a property name and value and returning a sequence of (name, value) tuples.

        Args:
            *transformers: One or more CssPropertyTransformer functions

        Returns:
            Self for method chaining

        Example:
            >>> def normalize_colors(name: str, value: str) -> Sequence[tuple[str, str]]:
            ...     if name in ('color', 'background-color'):
            ...         # normalize color format
            ...         return [(name, normalized_value)]
            ...     return [(name, value)]
            >>>
            >>> css_formatter().transform_properties(normalize_colors)
        """
        self._property_transformers.extend(transformers)
        return self

    def reorder(self, *reorderers: CssPropertyReorderer) -> "CssFormatter":
        """Add list-level reorderers for reordering CSS properties.

        Reorderers work on complete "name: value" property strings and determine
        the output order of properties.

        Args:
            *reorderers: One or more CssPropertyReorderer functions

        Returns:
            Self for method chaining

        Example:
            >>> from markuplift.attribute_formatting import (
            ...     prioritize_css_properties,
            ...     sort_css_properties
            ... )
            >>>
            >>> css_formatter().reorder(
            ...     prioritize_css_properties("display", "position"),
            ...     sort_css_properties()
            ... )
        """
        self._reorderers.extend(reorderers)
        return self

    def wrap_when(self, predicate: Callable[[Sequence[str]], bool]) -> "CssFormatter":
        """Set the wrapping predicate to control inline vs multi-line formatting.

        The predicate receives the list of CSS property strings (after all
        transformations and reordering) and returns True if properties should
        be wrapped on separate lines, False for inline formatting.

        Args:
            predicate: Function taking property list and returning bool

        Returns:
            Self for method chaining

        Example:
            >>> # Wrap when more than 3 properties
            >>> css_formatter().wrap_when(lambda props: len(props) > 3)
            >>>
            >>> # Never wrap (always inline)
            >>> css_formatter().wrap_when(lambda props: False)
        """
        self._wrap_predicate = predicate
        return self

    def __call__(self, value: str, formatter: Any, level: int) -> str:
        """Format CSS attribute value with configured transformations.

        This method makes CssFormatter directly usable as an AttributeValueFormatter.

        Args:
            value: The CSS style attribute value (e.g., "color: red; background: blue;")
            formatter: The formatter instance providing indentation context
            level: The indentation level of the attribute

        Returns:
            Formatted CSS value, either inline or multi-line depending on configuration
        """
        # Parse CSS properties, removing empty entries
        properties = [prop.strip() for prop in value.split(";") if prop.strip()]

        # Apply property-level transformers if any
        if self._property_transformers:
            transformed_properties = []
            for prop_str in properties:
                # Parse "name: value" format
                if ":" in prop_str:
                    name, val = prop_str.split(":", 1)
                    name = name.strip()
                    val = val.strip()

                    # Apply transformers
                    result_tuples: list[tuple[str, str]] = [(name, val)]
                    for transformer in self._property_transformers:
                        new_result: list[tuple[str, str]] = []
                        for n, v in result_tuples:
                            new_result.extend(transformer(n, v))
                        result_tuples = new_result

                    # Convert back to "name: value" strings
                    transformed_properties.extend([f"{n}: {v}" for n, v in result_tuples])
                else:
                    # Malformed property, keep as-is
                    transformed_properties.append(prop_str)

            properties = transformed_properties

        # Apply list-level reorderers
        for reorderer in self._reorderers:
            properties = list(reorderer(properties))

        # Determine wrapping
        should_wrap = self._wrap_predicate(properties) if self._wrap_predicate else False

        if not should_wrap:
            # Inline format
            return "; ".join(properties) + (";" if properties else "")

        # Multi-line format: properties indented one level deeper than attribute
        property_indent = formatter.one_indent * (level + 1)
        # Closing quote aligns with the attribute itself
        closing_indent = formatter.one_indent * level

        formatted_props = [f"\n{property_indent}{prop};" for prop in properties]
        return "".join(formatted_props) + f"\n{closing_indent}"


def css_formatter() -> CssFormatter:
    """Create a CSS property formatter with fluent API.

    Returns:
        A new CssFormatter instance that can be configured via fluent methods
        and used directly as an AttributeValueFormatter.

    Example:
        >>> from markuplift import Html5Formatter
        >>> from markuplift.attribute_formatting import css_formatter, sort_css_properties
        >>> from markuplift.predicates import attribute_matches
        >>>
        >>> formatter = Html5Formatter(
        ...     reformat_attribute_when={
        ...         attribute_matches("style"): (
        ...             css_formatter()
        ...             .reorder(sort_css_properties())
        ...             .wrap_when(lambda props: len(props) > 2)
        ...         )
        ...     }
        ... )
    """
    return CssFormatter()


# CSS property reorderers


def sort_css_properties() -> CssPropertyReorderer:
    """Sort CSS properties alphabetically by property name.

    Returns:
        A CssPropertyReorderer that sorts property strings alphabetically.

    Example:
        >>> from markuplift import Html5Formatter, css_formatter
        >>> from markuplift.attribute_formatting import sort_css_properties
        >>> from markuplift.predicates import attribute_matches
        >>>
        >>> formatter = Html5Formatter(
        ...     reformat_attribute_when={
        ...         attribute_matches("style"): (
        ...             css_formatter().reorder(sort_css_properties())
        ...         )
        ...     }
        ... )
        >>> html = '<div style="z-index: 1; color: red; background: blue;">'
        >>> formatter.format_str(html)
        # Output: <div style="background: blue; color: red; z-index: 1;">
    """

    def reorderer(properties: Sequence[str]) -> Sequence[str]:
        # Extract property name (part before ':') for sorting
        def get_property_name(prop: str) -> str:
            return prop.split(":", 1)[0].strip().lower() if ":" in prop else prop.lower()

        return sorted(properties, key=get_property_name)

    return reorderer


def prioritize_css_properties(*priority_names: str) -> CssPropertyReorderer:
    """Prioritize specific CSS properties to appear first, others maintain original order.

    Args:
        *priority_names: CSS property names to place first, in the order specified.
                        Property names are case-insensitive. Properties not in this
                        list maintain their original relative order.

    Returns:
        A CssPropertyReorderer that places priority properties first.

    Example:
        >>> from markuplift import Html5Formatter, css_formatter
        >>> from markuplift.attribute_formatting import prioritize_css_properties
        >>> from markuplift.predicates import attribute_matches
        >>>
        >>> formatter = Html5Formatter(
        ...     reformat_attribute_when={
        ...         attribute_matches("style"): (
        ...             css_formatter().reorder(
        ...                 prioritize_css_properties("display", "position", "width", "height")
        ...             )
        ...         )
        ...     }
        ... )
        >>> html = '<div style="color: red; width: 100px; background: blue; display: flex;">'
        >>> formatter.format_str(html)
        # Output: <div style="display: flex; width: 100px; color: red; background: blue;">
    """

    # Normalize priority names to lowercase for case-insensitive matching
    priority_names_lower = [name.lower() for name in priority_names]

    def reorderer(properties: Sequence[str]) -> Sequence[str]:
        def get_property_name(prop: str) -> str:
            return prop.split(":", 1)[0].strip().lower() if ":" in prop else prop.lower()

        # Separate priority and rest properties
        priority_props = []
        rest_props = []

        for prop in properties:
            prop_name = get_property_name(prop)
            if prop_name in priority_names_lower:
                priority_props.append(prop)
            else:
                rest_props.append(prop)

        # Sort priority properties by their position in priority_names
        priority_props.sort(key=lambda p: priority_names_lower.index(get_property_name(p)))

        return priority_props + rest_props

    return reorderer


def defer_css_properties(*trailing_names: str) -> CssPropertyReorderer:
    """Defer specific CSS properties to appear last, others maintain original order.

    Args:
        *trailing_names: CSS property names to place last. Property names are
                        case-insensitive. Other properties maintain their original
                        relative order.

    Returns:
        A CssPropertyReorderer that defers specified properties to the end.

    Example:
        >>> from markuplift import Html5Formatter, css_formatter
        >>> from markuplift.attribute_formatting import defer_css_properties
        >>> from markuplift.predicates import attribute_matches
        >>>
        >>> formatter = Html5Formatter(
        ...     reformat_attribute_when={
        ...         attribute_matches("style"): (
        ...             css_formatter().reorder(
        ...                 defer_css_properties("opacity", "z-index")
        ...             )
        ...         )
        ...     }
        ... )
        >>> html = '<div style="z-index: 10; color: red; width: 100px; opacity: 0.5;">'
        >>> formatter.format_str(html)
        # Output: <div style="color: red; width: 100px; z-index: 10; opacity: 0.5;">
    """

    # Normalize trailing names to lowercase for case-insensitive matching
    trailing_names_lower = [name.lower() for name in trailing_names]

    def reorderer(properties: Sequence[str]) -> Sequence[str]:
        def get_property_name(prop: str) -> str:
            return prop.split(":", 1)[0].strip().lower() if ":" in prop else prop.lower()

        # Separate rest and trailing properties
        rest_props = []
        trailing_props = []

        for prop in properties:
            prop_name = get_property_name(prop)
            if prop_name in trailing_names_lower:
                trailing_props.append(prop)
            else:
                rest_props.append(prop)

        return rest_props + trailing_props

    return reorderer


def css_property_order() -> CssPropertyReorderer:
    """Order CSS properties with topologically sorted CSS variables first, then semantic ordering.

    This reorderer provides sophisticated CSS property ordering that handles:
    1. CSS custom properties (--*) with dependency resolution via topological sorting
    2. Normal properties ordered by semantic categories (layout → box model → typography → visual → transitions)
    3. Alphabetical sorting within each category for unlisted properties

    CSS Variable Dependencies:
        When CSS variables reference other variables (e.g., --color: var(--primary)), they must
        be defined in dependency order. This function uses topological sorting to ensure variables
        appear before any variables that depend on them. Handles nested var() references and
        fallback values. If circular dependencies are detected, falls back to original order.

    Property Categories:
        0. Layout: display, position, top, right, bottom, left, float, clear, z-index
        1. Box model: width, height, margin, padding, border, box-sizing
        2. Typography: font-*, font-family, font-size, font-weight, line-height, color, text-align, text-decoration
        3. Visual: background-*, background-color, background-image, box-shadow, opacity
        4. Transitions: transition, transform, animation

    Returns:
        A CssPropertyReorderer that orders properties with variables first (dependency-sorted),
        followed by normal properties in semantic order.

    Example:
        >>> from markuplift import Html5Formatter, css_formatter
        >>> from markuplift.attribute_formatting import css_property_order
        >>> from markuplift.predicates import attribute_matches
        >>>
        >>> # With CSS variables
        >>> formatter = Html5Formatter(
        ...     reformat_attribute_when={
        ...         attribute_matches("style"): (
        ...             css_formatter().reorder(css_property_order())
        ...         )
        ...     }
        ... )
        >>> html = '<div style="color: var(--text); --text: var(--primary); --primary: red;">'
        >>> formatter.format_str(html)
        # Output: <div style="--primary: red; --text: var(--primary); color: var(--text);">
        # Variables ordered by dependency, then normal properties
    """

    def reorderer(properties: Sequence[str]) -> Sequence[str]:
        # Parse "name: value" strings into dict
        props_dict: Dict[str, str] = {}
        for prop in properties:
            if ":" in prop:
                # Handle CSS variables which have "--" at the start
                parts = prop.split(":", 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    value = parts[1].strip()
                    props_dict[name] = value
            # Skip malformed properties (no colon)

        # --- Step 1: Separate custom properties and normal properties ---
        custom_props = {k: v for k, v in props_dict.items() if k.startswith("--")}
        normal_props = {k: v for k, v in props_dict.items() if not k.startswith("--")}

        # --- Step 2: Build dependency graph for custom properties ---
        dep_graph: Dict[str, set[str]] = {}
        var_ref_pattern = re.compile(r"var\(\s*(--[\w-]+)")

        # Initialize all custom properties in the graph (even with no dependencies)
        for k in custom_props:
            dep_graph[k] = set()

        # Add dependencies
        for k, v in custom_props.items():
            deps = var_ref_pattern.findall(v)
            for d in deps:
                if d in custom_props:  # only include dependencies among defined vars
                    dep_graph[k].add(d)

        # --- Step 3: Topological sort ---
        ts = TopologicalSorter(dep_graph)
        try:
            sorted_vars = [(k, custom_props[k]) for k in ts.static_order()]
        except CycleError:
            # fallback: preserve original order if there is a cycle
            sorted_vars = list(custom_props.items())

        # --- Step 4: Order normal properties by semantic categories ---
        order_groups = [
            ["display", "position", "top", "right", "bottom", "left", "float", "clear", "z-index"],
            ["width", "height", "margin", "padding", "border", "box-sizing"],
            [
                "font",
                "font-family",
                "font-size",
                "font-weight",
                "line-height",
                "color",
                "text-align",
                "text-decoration",
            ],
            [
                "background",
                "background-color",
                "background-image",
                "background-size",
                "background-position",
                "box-shadow",
                "opacity",
            ],
            ["transition", "transform", "animation"],
        ]
        priority = {prop: i for i, group in enumerate(order_groups) for prop in group}
        default_priority = len(order_groups)

        sorted_normal = sorted(normal_props.items(), key=lambda kv: (priority.get(kv[0], default_priority), kv[0]))

        # --- Step 5: Concatenate and convert back to "name: value" format ---
        ordered_tuples = sorted_vars + sorted_normal
        return [f"{name}: {value}" for name, value in ordered_tuples]

    return reorderer


def wrap_css_properties(*reorderers: CssPropertyReorderer, when_more_than: int = 0) -> AttributeValueFormatter:
    """Create a formatter that wraps CSS style attributes with optional property reordering.

    This formatter wraps CSS properties on separate lines when the property count exceeds
    the threshold. Optionally, properties can be reordered before wrapping using one or
    more CssPropertyReorderer functions.

    Args:
        *reorderers: Zero or more CssPropertyReorderer functions to apply before wrapping.
                    Reorderers are applied in the order specified.
        when_more_than: Wrap CSS properties when count exceeds this value (exclusive).
                       For example, when_more_than=2 wraps styles with 3+ properties.
                       Default is 0 (wraps all multi-property styles with 1+ properties).

    Returns:
        An AttributeValueFormatter function that can be used with reformat_attribute_when

    Example:
        >>> from markuplift import Html5Formatter, wrap_css_properties
        >>> from markuplift.attribute_formatting import sort_css_properties
        >>> from markuplift.predicates import attribute_matches
        >>>
        >>> # Basic wrapping (no reordering)
        >>> formatter = Html5Formatter(
        ...     reformat_attribute_when={
        ...         attribute_matches("style"): wrap_css_properties(when_more_than=2)
        ...     }
        ... )
        >>>
        >>> # Wrap with reordering
        >>> formatter = Html5Formatter(
        ...     reformat_attribute_when={
        ...         attribute_matches("style"): wrap_css_properties(
        ...             sort_css_properties(),
        ...             when_more_than=2
        ...         )
        ...     }
        ... )

    Note:
        When used with wrap_attributes_when, the formatter automatically receives
        the correct indentation level accounting for the wrapped attributes.
    """
    # Build CssFormatter with the specified configuration
    css_fmt = css_formatter()

    # Add reorderers if any
    if reorderers:
        css_fmt = css_fmt.reorder(*reorderers)

    # Set wrapping predicate
    css_fmt = css_fmt.wrap_when(lambda props: len(props) > when_more_than)

    return css_fmt


def reorder_css_properties(*reorderers: CssPropertyReorderer) -> AttributeValueFormatter:
    """Create a formatter that reorders CSS properties without wrapping (inline format).

    This formatter reorders CSS properties according to the specified reorderers but
    keeps the result in inline format (properties separated by semicolons on one line).
    Useful when you want consistent property ordering without multi-line formatting.

    Args:
        *reorderers: One or more CssPropertyReorderer functions to apply.
                    Reorderers are applied in the order specified.

    Returns:
        An AttributeValueFormatter function that can be used with reformat_attribute_when

    Example:
        >>> from markuplift import Html5Formatter
        >>> from markuplift.attribute_formatting import (
        ...     reorder_css_properties,
        ...     prioritize_css_properties
        ... )
        >>> from markuplift.predicates import attribute_matches
        >>>
        >>> formatter = Html5Formatter(
        ...     reformat_attribute_when={
        ...         attribute_matches("style"): reorder_css_properties(
        ...             prioritize_css_properties("display", "position")
        ...         )
        ...     }
        ... )
        >>> html = '<div style="color: red; display: flex; position: relative;">'
        >>> formatter.format_str(html)
        # Output: <div style="display: flex; position: relative; color: red;">
    """
    # Build CssFormatter that never wraps (always inline)
    css_fmt = css_formatter().reorder(*reorderers).wrap_when(lambda props: False)
    return css_fmt


# Reusable attribute reorderer factories


def sort_attributes() -> AttributeReorderer:
    """Sort attributes alphanumerically by name.

    Returns:
        An AttributeReorderer that sorts attribute names in alphanumeric order.

    Example:
        >>> from markuplift import Html5Formatter, sort_attributes
        >>> from markuplift.predicates import any_element
        >>>
        >>> formatter = Html5Formatter(
        ...     reorder_attributes_when={
        ...         any_element(): sort_attributes()
        ...     }
        ... )
        >>> html = '<div role="main" id="content" class="wrapper">'
        >>> formatter.format_str(html)
        # Output: <div class="wrapper" id="content" role="main">
    """

    def orderer(names: Sequence[str]) -> Sequence[str]:
        return sorted(names)

    return orderer


def prioritize_attributes(*priority_names: str) -> AttributeReorderer:
    """Prioritize specific attributes to appear first, others follow in original order.

    Args:
        *priority_names: Attribute names to place first, in the order specified.
                        Attributes not in this list maintain their original relative order.

    Returns:
        An AttributeReorderer that places priority attributes first.

    Example:
        >>> from markuplift import Html5Formatter, prioritize_attributes
        >>> from markuplift.predicates import tag_name
        >>>
        >>> formatter = Html5Formatter(
        ...     reorder_attributes_when={
        ...         tag_name("input"): prioritize_attributes("name", "id", "type")
        ...     }
        ... )
        >>> html = '<input value="test" class="form-control" type="text" name="username" id="user">'
        >>> formatter.format_str(html)
        # Output: <input name="username" id="user" type="text" value="test" class="form-control">
    """

    def orderer(names: Sequence[str]) -> Sequence[str]:
        priority = [n for n in priority_names if n in names]
        rest = [n for n in names if n not in priority_names]
        return priority + rest

    return orderer


def defer_attributes(*trailing_names: str) -> AttributeReorderer:
    """Defer specific attributes to appear last, others maintain original order.

    Args:
        *trailing_names: Attribute names to place last. Other attributes
                        maintain their original relative order.

    Returns:
        An AttributeReorderer that defers specified attributes to the end.

    Example:
        >>> from markuplift import Html5Formatter, defer_attributes
        >>> from markuplift.predicates import tag_name
        >>>
        >>> formatter = Html5Formatter(
        ...     reorder_attributes_when={
        ...         tag_name("button"): defer_attributes("data-track", "aria-label")
        ...     }
        ... )
        >>> html = '<button data-track="click" class="btn" id="submit" aria-label="Submit form">Submit</button>'
        >>> formatter.format_str(html)
        # Output: <button class="btn" id="submit" data-track="click" aria-label="Submit form">Submit</button>
    """

    def orderer(names: Sequence[str]) -> Sequence[str]:
        rest = [n for n in names if n not in trailing_names]
        trailing = [n for n in names if n in trailing_names]
        return rest + trailing

    return orderer


def order_attributes(*ordered_names: str) -> AttributeReorderer:
    """Order attributes according to specified sequence, then sort remaining alphanumerically.

    Args:
        *ordered_names: Attribute names in desired order. Attributes not specified
                       will be sorted alphanumerically and placed after.

    Returns:
        An AttributeReorderer that orders attributes per specification, then sorts remainder.

    Example:
        >>> from markuplift import Html5Formatter, order_attributes
        >>> from markuplift.predicates import tag_name
        >>>
        >>> formatter = Html5Formatter(
        ...     reorder_attributes_when={
        ...         tag_name("a"): order_attributes("href", "title", "target")
        ...     }
        ... )
        >>> html = '<a target="_blank" rel="noopener" href="/page" title="Link" class="link">Click</a>'
        >>> formatter.format_str(html)
        # Output: <a href="/page" title="Link" target="_blank" class="link" rel="noopener">
        #         (href, title, target first as specified, then class and rel sorted)
    """

    def orderer(names: Sequence[str]) -> Sequence[str]:
        ordered = [n for n in ordered_names if n in names]
        unspecified = sorted(n for n in names if n not in ordered_names)
        return ordered + unspecified

    return orderer


def html_attribute_order() -> AttributeReorderer:
    """Order HTML attributes according to a semantic priority hierarchy.

    Orders attributes into these priority categories, preserving original order within each:
    0. id - unique identifier (highest priority)
    1. name - form element name
    2. class - CSS class names
    3. References/URLs - href, src, action (resource location)
    4. Behavior/events - on* event handlers
    5. Semantic/accessibility - alt, title, aria-*, role
    6. Custom/data - data-* and other unknown attributes
    7. style - inline styles (lowest priority)

    This ordering follows common HTML conventions where identity and classification
    come first, followed by resource references, then behavior, accessibility, custom
    attributes, and finally presentation.

    Returns:
        An AttributeReorderer that orders attributes by semantic category.

    Example:
        >>> from markuplift import Html5Formatter, html_attribute_order
        >>> from markuplift.predicates import any_element
        >>>
        >>> formatter = Html5Formatter(
        ...     reorder_attributes_when={
        ...         any_element(): html_attribute_order()
        ...     }
        ... )
        >>> html = '<img style="border:0" alt="Logo" class="logo" src="/logo.png" id="main-logo">'
        >>> formatter.format_str(html)
        # Output: <img id="main-logo" class="logo" src="/logo.png" alt="Logo" style="border:0">
    """

    def category(attr: str) -> int:
        """Determine the priority category for an attribute."""
        attr_lower = attr.lower()
        if attr_lower == "id":
            return 0
        elif attr_lower == "name":
            return 1
        elif attr_lower == "class":
            return 2
        elif attr_lower in ("href", "src", "action"):
            return 3
        elif attr_lower.startswith("on"):
            return 4
        elif attr_lower in ("alt", "title", "role") or attr_lower.startswith("aria-"):
            return 5
        elif attr_lower == "style":
            return 7
        else:
            return 6  # data-* or other unknown attributes

    def orderer(names: Sequence[str]) -> Sequence[str]:
        # Stable sort by category - preserves original order within categories
        return sorted(names, key=category)

    return orderer
