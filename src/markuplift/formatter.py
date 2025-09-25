"""High-level XML/HTML document formatter.

This module provides the main Formatter class, which serves as the public API
for formatting XML and HTML documents. The Formatter uses ElementPredicateFactory
functions to create optimized, document-specific predicates that determine how
elements should be formatted.

The Formatter delegates the actual formatting work to DocumentFormatter instances,
which are created with concrete ElementPredicate functions for optimal performance.
"""

from typing import Optional
from io import BytesIO
from xml.sax.saxutils import escape

from les_iterables import flatten
from lxml import etree

from markuplift.document_formatter import DocumentFormatter
from markuplift.annotation import (
    BLOCK_TYPES,
)

# Import type aliases
from markuplift.types import ElementPredicateFactory, TextContentFormatter
# Import standard predicates
from markuplift.predicates import never_matches


class Formatter:
    """A configurable formatter for XML documents using ElementPredicateFactory functions.

    The Formatter class provides a flexible and extensible way to pretty-print and normalize
    XML documents. It uses ElementPredicateFactory functions that are evaluated once per
    document for maximum performance, especially beneficial for XPath-based predicates.

    ElementPredicateFactory functions take a document root element and return optimized
    ElementPredicate functions that can efficiently test any element against the criteria.
    This avoids re-evaluating expensive operations like XPath queries for every element.

    The Formatter delegates the actual formatting work to DocumentFormatter instances,
    which are created with concrete ElementPredicate functions for optimal performance.

    Args:
        block_when: Factory creating predicates for block-level elements
        inline_when: Factory creating predicates for inline elements
        normalize_whitespace_when: Factory for whitespace normalization
        strip_whitespace_when: Factory for whitespace stripping
        preserve_whitespace_when: Factory for whitespace preservation
        wrap_attributes_when: Factory for attribute wrapping
        reformat_text_when: Dict mapping factories to TextContentFormatter functions
        indent_size: Number of spaces per indentation level
        default_type: Default element type ('block' or 'inline') for unclassified elements
    """

    def __init__(
        self,
        *,
        block_when: ElementPredicateFactory | None = None,
        inline_when: ElementPredicateFactory | None = None,
        normalize_whitespace_when: ElementPredicateFactory | None = None,
        strip_whitespace_when: ElementPredicateFactory | None = None,
        preserve_whitespace_when: ElementPredicateFactory | None = None,
        wrap_attributes_when: ElementPredicateFactory | None = None,
        reformat_text_when: dict[ElementPredicateFactory, TextContentFormatter] | None = None,
        indent_size: Optional[int] = None,
        default_type: str | None = None,
    ):
        """Initialize a Formatter with predicate factory functions and other configuration.

        Args:
            block_when: Predicate factory function (root -> element predicate) for block elements.
            inline_when: Predicate factory function (root -> element predicate) for inline elements.
            normalize_whitespace_when: Predicate factory for whitespace normalization predicates.
            strip_whitespace_when: Predicate factory for whitespace stripping predicates.
            preserve_whitespace_when: Predicate factory for whitespace preservation predicates.
            wrap_attributes_when: Predicate factory for attribute wrapping predicates.
            reformat_text_when: Dictionary mapping predicate factories to formatter functions.
            indent_size: Number of spaces per indentation level. Defaults to 2.
            default_type: Default type for unclassified elements ("block" or "inline").
        """
        self._block_predicate_factory = block_when or never_matches
        self._inline_predicate_factory = inline_when or never_matches
        self._normalize_predicate_factory = normalize_whitespace_when or never_matches
        self._strip_predicate_factory = strip_whitespace_when or never_matches
        self._preserve_predicate_factory = preserve_whitespace_when or never_matches
        self._wrap_attributes_factory = wrap_attributes_when or never_matches
        self._text_content_formatter_factories = reformat_text_when or {}
        self._indent_size = indent_size or 2
        self._default_type = default_type or "block"

        # Validate parameters
        if self._indent_size < 0:
            raise ValueError(f"indent_size {self._indent_size} is less than 0")

        if self._default_type not in BLOCK_TYPES:
            raise ValueError(f"default_type {self._default_type} is not one of '{', '.join(BLOCK_TYPES)}'")

    @property
    def indent_size(self) -> int:
        """The number of spaces used for each indentation level."""
        return self._indent_size

    @property
    def default_type(self) -> str:
        """The default type for unclassified elements."""
        return self._default_type

    def format_file(self, file_path: str, doctype: str | None = None, xml_declaration: Optional[bool] = None) -> str:
        """Format an XML document from a file path.

        Args:
            file_path: Path to the XML file to format.
            doctype: Optional DOCTYPE declaration to prepend to the output.
            xml_declaration: If True, includes an XML declaration at the top of the output.

        Returns:
            A pretty-printed XML string.
        """
        tree = etree.parse(file_path)
        return self.format_tree(tree, doctype=doctype, xml_declaration=xml_declaration)

    def format_str(self, doc: str, doctype: str | None = None, xml_declaration: Optional[bool] = None) -> str:
        """Format an XML document from a string.

        Args:
            doc: XML document as a string.
            doctype: Optional DOCTYPE declaration to prepend to the output.
            xml_declaration: If True, includes an XML declaration at the top of the output.

        Returns:
            A pretty-printed XML string.
        """
        tree = etree.parse(BytesIO(doc.encode()))
        return self.format_tree(tree, doctype, xml_declaration)

    def format_bytes(self, doc: bytes, doctype: str | None = None, xml_declaration: Optional[bool] = None) -> str:
        """Format an XML document from bytes.

        Args:
            doc: XML document as bytes.
            doctype: Optional DOCTYPE declaration to prepend to the output.
            xml_declaration: If True, includes an XML declaration at the top of the output.

        Returns:
            A pretty-printed XML string.
        """
        tree = etree.parse(BytesIO(doc))
        return self.format_tree(tree, doctype, xml_declaration)

    def format_tree(self, tree: etree._ElementTree, doctype: str | None = None, xml_declaration: Optional[bool] = None) -> str:
        """Format an XML document from an lxml ElementTree.

        Args:
            tree: An lxml.etree._ElementTree representing the XML document.
            doctype: Optional DOCTYPE declaration to prepend to the output.
            xml_declaration: If True, includes an XML declaration at the top of the output.

        Returns:
            A pretty-printed XML string.
        """
        parts = []

        if xml_declaration is None:
            xml_declaration = False

        if xml_declaration:
            parts.append(['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'])

        doctype = doctype or (tree.docinfo.doctype if hasattr(tree, "docinfo") else None)
        if doctype:
            parts.append([doctype, "\n"])

        # Handle comments and PIs before root element
        for event, node in etree.iterwalk(tree, events=("comment", "pi", "start")):
            if event == "comment" and isinstance(node, etree._Comment):
                parts.append(["<!--"])
                if text := node.text:
                    escaped_text = escape(text)
                    if escaped_text.startswith("-"):
                        parts.append([" "])
                    parts.append([escaped_text])
                    if escaped_text.endswith("-"):
                        parts.append([" "])
                parts.append(["-->\n"])
            elif event == "pi" and isinstance(node, etree._ProcessingInstruction):
                pi_parts = []
                pi_parts.append(f"<?{node.target}")
                if node.text:
                    pi_parts.append(f" {node.text}")
                pi_parts.append("?>\n")
                parts.append(pi_parts)
            elif event == "start" and isinstance(node, etree._Element):
                # Reached root element, stop processing
                break

        formatted = self.format_element(tree.getroot(), doctype)
        if formatted:
            parts.append(formatted)

        return "".join(flatten(parts))

    def format_element(self, root: etree._Element, doctype: str | None = None) -> str:
        """Format a single XML element and its descendants.

        Args:
            root: The root lxml.etree._Element to format.
            doctype: Optional DOCTYPE declaration (not used, for API compatibility).

        Returns:
            A pretty-printed XML string for the element and its subtree.
        """
        # Create concrete predicates from factories using the document root
        block_predicate = self._block_predicate_factory(root)
        inline_predicate = self._inline_predicate_factory(root)
        normalize_predicate = self._normalize_predicate_factory(root)
        strip_predicate = self._strip_predicate_factory(root)
        preserve_predicate = self._preserve_predicate_factory(root)
        wrap_attributes_predicate = self._wrap_attributes_factory(root)

        # Create concrete text formatters
        text_formatters = {}
        for factory, formatter_func in self._text_content_formatter_factories.items():
            predicate = factory(root)
            text_formatters[predicate] = formatter_func

        # Create DocumentFormatter with concrete predicates and delegate formatting
        doc_formatter = DocumentFormatter(
            block_predicate=block_predicate,
            inline_predicate=inline_predicate,
            normalize_whitespace_predicate=normalize_predicate,
            strip_whitespace_predicate=strip_predicate,
            preserve_whitespace_predicate=preserve_predicate,
            wrap_attributes_predicate=wrap_attributes_predicate,
            text_content_formatters=text_formatters,
            indent_size=self._indent_size,
            default_type=self._default_type,
        )

        return doc_formatter.format_element(root, doctype)
