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
from .html5_formatter import Html5Formatter
from .xml_formatter import XmlFormatter
from .doctype import DoctypeStrategy, Html5DoctypeStrategy, XmlDoctypeStrategy, NullDoctypeStrategy
from .attribute_formatting import (
    AttributeFormattingStrategy,
    Html5AttributeStrategy,
    XmlAttributeStrategy,
    NullAttributeStrategy,
    CssFormatter,
    css_formatter,
    css_property_order,
    defer_css_properties,
    prioritize_css_properties,
    reorder_css_properties,
    sort_css_properties,
    wrap_css_properties,
    sort_attributes,
    prioritize_attributes,
    defer_attributes,
    order_attributes,
    html_attribute_order,
)
from .types import (
    AttributePredicate,
    AttributePredicateFactory,
    AttributeValueFormatter,
    AttributeReorderer,
    CssPropertyTransformer,
    CssPropertyReorderer,
    ElementPredicate,
    ElementPredicateFactory,
    ElementType,
    NameMatcher,
    TextContent,
    TextContentFormatter,
    ValueMatcher,
)

# Legacy constants removed - use ElementType.BLOCK and ElementType.INLINE instead
from .predicates import (
    all_of,
    any_element,
    any_of,
    attribute_count_between,
    attribute_count_max,
    attribute_count_min,
    attribute_equals,
    attribute_matches,
    has_attribute,
    has_child_elements,
    has_class,
    has_mixed_content,
    has_no_significant_content,
    has_significant_content,
    css_block_elements,
    html_block_elements,
    html_inline_elements,
    html_metadata_elements,
    html_normalize_whitespace,
    html_void_elements,
    html_whitespace_significant_elements,
    is_comment,
    is_element,
    is_processing_instruction,
    matches_xpath,
    never_match,
    never_matches,
    not_matching,
    pattern,
    PredicateError,
    PredicateFactory,
    supports_attributes,
    tag_equals,
    tag_in,
    tag_name,
)

__all__ = [
    "all_of",
    "any_element",
    "any_of",
    "attribute_count_between",
    "attribute_count_max",
    "attribute_count_min",
    "attribute_equals",
    "attribute_matches",
    "AttributeFormattingStrategy",
    "AttributePredicate",
    "AttributePredicateFactory",
    "AttributeReorderer",
    "AttributeValueFormatter",
    "CssFormatter",
    "css_formatter",
    "css_property_order",
    "CssPropertyReorderer",
    "CssPropertyTransformer",
    "defer_attributes",
    "defer_css_properties",
    "DocumentFormatter",
    "DoctypeStrategy",
    "ElementPredicate",
    "ElementPredicateFactory",
    "ElementType",
    "Formatter",
    "has_attribute",
    "has_child_elements",
    "has_class",
    "has_mixed_content",
    "has_no_significant_content",
    "has_significant_content",
    "css_block_elements",
    "html_attribute_order",
    "html_block_elements",
    "html_inline_elements",
    "html_metadata_elements",
    "html_normalize_whitespace",
    "html_void_elements",
    "html_whitespace_significant_elements",
    "Html5AttributeStrategy",
    "Html5DoctypeStrategy",
    "Html5Formatter",
    "is_comment",
    "is_element",
    "is_processing_instruction",
    "matches_xpath",
    "NameMatcher",
    "never_match",
    "never_matches",
    "not_matching",
    "NullAttributeStrategy",
    "NullDoctypeStrategy",
    "order_attributes",
    "pattern",
    "PredicateError",
    "PredicateFactory",
    "prioritize_attributes",
    "prioritize_css_properties",
    "reorder_css_properties",
    "sort_attributes",
    "sort_css_properties",
    "supports_attributes",
    "tag_equals",
    "tag_in",
    "tag_name",
    "TextContent",
    "TextContentFormatter",
    "ValueMatcher",
    "wrap_css_properties",
    "XmlAttributeStrategy",
    "XmlDoctypeStrategy",
    "XmlFormatter",
]

from collections import namedtuple

Version = namedtuple("Version", ["major", "minor", "patch"])
__version__ = "4.4.0"
__version_info__ = Version(*(__version__.split(".")))
