"""Type aliases for MarkupLift.

This module defines common type aliases used throughout the MarkupLift codebase
to improve readability, maintainability, and code quality.

Type Aliases:
    ElementPredicate: A function that tests an XML element and returns bool
    ElementPredicateFactory: A function that creates ElementPredicate instances
    TextContent: Union of string and CDATA for element text content
    TextContentFormatter: A function that formats element text content
    AttributePredicate: A function that tests an element's attribute and returns bool
    AttributePredicateFactory: A function that creates AttributePredicate instances
    NameMatcher: String, regex pattern, or custom function for matching attribute names
    ValueMatcher: String, regex pattern, or custom function for matching attribute values
"""

from typing import Callable, Union, TYPE_CHECKING, Protocol
from re import Pattern
from enum import Enum
from lxml import etree
from lxml.etree import CDATA

if TYPE_CHECKING:
    from markuplift.document_formatter import DocumentFormatter


class ElementType(Enum):
    """Enumeration for element types used in document formatting.

    This enum defines the valid element types that can be used as the default_type
    parameter in formatters and for element classification during formatting.

    Values:
        BLOCK: Block-level elements that introduce line breaks
        INLINE: Inline elements that flow with text content
    """

    BLOCK = "block"
    INLINE = "inline"


# Type alias for element predicate functions
# The function takes an XML element (etree._Element) and returns a boolean.
ElementPredicate = Callable[[etree._Element], bool]


# Protocol for element predicate factory functions
# Supports both function types and PredicateFactory class instances
class ElementPredicateFactory(Protocol):
    """Protocol for objects that can create ElementPredicate functions.

    This protocol allows both function types and PredicateFactory class instances
    to be used interchangeably, supporting proper structural typing.
    """

    def __call__(self, root: etree._Element) -> ElementPredicate: ...


# Type alias for text content that can be either string or CDATA
TextContent = Union[str, CDATA]

# Type alias for text content formatter functions
# The function takes the text content (TextContent), the DocumentFormatter instance,
# and the current indentation level (int), and returns the formatted text (TextContent).
TextContentFormatter = Callable[[TextContent, "DocumentFormatter", int], TextContent]

# Type aliases for attribute matching
# NameMatcher can be exact string match, regex pattern, or custom function for attribute names
NameMatcher = Union[str, Pattern[str], Callable[[str], bool]]

# ValueMatcher can be exact string match, regex pattern, or custom function for attribute values
ValueMatcher = Union[str, Pattern[str], Callable[[str], bool]]

# Type alias for attribute predicate functions
# The function takes an XML element, attribute name, and attribute value, and returns a boolean.
AttributePredicate = Callable[[etree._Element, str, str], bool]


# Protocol for attribute predicate factory functions
# Supports both function types and callable classes that create AttributePredicate functions
class AttributePredicateFactory(Protocol):
    """Protocol for objects that can create AttributePredicate functions.

    This protocol allows both function types and callable class instances
    to be used interchangeably, supporting proper structural typing.
    """

    def __call__(self, root: etree._Element) -> AttributePredicate: ...
