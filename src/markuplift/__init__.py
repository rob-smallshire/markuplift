"""MarkupLift - A configurable XML and HTML formatter.

MarkupLift provides flexible formatting of XML and HTML documents with configurable
predicates for block vs inline elements, whitespace handling, and custom text content
formatters. The package uses a factory pattern with ElementPredicateFactory functions
for optimal performance.

Main Classes:
    Formatter: High-level API for formatting documents
    DocumentFormatter: Low-level document-specific formatter

Example:
    from markuplift import Formatter
    from markuplift.predicates import tag_equals, html_block_elements

    formatter = Formatter(
        block_predicate_factory=html_block_elements(),
        inline_predicate_factory=tag_equals("span")
    )
    result = formatter.format_str("<div><span>content</span></div>")
"""

from .formatter import Formatter
from .document_formatter import DocumentFormatter
from .types import ElementPredicate, ElementPredicateFactory
from .annotation import INLINE_TYPE_ANNOTATION as INLINE_TYPE
from .annotation import BLOCK_TYPE_ANNOTATION as BLOCK_TYPE
from .predicates import (
    all_of,
    any_of,
    attribute_count_between,
    attribute_count_max,
    attribute_count_min,
    attribute_equals,
    has_attribute,
    has_child_elements,
    has_mixed_content,
    has_no_significant_content,
    has_significant_content,
    html_block_elements,
    html_inline_elements,
    html_metadata_elements,
    html_void_elements,
    html_whitespace_significant_elements,
    is_comment,
    is_element,
    is_processing_instruction,
    matches_xpath,
    not_matching,
    tag_equals,
    tag_in,
    PredicateError,
)

__all__ = [
    "DocumentFormatter",
    "Formatter",
    "ElementPredicate",
    "ElementPredicateFactory",
    "PredicateError",
    "INLINE_TYPE",
    "BLOCK_TYPE",
    "all_of",
    "any_of",
    "attribute_count_between",
    "attribute_count_max",
    "attribute_count_min",
    "attribute_equals",
    "has_attribute",
    "has_child_elements",
    "has_mixed_content",
    "has_no_significant_content",
    "has_significant_content",
    "html_block_elements",
    "html_inline_elements",
    "html_metadata_elements",
    "html_void_elements",
    "html_whitespace_significant_elements",
    "is_comment",
    "is_element",
    "is_processing_instruction",
    "matches_xpath",
    "not_matching",
    "tag_equals",
    "tag_in",
]

from collections import namedtuple

Version = namedtuple("Version", ["major", "minor", "patch"])
__version__ = "2.1.0"
__version_info__ = Version(*(__version__.split(".")))
