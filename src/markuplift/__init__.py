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

__all__ = [
    "Formatter",
    "DocumentFormatter"
]

from collections import namedtuple

Version = namedtuple("Version", ["major", "minor", "patch"])
__version__ = "2.0.1"
__version_info__ = Version(*(__version__.split(".")))
