"""HTML5-optimized formatter wrapper.

This module provides Html5Formatter, a convenience wrapper around the main Formatter
that pre-configures HTML5-friendly strategies for parsing and escaping while letting
users control element classification through predicate factories.
"""

from typing import Optional
from markuplift.formatter import Formatter
from markuplift.escaping import HtmlEscapingStrategy
from markuplift.parsing import HtmlParsingStrategy
from markuplift.doctype import Html5DoctypeStrategy
from markuplift.predicates import html_block_elements, html_inline_elements, html_whitespace_significant_elements, not_matching, css_block_elements, all_of
from markuplift.types import ElementPredicateFactory, TextContentFormatter, AttributePredicateFactory


class Html5Formatter:
    """HTML5-optimized formatter with HTML-friendly parsing and escaping strategies.

    This is a convenience wrapper around the main Formatter class that pre-configures
    HTML5-specific strategies:
    - Uses HtmlParsingStrategy for better HTML5 void element handling
    - Uses HtmlEscapingStrategy for more readable attribute values (literal newlines)
    - Uses Html5DoctypeStrategy for automatic HTML5 DOCTYPE handling
    - Defaults to html_block_elements() and html_inline_elements() for sensible HTML5 formatting
    - Defaults to html_whitespace_significant_elements() for preserve_whitespace_when
    - Defaults to not_matching(html_whitespace_significant_elements()) for normalize_whitespace_when
    - Defaults to css_block_elements() excluding whitespace-significant elements for strip_whitespace_when

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
        reformat_attribute_when: dict[AttributePredicateFactory, TextContentFormatter] | None = None,
        indent_size: Optional[int] = None,
        default_type: str | None = None,
    ):
        """Initialize Html5Formatter with HTML5-optimized strategies.

        Args:
            block_when: Predicate factory function (root -> element predicate) for block elements.
                       Defaults to html_block_elements() if not provided.
            inline_when: Predicate factory function (root -> element predicate) for inline elements.
                        Defaults to html_inline_elements() if not provided.
            normalize_whitespace_when: Predicate factory for whitespace normalization predicates.
                                     Defaults to not_matching(html_whitespace_significant_elements()) if not provided.
            strip_whitespace_when: Predicate factory for whitespace stripping predicates.
                                 Defaults to css_block_elements() excluding whitespace-significant elements if not provided.
            preserve_whitespace_when: Predicate factory for whitespace preservation predicates.
                                    Defaults to html_whitespace_significant_elements() if not provided.
            wrap_attributes_when: Predicate factory for attribute wrapping predicates.
            reformat_text_when: Dictionary mapping predicate factories to formatter functions.
            reformat_attribute_when: Dictionary mapping attribute predicate factories to formatter functions.
            indent_size: Number of spaces per indentation level. Defaults to 2.
            default_type: Default type for unclassified elements ("block" or "inline").

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
            normalize_whitespace_when = not_matching(html_whitespace_significant_elements())
        if preserve_whitespace_when is None:
            preserve_whitespace_when = html_whitespace_significant_elements()
        if strip_whitespace_when is None:
            strip_whitespace_when = all_of(
                css_block_elements(),
                not_matching(html_whitespace_significant_elements())
            )

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
            escaping_strategy=HtmlEscapingStrategy(),
            parsing_strategy=HtmlParsingStrategy(),
            doctype_strategy=Html5DoctypeStrategy(),
            indent_size=indent_size,
            default_type=default_type,
        )

    def format_file(self, file_path: str, doctype: str | None = None) -> str:
        """Format an HTML file.

        Args:
            file_path: Path to the HTML file to format.
            doctype: Optional DOCTYPE declaration to prepend to the output.

        Returns:
            A pretty-printed HTML string.
        """
        return self._formatter.format_file(file_path, doctype=doctype, xml_declaration=False)

    def format_str(self, doc: str, doctype: str | None = None) -> str:
        """Format an HTML document from a string.

        Args:
            doc: HTML document as a string.
            doctype: Optional DOCTYPE declaration to prepend to the output.

        Returns:
            A pretty-printed HTML string.
        """
        return self._formatter.format_str(doc, doctype=doctype, xml_declaration=False)

    def format_bytes(self, doc: bytes, doctype: str | None = None) -> str:
        """Format an HTML document from bytes.

        Args:
            doc: HTML document as bytes.
            doctype: Optional DOCTYPE declaration to prepend to the output.

        Returns:
            A pretty-printed HTML string.
        """
        return self._formatter.format_bytes(doc, doctype=doctype, xml_declaration=False)

    def format_tree(self, tree, doctype: str | None = None) -> str:
        """Format an HTML document from an lxml ElementTree.

        Args:
            tree: An lxml ElementTree to format.
            doctype: Optional DOCTYPE declaration to prepend to the output.

        Returns:
            A pretty-printed HTML string.
        """
        return self._formatter.format_tree(tree, doctype=doctype, xml_declaration=False)