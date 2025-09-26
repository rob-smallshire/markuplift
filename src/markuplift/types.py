"""Type aliases for MarkupLift.

This module defines common type aliases used throughout the MarkupLift codebase
to improve readability, maintainability, and code quality.

Type Aliases:
    ElementPredicate: A function that tests an XML element and returns bool
    ElementPredicateFactory: A function that creates ElementPredicate instances
    TextContentFormatter: A function that formats element text content
    AttributePredicate: A function that tests an element's attribute and returns bool
    AttributePredicateFactory: A function that creates AttributePredicate instances
    NameMatcher: String, regex pattern, or custom function for matching attribute names
    ValueMatcher: String, regex pattern, or custom function for matching attribute values
"""

from typing import Callable, Union, TYPE_CHECKING
from re import Pattern
from lxml import etree

if TYPE_CHECKING:
    from markuplift.document_formatter import DocumentFormatter

# Type alias for element predicate functions
# The function takes an XML element (etree._Element) and returns a boolean.
ElementPredicate = Callable[[etree._Element], bool]

# Type alias for element predicate factory functions
# The function takes the document root (etree._Element) and returns an ElementPredicate.
ElementPredicateFactory = Callable[[etree._Element], ElementPredicate]

# Type alias for text content formatter functions
# The function takes the text content (str), the DocumentFormatter instance,
# and the current indentation level (int), and returns the formatted text (str).
TextContentFormatter = Callable[[str, "DocumentFormatter", int], str]

# Type aliases for attribute matching
# NameMatcher can be exact string match, regex pattern, or custom function for attribute names
NameMatcher = Union[str, Pattern[str], Callable[[str], bool]]

# ValueMatcher can be exact string match, regex pattern, or custom function for attribute values
ValueMatcher = Union[str, Pattern[str], Callable[[str], bool]]

# Type alias for attribute predicate functions
# The function takes an XML element, attribute name, and attribute value, and returns a boolean.
AttributePredicate = Callable[[etree._Element, str, str], bool]

# Type alias for attribute predicate factory functions
# The function takes the document root (etree._Element) and returns an AttributePredicate.
AttributePredicateFactory = Callable[[etree._Element], AttributePredicate]
