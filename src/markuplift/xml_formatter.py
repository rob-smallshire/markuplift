"""XML-strict formatter wrapper.

This module provides XmlFormatter, a convenience wrapper around the main Formatter
that pre-configures XML-strict strategies for parsing and escaping while letting
users control element classification through predicate factories.
"""

from typing import Optional
from markuplift.formatter import Formatter
from markuplift.escaping import XmlEscapingStrategy
from markuplift.parsing import XmlParsingStrategy
from markuplift.doctype import XmlDoctypeStrategy
from markuplift.types import ElementPredicateFactory, TextContentFormatter, AttributePredicateFactory


class XmlFormatter:
    """XML-strict formatter with XML-compliant parsing and escaping strategies.

    This is a convenience wrapper around the main Formatter class that pre-configures
    XML-strict strategies:
    - Uses XmlParsingStrategy for strict XML compliance and validation
    - Uses XmlEscapingStrategy for XML-compliant attribute values (&#10; entities)

    Element classification (block vs inline) is still controlled by user-provided
    predicate factories, as this is a user configuration concern rather than a
    format-specific concern.

    All Formatter methods are available through delegation.

    Example:
        >>> from markuplift import XmlFormatter
        >>>
        >>> formatter = XmlFormatter(
        ...     block_when=tag_in("div", "p", "section"),
        ...     inline_when=tag_in("em", "strong", "code")
        ... )
        >>> formatted = formatter.format_str('<root><child>content</child></root>')
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
        reformat_attribute_when: dict[AttributePredicateFactory, TextContentFormatter] | None = None,
        indent_size: Optional[int] = None,
        default_type: str | None = None,
    ):
        """Initialize XmlFormatter with XML-strict strategies.

        Args:
            block_when: Predicate factory function (root -> element predicate) for block elements.
            inline_when: Predicate factory function (root -> element predicate) for inline elements.
            normalize_whitespace_when: Predicate factory for whitespace normalization predicates.
            strip_whitespace_when: Predicate factory for whitespace stripping predicates.
            preserve_whitespace_when: Predicate factory for whitespace preservation predicates.
            wrap_attributes_when: Predicate factory for attribute wrapping predicates.
            reformat_text_when: Dictionary mapping predicate factories to formatter functions.
            reformat_attribute_when: Dictionary mapping attribute predicate factories to formatter functions.
            indent_size: Number of spaces per indentation level. Defaults to 2.
            default_type: Default type for unclassified elements ("block" or "inline").

        Note:
            This class automatically configures XML-strict parsing and escaping strategies.
            Element classification should be provided by the user via predicate factories.
        """
        # Pre-configure XML-strict strategies
        self._formatter = Formatter(
            block_when=block_when,
            inline_when=inline_when,
            normalize_whitespace_when=normalize_whitespace_when,
            strip_whitespace_when=strip_whitespace_when,
            preserve_whitespace_when=preserve_whitespace_when,
            wrap_attributes_when=wrap_attributes_when,
            reformat_text_when=reformat_text_when,
            reformat_attribute_when=reformat_attribute_when,
            escaping_strategy=XmlEscapingStrategy(),
            parsing_strategy=XmlParsingStrategy(),
            doctype_strategy=XmlDoctypeStrategy(),
            indent_size=indent_size,
            default_type=default_type,
        )

    def format_file(self, file_path: str, doctype: str | None = None, xml_declaration: Optional[bool] = None) -> str:
        """Format an XML file.

        Args:
            file_path: Path to the XML file to format.
            doctype: Optional DOCTYPE declaration to prepend to the output.
            xml_declaration: If True, includes an XML declaration at the top of the output.

        Returns:
            A pretty-printed XML string.
        """
        return self._formatter.format_file(file_path, doctype=doctype, xml_declaration=xml_declaration)

    def format_str(self, doc: str, doctype: str | None = None, xml_declaration: Optional[bool] = None) -> str:
        """Format an XML document from a string.

        Args:
            doc: XML document as a string.
            doctype: Optional DOCTYPE declaration to prepend to the output.
            xml_declaration: If True, includes an XML declaration at the top of the output.

        Returns:
            A pretty-printed XML string.
        """
        return self._formatter.format_str(doc, doctype=doctype, xml_declaration=xml_declaration)

    def format_bytes(self, doc: bytes, doctype: str | None = None, xml_declaration: Optional[bool] = None) -> str:
        """Format an XML document from bytes.

        Args:
            doc: XML document as bytes.
            doctype: Optional DOCTYPE declaration to prepend to the output.
            xml_declaration: If True, includes an XML declaration at the top of the output.

        Returns:
            A pretty-printed XML string.
        """
        return self._formatter.format_bytes(doc, doctype=doctype, xml_declaration=xml_declaration)

    def format_tree(self, tree, doctype: str | None = None, xml_declaration: Optional[bool] = None) -> str:
        """Format an XML document from an lxml ElementTree.

        Args:
            tree: An lxml ElementTree to format.
            doctype: Optional DOCTYPE declaration to prepend to the output.
            xml_declaration: If True, includes an XML declaration at the top of the output.

        Returns:
            A pretty-printed XML string.
        """
        return self._formatter.format_tree(tree, doctype=doctype, xml_declaration=xml_declaration)