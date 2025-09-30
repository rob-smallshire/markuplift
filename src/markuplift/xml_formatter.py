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
from markuplift.attribute_formatting import XmlAttributeStrategy
from markuplift.types import (
    ElementPredicateFactory,
    TextContentFormatter,
    AttributePredicateFactory,
    AttributeValueFormatter,
    ElementType,
)


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
        reformat_attribute_when: dict[AttributePredicateFactory, AttributeValueFormatter] | None = None,
        indent_size: Optional[int] = None,
        default_type: ElementType | None = None,
        preserve_cdata: bool = True,
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
            default_type: Default type for unclassified elements (ElementType enum).
            preserve_cdata: Whether to preserve CDATA sections from input. Defaults to True.

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
            parsing_strategy=XmlParsingStrategy(preserve_cdata=preserve_cdata),
            doctype_strategy=XmlDoctypeStrategy(),
            attribute_strategy=XmlAttributeStrategy(),
            indent_size=indent_size,
            default_type=default_type,
            preserve_cdata=preserve_cdata,
        )

    @property
    def block_when(self) -> ElementPredicateFactory:
        """The predicate factory for block elements."""
        return self._formatter.block_when

    @property
    def inline_when(self) -> ElementPredicateFactory:
        """The predicate factory for inline elements."""
        return self._formatter.inline_when

    @property
    def normalize_whitespace_when(self) -> ElementPredicateFactory:
        """The predicate factory for whitespace normalization."""
        return self._formatter.normalize_whitespace_when

    @property
    def strip_whitespace_when(self) -> ElementPredicateFactory:
        """The predicate factory for whitespace stripping."""
        return self._formatter.strip_whitespace_when

    @property
    def preserve_whitespace_when(self) -> ElementPredicateFactory:
        """The predicate factory for whitespace preservation."""
        return self._formatter.preserve_whitespace_when

    @property
    def wrap_attributes_when(self) -> ElementPredicateFactory:
        """The predicate factory for attribute wrapping."""
        return self._formatter.wrap_attributes_when

    @property
    def reformat_text_when(self) -> dict[ElementPredicateFactory, TextContentFormatter]:
        """The dictionary mapping predicate factories to text content formatters."""
        return self._formatter.reformat_text_when

    @property
    def reformat_attribute_when(self) -> dict[AttributePredicateFactory, AttributeValueFormatter]:
        """The dictionary mapping attribute predicate factories to formatters."""
        return self._formatter.reformat_attribute_when

    @property
    def indent_size(self) -> int:
        """The number of spaces used for each indentation level."""
        return self._formatter.indent_size

    @property
    def default_type(self) -> ElementType:
        """The default type for unclassified elements."""
        return self._formatter.default_type

    @property
    def preserve_cdata(self) -> bool:
        """Whether CDATA sections are preserved from input."""
        return self._formatter.preserve_cdata

    def derive(
        self,
        *,
        block_when: ElementPredicateFactory | None = None,
        inline_when: ElementPredicateFactory | None = None,
        normalize_whitespace_when: ElementPredicateFactory | None = None,
        strip_whitespace_when: ElementPredicateFactory | None = None,
        preserve_whitespace_when: ElementPredicateFactory | None = None,
        wrap_attributes_when: ElementPredicateFactory | None = None,
        reformat_text_when: dict[ElementPredicateFactory, TextContentFormatter] | None = None,
        reformat_attribute_when: dict[AttributePredicateFactory, AttributeValueFormatter] | None = None,
        indent_size: Optional[int] = None,
        default_type: ElementType | None = None,
        preserve_cdata: bool | None = None,
    ) -> "XmlFormatter":
        """Create a new XmlFormatter derived from this one with selective modifications.

        This factory method creates a new XmlFormatter instance that inherits all settings
        from the current formatter except for those explicitly provided as arguments.
        This maintains the XML-strict strategies (parsing, escaping, doctype, attributes)
        while allowing customization of element classification and formatting rules.

        Args:
            block_when: Predicate factory for block elements (uses current if None).
            inline_when: Predicate factory for inline elements (uses current if None).
            normalize_whitespace_when: Predicate factory for whitespace normalization (uses current if None).
            strip_whitespace_when: Predicate factory for whitespace stripping (uses current if None).
            preserve_whitespace_when: Predicate factory for whitespace preservation (uses current if None).
            wrap_attributes_when: Predicate factory for attribute wrapping (uses current if None).
            reformat_text_when: Dictionary mapping predicate factories to formatters (uses current if None).
            reformat_attribute_when: Dictionary mapping attribute predicate factories to formatters (uses current if None).
            indent_size: Number of spaces per indentation level (uses current if None).
            default_type: Default type for unclassified elements (uses current if None).
            preserve_cdata: Whether to preserve CDATA sections from input (uses current if None).

        Returns:
            A new XmlFormatter instance with the specified modifications.

        Note:
            The XML-strict strategies (parsing, escaping, doctype, attributes) are
            preserved and cannot be overridden through this method, ensuring XML
            compliance is maintained.

        Example:
            >>> from markuplift import XmlFormatter
            >>> from markuplift.predicates import tag_in, any_of
            >>>
            >>> # Create a base XML formatter
            >>> base = XmlFormatter(block_when=tag_in("section", "article"))
            >>>
            >>> # Derive a formatter with additional block elements
            >>> extended = base.derive(
            ...     block_when=any_of(base.block_when, tag_in("custom", "special"))
            ... )
        """
        return XmlFormatter(
            block_when=block_when if block_when is not None else self._formatter.block_when,
            inline_when=inline_when if inline_when is not None else self._formatter.inline_when,
            normalize_whitespace_when=normalize_whitespace_when
            if normalize_whitespace_when is not None
            else self._formatter.normalize_whitespace_when,
            strip_whitespace_when=strip_whitespace_when
            if strip_whitespace_when is not None
            else self._formatter.strip_whitespace_when,
            preserve_whitespace_when=preserve_whitespace_when
            if preserve_whitespace_when is not None
            else self._formatter.preserve_whitespace_when,
            wrap_attributes_when=wrap_attributes_when
            if wrap_attributes_when is not None
            else self._formatter.wrap_attributes_when,
            reformat_text_when=reformat_text_when
            if reformat_text_when is not None
            else self._formatter.reformat_text_when,
            reformat_attribute_when=reformat_attribute_when
            if reformat_attribute_when is not None
            else self._formatter.reformat_attribute_when,
            indent_size=indent_size if indent_size is not None else self._formatter.indent_size,
            default_type=default_type if default_type is not None else self._formatter.default_type,
            preserve_cdata=preserve_cdata if preserve_cdata is not None else self.preserve_cdata,
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
