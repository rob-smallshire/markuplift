"""High-level XML/HTML document formatter.

This module provides the main Formatter class, which serves as the public API
for formatting XML and HTML documents. The Formatter uses ElementPredicateFactory
functions to create optimized, document-specific predicates that determine how
elements should be formatted.

The Formatter delegates the actual formatting work to DocumentFormatter instances,
which are created with concrete ElementPredicate functions for optimal performance.
"""

from typing import Optional

from lxml import etree

from markuplift.document_formatter import DocumentFormatter
from markuplift.annotation import (
    BLOCK_TYPES,
)

# Import type aliases
from markuplift.types import (
    ElementPredicateFactory,
    TextContentFormatter,
    AttributePredicateFactory,
    AttributeValueFormatter,
    AttributeReorderer,
    ElementType,
)

# Import standard predicates
from markuplift.predicates import never_matches

# Import escaping strategies
from markuplift.escaping import EscapingStrategy, XmlEscapingStrategy

# Import parsing strategies
from markuplift.parsing import ParsingStrategy, XmlParsingStrategy

# Import doctype strategies
from markuplift.doctype import DoctypeStrategy, NullDoctypeStrategy

# Import attribute formatting strategies
from markuplift.attribute_formatting import AttributeFormattingStrategy, NullAttributeStrategy


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
        reformat_attribute_when: Dict mapping attribute factories to AttributeValueFormatter functions
        reorder_attributes_when: Dict mapping factories to AttributeReorderer functions
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
        reformat_attribute_when: dict[AttributePredicateFactory, AttributeValueFormatter] | None = None,
        reorder_attributes_when: dict[ElementPredicateFactory, AttributeReorderer] | None = None,
        escaping_strategy: EscapingStrategy | None = None,
        parsing_strategy: ParsingStrategy | None = None,
        doctype_strategy: DoctypeStrategy | None = None,
        attribute_strategy: AttributeFormattingStrategy | None = None,
        indent_size: Optional[int] = None,
        default_type: ElementType | None = None,
        preserve_cdata: bool = True,
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
            reformat_attribute_when: Dictionary mapping attribute predicate factories to formatter functions.
            reorder_attributes_when: Dictionary mapping predicate factories to attribute reorderer functions.
            escaping_strategy: Strategy for escaping text and attribute values. Defaults to XmlEscapingStrategy.
            parsing_strategy: Strategy for parsing document content. Defaults to XmlParsingStrategy.
            doctype_strategy: Strategy for handling DOCTYPE declarations. Defaults to NullDoctypeStrategy.
            attribute_strategy: Strategy for formatting attributes. Defaults to NullAttributeStrategy.
            indent_size: Number of spaces per indentation level. Defaults to 2.
            default_type: Default type for unclassified elements (ElementType enum).
            preserve_cdata: Whether to preserve CDATA sections from input. Defaults to True.
        """
        self._block_predicate_factory = block_when or never_matches
        self._inline_predicate_factory = inline_when or never_matches
        self._normalize_predicate_factory = normalize_whitespace_when or never_matches
        self._strip_predicate_factory = strip_whitespace_when or never_matches
        self._preserve_predicate_factory = preserve_whitespace_when or never_matches
        self._wrap_attributes_factory = wrap_attributes_when or never_matches
        self._text_content_formatter_factories = reformat_text_when or {}
        self._attribute_content_formatter_factories = reformat_attribute_when or {}
        self._attribute_reorderer_factories = reorder_attributes_when or {}
        self._escaping_strategy = escaping_strategy or XmlEscapingStrategy()
        self._parsing_strategy = parsing_strategy or XmlParsingStrategy(preserve_cdata=preserve_cdata)
        self._doctype_strategy = doctype_strategy or NullDoctypeStrategy()
        self._attribute_strategy = attribute_strategy or NullAttributeStrategy()
        self._indent_size = indent_size or 2
        if default_type is None:
            self._default_type = ElementType.BLOCK
        else:
            self._default_type = default_type

        # Validate parameters
        if self._indent_size < 0:
            raise ValueError(f"indent_size {self._indent_size} is less than 0")

        if self._default_type not in BLOCK_TYPES:
            raise ValueError(
                f"default_type {self._default_type} is not one of '{', '.join(str(t) for t in BLOCK_TYPES)}'"
            )

    @property
    def indent_size(self) -> int:
        """The number of spaces used for each indentation level."""
        return self._indent_size

    @property
    def default_type(self) -> ElementType:
        """The default type for unclassified elements."""
        return self._default_type

    @property
    def block_when(self) -> ElementPredicateFactory:
        """The predicate factory for block elements."""
        return self._block_predicate_factory

    @property
    def inline_when(self) -> ElementPredicateFactory:
        """The predicate factory for inline elements."""
        return self._inline_predicate_factory

    @property
    def normalize_whitespace_when(self) -> ElementPredicateFactory:
        """The predicate factory for whitespace normalization."""
        return self._normalize_predicate_factory

    @property
    def strip_whitespace_when(self) -> ElementPredicateFactory:
        """The predicate factory for whitespace stripping."""
        return self._strip_predicate_factory

    @property
    def preserve_whitespace_when(self) -> ElementPredicateFactory:
        """The predicate factory for whitespace preservation."""
        return self._preserve_predicate_factory

    @property
    def wrap_attributes_when(self) -> ElementPredicateFactory:
        """The predicate factory for attribute wrapping."""
        return self._wrap_attributes_factory

    @property
    def reformat_text_when(self) -> dict[ElementPredicateFactory, TextContentFormatter]:
        """The dictionary mapping predicate factories to text content formatters."""
        return self._text_content_formatter_factories

    @property
    def reformat_attribute_when(self) -> dict[AttributePredicateFactory, AttributeValueFormatter]:
        """The dictionary mapping attribute predicate factories to formatters."""
        return self._attribute_content_formatter_factories

    @property
    def reorder_attributes_when(self) -> dict[ElementPredicateFactory, AttributeReorderer]:
        """The dictionary mapping predicate factories to attribute reorderers."""
        return self._attribute_reorderer_factories

    @property
    def escaping_strategy(self) -> EscapingStrategy:
        """The strategy for escaping text and attribute values."""
        return self._escaping_strategy

    @property
    def parsing_strategy(self) -> ParsingStrategy:
        """The strategy for parsing document content."""
        return self._parsing_strategy

    @property
    def doctype_strategy(self) -> DoctypeStrategy:
        """The strategy for handling DOCTYPE declarations."""
        return self._doctype_strategy

    @property
    def attribute_strategy(self) -> AttributeFormattingStrategy:
        """The strategy for formatting attributes."""
        return self._attribute_strategy

    @property
    def preserve_cdata(self) -> bool:
        """Whether CDATA sections are preserved from input."""
        return self._parsing_strategy.preserve_cdata

    def format_file(self, file_path: str, doctype: str | None = None, xml_declaration: Optional[bool] = None) -> str:
        """Format an XML document from a file path.

        Args:
            file_path: Path to the XML file to format.
            doctype: Optional DOCTYPE declaration to prepend to the output.
            xml_declaration: If True, includes an XML declaration at the top of the output.

        Returns:
            A pretty-printed XML string.
        """
        tree = self._parsing_strategy.parse_file(file_path)
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
        tree = self._parsing_strategy.parse_string(doc)
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
        tree = self._parsing_strategy.parse_bytes(doc)
        return self.format_tree(tree, doctype, xml_declaration)

    def format_tree(
        self, tree: etree._ElementTree, doctype: str | None = None, xml_declaration: Optional[bool] = None
    ) -> str:
        """Format an XML document from an lxml ElementTree.

        Args:
            tree: An lxml.etree._ElementTree representing the XML document.
            doctype: Optional DOCTYPE declaration to prepend to the output.
            xml_declaration: If True, includes an XML declaration at the top of the output.

        Returns:
            A pretty-printed XML string.
        """
        doc_formatter = self._create_document_formatter(tree.getroot())
        return doc_formatter.format_tree(tree, doctype, xml_declaration)

    def format_element(self, root: etree._Element, doctype: str | None = None) -> str:
        """Format a single XML element and its descendants.

        Args:
            root: The root lxml.etree._Element to format.
            doctype: Optional DOCTYPE declaration to prepend to the output.

        Returns:
            A pretty-printed XML string for the element and its subtree.
        """
        doc_formatter = self._create_document_formatter(root)
        return doc_formatter.format_element(root, doctype)

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
        reorder_attributes_when: dict[ElementPredicateFactory, AttributeReorderer] | None = None,
        escaping_strategy: EscapingStrategy | None = None,
        parsing_strategy: ParsingStrategy | None = None,
        doctype_strategy: DoctypeStrategy | None = None,
        attribute_strategy: AttributeFormattingStrategy | None = None,
        indent_size: Optional[int] = None,
        default_type: ElementType | None = None,
        preserve_cdata: bool | None = None,
    ) -> "Formatter":
        """Create a new Formatter derived from this one with selective modifications.

        This factory method creates a new Formatter instance that inherits all settings
        from the current formatter except for those explicitly provided as arguments.
        This allows easy customization without having to respecify all parameters.

        Args:
            block_when: Predicate factory for block elements (uses current if None).
            inline_when: Predicate factory for inline elements (uses current if None).
            normalize_whitespace_when: Predicate factory for whitespace normalization (uses current if None).
            strip_whitespace_when: Predicate factory for whitespace stripping (uses current if None).
            preserve_whitespace_when: Predicate factory for whitespace preservation (uses current if None).
            wrap_attributes_when: Predicate factory for attribute wrapping (uses current if None).
            reformat_text_when: Dictionary mapping predicate factories to formatters (uses current if None).
            reformat_attribute_when: Dictionary mapping attribute predicate factories to formatters (uses current if None).
            reorder_attributes_when: Dictionary mapping predicate factories to attribute reorderers (uses current if None).
            escaping_strategy: Strategy for escaping text and attribute values (uses current if None).
            parsing_strategy: Strategy for parsing document content (uses current if None).
            doctype_strategy: Strategy for handling DOCTYPE declarations (uses current if None).
            attribute_strategy: Strategy for formatting attributes (uses current if None).
            indent_size: Number of spaces per indentation level (uses current if None).
            default_type: Default type for unclassified elements (uses current if None).

        Returns:
            A new Formatter instance with the specified modifications.

        Example:
            >>> from markuplift import Formatter
            >>> from markuplift.predicates import tag_in
            >>>
            >>> # Create a base formatter
            >>> base = Formatter(block_when=tag_in("div", "p"))
            >>>
            >>> # Derive a new formatter with additional block elements
            >>> extended = base.derive(block_when=tag_in("div", "p", "section", "article"))
            >>>
            >>> # Create another variant with different indentation
            >>> compact = base.derive(indent_size=0)
        """
        return type(self)(
            block_when=block_when if block_when is not None else self._block_predicate_factory,
            inline_when=inline_when if inline_when is not None else self._inline_predicate_factory,
            normalize_whitespace_when=normalize_whitespace_when
            if normalize_whitespace_when is not None
            else self._normalize_predicate_factory,
            strip_whitespace_when=strip_whitespace_when
            if strip_whitespace_when is not None
            else self._strip_predicate_factory,
            preserve_whitespace_when=preserve_whitespace_when
            if preserve_whitespace_when is not None
            else self._preserve_predicate_factory,
            wrap_attributes_when=wrap_attributes_when
            if wrap_attributes_when is not None
            else self._wrap_attributes_factory,
            reformat_text_when=reformat_text_when
            if reformat_text_when is not None
            else self._text_content_formatter_factories,
            reformat_attribute_when=reformat_attribute_when
            if reformat_attribute_when is not None
            else self._attribute_content_formatter_factories,
            reorder_attributes_when=reorder_attributes_when
            if reorder_attributes_when is not None
            else self._attribute_reorderer_factories,
            escaping_strategy=escaping_strategy if escaping_strategy is not None else self._escaping_strategy,
            parsing_strategy=parsing_strategy if parsing_strategy is not None else self._parsing_strategy,
            doctype_strategy=doctype_strategy if doctype_strategy is not None else self._doctype_strategy,
            attribute_strategy=attribute_strategy if attribute_strategy is not None else self._attribute_strategy,
            indent_size=indent_size if indent_size is not None else self._indent_size,
            default_type=default_type if default_type is not None else self._default_type,
            preserve_cdata=preserve_cdata if preserve_cdata is not None else self.preserve_cdata,
        )

    def _create_document_formatter(self, root: etree._Element) -> DocumentFormatter:
        """Create a DocumentFormatter with concrete predicates for the given root.

        Args:
            root: The root element to create predicates for.

        Returns:
            A DocumentFormatter configured with concrete predicates.
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
        for text_factory, formatter_func in self._text_content_formatter_factories.items():
            text_predicate = text_factory(root)
            text_formatters[text_predicate] = formatter_func

        # Create concrete attribute formatters
        attribute_formatters = {}
        for attr_factory, formatter_func in self._attribute_content_formatter_factories.items():
            attr_predicate = attr_factory(root)
            attribute_formatters[attr_predicate] = formatter_func

        # Create concrete attribute reorderers
        attribute_reorderers = {}
        for reorderer_factory, reorderer_func in self._attribute_reorderer_factories.items():
            reorderer_predicate = reorderer_factory(root)
            attribute_reorderers[reorderer_predicate] = reorderer_func

        # Create DocumentFormatter with concrete predicates
        return DocumentFormatter(
            block_predicate=block_predicate,
            inline_predicate=inline_predicate,
            normalize_whitespace_predicate=normalize_predicate,
            strip_whitespace_predicate=strip_predicate,
            preserve_whitespace_predicate=preserve_predicate,
            wrap_attributes_predicate=wrap_attributes_predicate,
            text_content_formatters=text_formatters,
            attribute_content_formatters=attribute_formatters,
            attribute_reorderers=attribute_reorderers,
            escaping_strategy=self._escaping_strategy,
            doctype_strategy=self._doctype_strategy,
            attribute_strategy=self._attribute_strategy,
            indent_size=self._indent_size,
            default_type=self._default_type,
        )
