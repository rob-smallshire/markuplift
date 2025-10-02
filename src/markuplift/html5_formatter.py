"""HTML5-optimized formatter wrapper.

This module provides Html5Formatter, a convenience wrapper around the main Formatter
that pre-configures HTML5-friendly strategies for parsing and escaping while letting
users control element classification through predicate factories.
"""

from typing import Optional
from lxml import etree
from markuplift.formatter import Formatter
from markuplift.escaping import HtmlEscapingStrategy
from markuplift.parsing import HtmlParsingStrategy
from markuplift.doctype import Html5DoctypeStrategy
from markuplift.empty_element import Html5EmptyElementStrategy
from markuplift.predicates import (
    html_block_elements,
    html_inline_elements,
    html_whitespace_significant_elements,
    html_normalize_whitespace,
    not_matching,
    all_of,
)
from markuplift.attribute_formatting import Html5AttributeStrategy
from markuplift.types import (
    ElementPredicateFactory,
    TextContentFormatter,
    AttributePredicateFactory,
    AttributeValueFormatter,
    AttributeReorderer,
    ElementType,
)


class Html5Formatter:
    """HTML5-optimized formatter with HTML-friendly parsing and escaping strategies.

    This is a convenience wrapper around the main Formatter class that pre-configures
    HTML5-specific strategies:
    - Uses HtmlParsingStrategy for better HTML5 void element handling
    - Uses HtmlEscapingStrategy for more readable attribute values (literal newlines)
    - Uses Html5DoctypeStrategy for automatic HTML5 DOCTYPE handling
    - Defaults to html_block_elements() and html_inline_elements() for sensible HTML5 formatting
    - Defaults to html_whitespace_significant_elements() for preserve_whitespace_when
    - Defaults to html_normalize_whitespace() for normalize_whitespace_when (excludes whitespace-significant elements and their descendants)
    - Defaults to html_block_elements() excluding whitespace-significant elements for strip_whitespace_when
    - Defaults to html_attribute_order() for reorder_attributes_when, providing semantic HTML attribute ordering

    Element classification can be overridden by providing custom predicate factories,
    but defaults to standard HTML5 element classifications for immediate usability.

    All Formatter methods are available through delegation.

    Example:
        >>> from markuplift import Html5Formatter
        >>>
        >>> # Uses HTML5 defaults - no configuration needed
        >>> formatter = Html5Formatter()
        >>> formatted = formatter.format_str('<div><img src="test.jpg"><br></div>')
        >>>
        >>> # Or customize element classification if needed
        >>> from markuplift.predicates import tag_in
        >>> custom_formatter = Html5Formatter(block_when=tag_in("div", "section"))
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
        parse_as_xml_when: ElementPredicateFactory | None = None,
        indent_size: Optional[int] = None,
        default_type: ElementType | None = None,
        preserve_cdata: bool = True,
    ):
        """Initialize Html5Formatter with HTML5-optimized strategies.

        Args:
            block_when: Predicate factory function (root -> element predicate) for block elements.
                       Defaults to html_block_elements() if not provided.
            inline_when: Predicate factory function (root -> element predicate) for inline elements.
                        Defaults to html_inline_elements() if not provided.
            normalize_whitespace_when: Predicate factory for whitespace normalization predicates.
                                     Defaults to html_normalize_whitespace() if not provided, which excludes
                                     whitespace-significant elements and their descendants.
            strip_whitespace_when: Predicate factory for whitespace stripping predicates.
                                 Defaults to html_block_elements() excluding whitespace-significant elements if not provided.
            preserve_whitespace_when: Predicate factory for whitespace preservation predicates.
                                    Defaults to html_whitespace_significant_elements() if not provided.
            wrap_attributes_when: Predicate factory for attribute wrapping predicates.
            reformat_text_when: Dictionary mapping predicate factories to formatter functions.
            reformat_attribute_when: Dictionary mapping attribute predicate factories to formatter functions.
            reorder_attributes_when: Dictionary mapping predicate factories to attribute reorderer functions.
                                   Defaults to html_attribute_order() for all elements if not provided.
            parse_as_xml_when: Predicate factory for identifying subtrees to reparse as XML.
                             Useful for preserving case-sensitive elements like SVG in HTML5 documents.
                             Defaults to None (no XML reparsing).
            indent_size: Number of spaces per indentation level. Defaults to 2.
            default_type: Default type for unclassified elements (ElementType enum).
            preserve_cdata: Whether to preserve CDATA sections from input. Defaults to True.

        Note:
            This class automatically configures HTML5-friendly parsing and escaping strategies.
            Element classification defaults to HTML5 standards but can be overridden via predicate factories.
        """
        # Default to HTML5 element classifications if not provided
        if block_when is None:
            block_when = html_block_elements()
        if inline_when is None:
            inline_when = html_inline_elements()

        # Default to HTML5 whitespace handling if not provided
        if normalize_whitespace_when is None:
            normalize_whitespace_when = html_normalize_whitespace()
        if preserve_whitespace_when is None:
            preserve_whitespace_when = html_whitespace_significant_elements()
        if strip_whitespace_when is None:
            strip_whitespace_when = all_of(html_block_elements(), not_matching(html_whitespace_significant_elements()))

        # Default to HTML5 semantic attribute ordering if not provided
        if reorder_attributes_when is None:
            from markuplift.attribute_formatting import html_attribute_order
            from markuplift.predicates import any_element
            reorder_attributes_when = {any_element(): html_attribute_order()}

        # Store parse_as_xml_when for use in format methods
        self._parse_as_xml_when = parse_as_xml_when

        # Pre-configure HTML5-friendly strategies
        self._formatter = Formatter(
            block_when=block_when,
            inline_when=inline_when,
            normalize_whitespace_when=normalize_whitespace_when,
            strip_whitespace_when=strip_whitespace_when,
            preserve_whitespace_when=preserve_whitespace_when,
            wrap_attributes_when=wrap_attributes_when,
            reformat_text_when=reformat_text_when,
            reformat_attribute_when=reformat_attribute_when,
            reorder_attributes_when=reorder_attributes_when,
            escaping_strategy=HtmlEscapingStrategy(),
            parsing_strategy=HtmlParsingStrategy(preserve_cdata=preserve_cdata),
            doctype_strategy=Html5DoctypeStrategy(),
            attribute_strategy=Html5AttributeStrategy(),
            empty_element_strategy=Html5EmptyElementStrategy(),
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
    def reorder_attributes_when(self) -> dict[ElementPredicateFactory, AttributeReorderer]:
        """The dictionary mapping predicate factories to attribute reorderers."""
        return self._formatter.reorder_attributes_when

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

    @property
    def parse_as_xml_when(self) -> ElementPredicateFactory | None:
        """The predicate factory for XML subtree reparsing."""
        return self._parse_as_xml_when

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
        parse_as_xml_when: ElementPredicateFactory | None = None,
        indent_size: Optional[int] = None,
        default_type: ElementType | None = None,
        preserve_cdata: bool | None = None,
    ) -> "Html5Formatter":
        """Create a new Html5Formatter derived from this one with selective modifications.

        This factory method creates a new Html5Formatter instance that inherits all settings
        from the current formatter except for those explicitly provided as arguments.
        This maintains the HTML5-specific strategies (parsing, escaping, doctype, attributes)
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
            reorder_attributes_when: Dictionary mapping predicate factories to attribute reorderers (uses current if None).
            parse_as_xml_when: Predicate factory for XML subtree reparsing (uses current if None).
            indent_size: Number of spaces per indentation level (uses current if None).
            default_type: Default type for unclassified elements (uses current if None).
            preserve_cdata: Whether to preserve CDATA sections from input (uses current if None).

        Returns:
            A new Html5Formatter instance with the specified modifications.

        Note:
            The HTML5-specific strategies (parsing, escaping, doctype, attributes) are
            preserved and cannot be overridden through this method, ensuring HTML5
            compliance is maintained.

        Example:
            >>> from markuplift import Html5Formatter
            >>> from markuplift.predicates import tag_in, all_of
            >>>
            >>> # Create a base HTML5 formatter with defaults
            >>> base = Html5Formatter()
            >>>
            >>> # Derive a formatter with custom block elements while keeping HTML5 defaults
            >>> custom = base.derive(
            ...     block_when=all_of(base.block_when, tag_in("custom-block"))
            ... )
        """
        return Html5Formatter(
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
            reorder_attributes_when=reorder_attributes_when
            if reorder_attributes_when is not None
            else self._formatter.reorder_attributes_when,
            parse_as_xml_when=parse_as_xml_when if parse_as_xml_when is not None else self._parse_as_xml_when,
            indent_size=indent_size if indent_size is not None else self._formatter.indent_size,
            default_type=default_type if default_type is not None else self._formatter.default_type,
            preserve_cdata=preserve_cdata if preserve_cdata is not None else self.preserve_cdata,
        )

    def format_file(self, file_path: str, doctype: str | None = None) -> str:
        """Format an HTML file.

        Args:
            file_path: Path to the HTML file to format.
            doctype: Optional DOCTYPE declaration to prepend to the output.

        Returns:
            A pretty-printed HTML string.
        """
        with open(file_path, 'rb') as f:
            source_bytes = f.read()
        return self._format_with_source(source_bytes, doctype)

    def format_str(self, doc: str, doctype: str | None = None) -> str:
        """Format an HTML document from a string.

        Args:
            doc: HTML document as a string.
            doctype: Optional DOCTYPE declaration to prepend to the output.

        Returns:
            A pretty-printed HTML string.
        """
        source_bytes = doc.encode('utf-8')
        return self._format_with_source(source_bytes, doctype)

    def format_bytes(self, doc: bytes, doctype: str | None = None) -> str:
        """Format an HTML document from bytes.

        Args:
            doc: HTML document as bytes.
            doctype: Optional DOCTYPE declaration to prepend to the output.

        Returns:
            A pretty-printed HTML string.
        """
        return self._format_with_source(doc, doctype)

    def format_tree(self, tree, doctype: str | None = None) -> str:
        """Format an HTML document from an lxml ElementTree.

        Args:
            tree: An lxml ElementTree to format.
            doctype: Optional DOCTYPE declaration to prepend to the output.

        Returns:
            A pretty-printed HTML string.

        Note:
            When formatting from a tree, no source bytes are available, so XML
            subtree reparsing (parse_as_xml_when) cannot be applied.
        """
        return self._formatter.format_tree(tree, doctype=doctype, xml_declaration=False)

    def _format_with_source(self, source_bytes: bytes, doctype: str | None = None) -> str:
        """Format HTML from bytes, with optional XML subtree reparsing.

        Args:
            source_bytes: HTML document as bytes.
            doctype: Optional DOCTYPE declaration to prepend to the output.

        Returns:
            A pretty-printed HTML string.
        """
        # Parse as HTML using the parsing strategy
        tree = self._formatter._parsing_strategy.parse_bytes(source_bytes)

        # Reparse XML subtrees if requested (modifies tree in-place)
        if self._parse_as_xml_when:
            self._reparse_xml_subtrees(tree, source_bytes)

        # Format the tree (source_bytes no longer needed)
        return self._formatter.format_tree(tree, doctype=doctype, xml_declaration=False)

    def _reparse_xml_subtrees(self, tree: etree._ElementTree, source_bytes: bytes) -> None:
        """Reparse specified subtrees as XML to preserve case.

        Modifies tree in-place, replacing HTML-parsed elements with XML-parsed versions.

        Args:
            tree: The HTML-parsed ElementTree to modify.
            source_bytes: The original source bytes for extraction.
        """
        from markuplift.source_locator import SimpleTagScanner

        root = tree.getroot()

        # Create predicate for this document
        predicate = self._parse_as_xml_when(root)

        # Find elements matching predicate
        elements_to_reparse = []
        for elem in root.iter():
            if predicate(elem):
                elements_to_reparse.append(elem)

        # Reparse each matching element
        scanner = SimpleTagScanner(source_bytes)
        xml_parser = etree.XMLParser()

        for elem in elements_to_reparse:
            # Get path from root
            path = self._get_element_path(root, elem)

            # Account for root element being at index [0] in scanner's view
            scanner_path = [0] + path if path else [0]

            # Find byte range in source
            byte_range = scanner.find_element_range(scanner_path)
            if not byte_range:
                continue

            start, end = byte_range

            # Extract and reparse as XML
            subtree_bytes = source_bytes[start:end]
            try:
                xml_elem = etree.fromstring(subtree_bytes, parser=xml_parser)
            except etree.XMLSyntaxError:
                # If XML parsing fails, skip this element
                continue

            # Replace in tree
            parent = elem.getparent()
            if parent is not None:
                index = list(parent).index(elem)
                parent.remove(elem)
                parent.insert(index, xml_elem)

    def _get_element_path(self, root: etree._Element, target: etree._Element) -> list[int]:
        """Get path from root to target as list of child indices.

        This counts only element children, not comments or other nodes,
        to match the scanner's element-only counting.

        Args:
            root: The root element to start from.
            target: The target element to find.

        Returns:
            List of child indices representing the path from root to target.
            Returns empty list if target is root, None if target not found.
        """
        def walk(elem, path):
            if elem is target:
                return path
            # Only count element children, filtering out comments and other nodes
            element_index = 0
            for child in elem:
                # Check if child is an element (not a comment, PI, etc.)
                if isinstance(child.tag, str):
                    result = walk(child, path + [element_index])
                    if result is not None:
                        return result
                    element_index += 1
            return None

        return walk(root, [])
