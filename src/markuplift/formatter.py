from pprint import pprint
from typing import Callable, Optional
from io import BytesIO
from xml.sax.saxutils import quoteattr, escape

from les_iterables import flatten
from lxml import etree

from markuplift.annotation import (
    Annotations, annotate_explicit_block_elements,
    annotate_explicit_inline_elements, annotate_elements_in_mixed_content_as_inline,
    annotate_inline_descendants_as_inline, annotate_unmixed_block_descendants_as_block,
    annotate_xml_space, annotate_explicit_whitespace_preserving_elements,
    annotate_whitespace_preserving_descendants_as_whitespace_preserving,
    annotate_explicit_whitespace_normalizing_elements, BLOCK_TYPES,
    annotate_untyped_elements_as_default, annotate_logical_level, annotate_physical_level,
    annotate_text_transforms, annotate_tail_transforms, annotate_explicit_stripped_elements,
    PHYSICAL_LEVEL_ANNOTATION_KEY,
)

# Type alias for predicate factory functions
PredicateFactory = Callable[[etree._Element], Callable[[etree._Element], bool]]


def predicate_to_factory(predicate: Callable[[etree._Element], bool] | None) -> PredicateFactory | None:
    """Convert a traditional predicate function to a predicate factory for backwards compatibility.

    Args:
        predicate: A traditional predicate function (element -> bool) or None.

    Returns:
        A predicate factory function (root -> element predicate) or None.

    Example:
        # Old style:
        formatter = Formatter(block_predicate=is_block_element)

        # New style with helper:
        formatter = Formatter(block_predicate_factory=predicate_to_factory(is_block_element))
    """
    if predicate is None:
        return None
    return lambda root: predicate


def create_simple_predicate_factory(predicate: Callable[[etree._Element], bool]) -> PredicateFactory:
    """Create a predicate factory from a simple predicate function.

    This is useful when you have a predicate that doesn't depend on document structure
    and can be applied to any element regardless of the document it belongs to.

    Args:
        predicate: A predicate function (element -> bool).

    Returns:
        A predicate factory function (root -> element predicate).
    """
    return lambda root: predicate


class DocumentFormatter:
    """A formatter configured for a specific XML document with concrete predicates.

    DocumentFormatter is optimized for formatting a single document efficiently by
    working with concrete predicate functions that have already been bound to the
    document's structure. This avoids the overhead of re-evaluating predicates
    (such as XPath expressions) for every element.

    This class is typically used internally by the Formatter class, but can also
    be used directly when you have concrete predicate functions.
    """

    def __init__(
        self,
        *,
        block_predicate: Callable[[etree._Element], bool] | None = None,
        inline_predicate: Callable[[etree._Element], bool] | None = None,
        normalize_whitespace_predicate: Callable[[etree._Element], bool] | None = None,
        strip_whitespace_predicate: Callable[[etree._Element], bool] | None = None,
        preserve_whitespace_predicate: Callable[[etree._Element], bool] | None = None,
        wrap_attributes_predicate: Callable[[etree._Element], bool] | None = None,
        text_content_formatters: dict[Callable[[etree._Element], bool], Callable[[str, "DocumentFormatter", int], str]] | None = None,
        indent_size: Optional[int] = None,
        default_type: str | None = None,
    ):
        """Initialize a DocumentFormatter with concrete predicate functions.

        Args:
            block_predicate: Function (element -> bool) for block elements.
            inline_predicate: Function (element -> bool) for inline elements.
            normalize_whitespace_predicate: Function (element -> bool) for whitespace normalization.
            strip_whitespace_predicate: Function (element -> bool) for whitespace stripping.
            preserve_whitespace_predicate: Function (element -> bool) for whitespace preservation.
            wrap_attributes_predicate: Function (element -> bool) for attribute wrapping.
            text_content_formatters: Dictionary mapping predicates to formatter functions.
            indent_size: Number of spaces per indentation level. Defaults to 2.
            default_type: Default type for unclassified elements ("block" or "inline").
        """
        if block_predicate is None:
            block_predicate = lambda e: False

        if inline_predicate is None:
            inline_predicate = lambda e: False

        if normalize_whitespace_predicate is None:
            normalize_whitespace_predicate = lambda e: False

        if strip_whitespace_predicate is None:
            strip_whitespace_predicate = lambda e: False

        if preserve_whitespace_predicate is None:
            preserve_whitespace_predicate = lambda e: False

        if wrap_attributes_predicate is None:
            wrap_attributes_predicate = lambda e: False

        if text_content_formatters is None:
            text_content_formatters = {}

        if indent_size is None:
            indent_size = 2

        if indent_size < 0:
            raise ValueError(f"indent_size {indent_size} is less than 0")

        if default_type not in BLOCK_TYPES:
            raise ValueError(f"default_type {default_type} is not one of '{', '.join(BLOCK_TYPES)}'")

        self._mark_as_block = block_predicate
        self._mark_as_inline = inline_predicate
        self._must_normalize_whitespace = normalize_whitespace_predicate
        self._must_strip_whitespace = strip_whitespace_predicate
        self._must_preserve_whitespace = preserve_whitespace_predicate
        self._must_wrap_attributes = wrap_attributes_predicate
        self._text_content_formatters = text_content_formatters
        self._indent_char = " "
        self._indent_size = indent_size
        self._one_indent = self._indent_char * self._indent_size
        self._default_type = default_type

    @property
    def indent_char(self) -> str:
        """The character used for indentation (always a single space)."""
        return self._indent_char

    @property
    def indent_size(self) -> int:
        """The number of spaces used for each indentation level."""
        return self._indent_size

    @property
    def one_indent(self) -> str:
        """A string representing a single indentation level (indent_size spaces)."""
        return self._one_indent

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
            doctype: Optional DOCTYPE declaration to prepend to the output.

        Returns:
            A pretty-printed XML string for the element and its subtree.
        """
        # Create a parallel tree to add special attributes for formatting control
        annotations = self._annotate_tree(root)

        # Format the document using the annotated tree
        parts = []
        self._format_element(annotations, root, parts)
        return "".join(flatten(parts))

    def _annotate_tree(self, root: etree._Element) -> Annotations:
        annotations = Annotations()
        # Order matters - later annotations may read or override earlier ones
        annotate_explicit_block_elements(root, annotations, self._mark_as_block)
        annotate_explicit_inline_elements(root, annotations, self._mark_as_inline)
        annotate_elements_in_mixed_content_as_inline(root, annotations)
        annotate_inline_descendants_as_inline(root, annotations)
        annotate_unmixed_block_descendants_as_block(root, annotations)
        annotate_explicit_whitespace_preserving_elements(root, annotations, self._must_preserve_whitespace)
        annotate_whitespace_preserving_descendants_as_whitespace_preserving(root, annotations)
        annotate_explicit_whitespace_normalizing_elements(root, annotations, self._must_normalize_whitespace)
        annotate_explicit_stripped_elements(root, annotations, self._must_strip_whitespace)
        annotate_xml_space(root, annotations)
        annotate_untyped_elements_as_default(root, annotations, self._default_type)
        annotate_logical_level(root, annotations)
        annotate_physical_level(root, annotations)
        annotate_text_transforms(root, annotations, self.one_indent)
        annotate_tail_transforms(root, annotations, self.one_indent)
        return annotations

    def _format_element(self, annotations: Annotations, element: etree._Element, parts: list[str]):
        # Non-recursive, event-driven approach to formatting
        for event, node in etree.iterwalk(element, events=("start", "end", "comment", "pi")):
            if event == "start" and isinstance(node, etree._Element):
                # Opening tag
                opening_tag_parts = []
                opening_tag_parts.append(f"<{node.tag}")

                # Attribute handling
                must_wrap_attributes = self._must_wrap_attributes(node)
                if must_wrap_attributes:
                    spacer = "\n" + self._one_indent * (int(annotations.annotation(node, "physical_level", 0)) + 1)
                else:
                    spacer = " "

                real_attributes = {k: v for k, v in node.attrib.items() if not k.startswith("_")}
                for k, v in real_attributes.items():
                    k_qname = etree.QName(k)
                    if k_qname.namespace:
                        if k_qname.namespace == "http://www.w3.org/XML/1998/namespace":
                            prefix = "xml"
                        else:
                            prefix = node.nsmap.get(k_qname.namespace)
                        if prefix:
                            k = f"{prefix}:{k_qname.localname}"
                        else:
                            k = k_qname.localname
                    escaped_value = quoteattr(v)
                    opening_tag_parts.append(f'{spacer}{k}={escaped_value}')
                if real_attributes and must_wrap_attributes:
                    opening_tag_parts.append("\n" + self._one_indent * int(annotations.annotation(node, "physical_level", 0)))

                is_self_closing = self._is_self_closing(annotations, node)

                if is_self_closing:
                    if not must_wrap_attributes:
                        opening_tag_parts.append(" ")
                    opening_tag_parts.append("/")

                opening_tag_parts.append(">")
                parts.append(opening_tag_parts)

                # Content
                if not is_self_closing:
                    if text := self._text_content(annotations, node):
                        escaped_text = escape(text)
                        parts.append(escaped_text)

            elif event == "end" and isinstance(node, etree._Element):
                if not self._is_self_closing(annotations, node):
                    # Closing tag
                    closing_tag_parts = [f"</{node.tag}>"]
                    parts.append(closing_tag_parts)

                # Tail
                if tail := self._tail_content(annotations, node):
                    escaped_tail = escape(tail)
                    parts.append(escaped_tail)

            elif event == "comment" and isinstance(node, etree._Comment):
                parts.append("<!--")
                if text := self._text_content(annotations, node):
                    escaped_text = escape(text)
                    if escaped_text.startswith("-"):
                        parts.append(" ")
                    parts.append(escaped_text)
                    if escaped_text.endswith("-"):
                        parts.append(" ")
                parts.append("-->")
                # Tail
                if tail := self._tail_content(annotations, node):
                    escaped_tail = escape(tail)
                    parts.append(escaped_tail)

            elif event == "pi" and isinstance(node, etree._ProcessingInstruction):
                pi_parts = []
                pi_parts.append(f"<?{node.target}")
                if node.text:
                    pi_parts.append(f" {node.text}")
                pi_parts.append("?>")
                parts.append(pi_parts)
                # Tail
                if tail := self._tail_content(annotations, node):
                    escaped_tail = escape(tail)
                    parts.append(escaped_tail)

            else:
                raise RuntimeError(f"Unexpected event {event} for node {node}")

    def _is_self_closing(self, annotations, element: etree._Element) -> bool:
        text = self._text_content(annotations, element)
        return (not bool(text)) and len(element) == 0

    def _text_content(self, annotations, element):
        text = element.text or ""

        text_transforms = annotations.annotation(element, "text_transforms", [])
        for transform in text_transforms:
            text = transform(text)

        physical_level = annotations.annotation(element, PHYSICAL_LEVEL_ANNOTATION_KEY, 0)

        for predicate, format_func in self._text_content_formatters.items():
            if predicate(element):
                text = format_func(text, self, physical_level)
                break
        return text

    def _tail_content(self, annotations, element):
        tail = element.tail or ""

        tail_transforms = annotations.annotation(element, "tail_transforms", [])
        for transform in tail_transforms:
            tail = transform(tail)
        return tail


class Formatter:
    """A configurable formatter for XML documents using predicate factories.

    The Formatter class provides a flexible and extensible way to pretty-print and normalize XML documents.
    It uses predicate factory functions that are evaluated once per document for maximum performance,
    especially beneficial for XPath-based predicates.

    Predicate factories take a document root element and return optimized predicate functions
    that can efficiently test any element against the criteria. This avoids re-evaluating
    expensive operations like XPath queries for every element.

    The Formatter delegates the actual formatting work to DocumentFormatter instances,
    which are created with concrete predicates for optimal performance.
    """

    def __init__(
        self,
        *,
        block_predicate_factory: PredicateFactory | None = None,
        inline_predicate_factory: PredicateFactory | None = None,
        normalize_whitespace_predicate_factory: PredicateFactory | None = None,
        strip_whitespace_predicate_factory: PredicateFactory | None = None,
        preserve_whitespace_predicate_factory: PredicateFactory | None = None,
        wrap_attributes_predicate_factory: PredicateFactory | None = None,
        text_content_formatters: dict[PredicateFactory, Callable[[str, DocumentFormatter, int], str]] | None = None,
        indent_size: Optional[int] = None,
        default_type: str | None = None,
    ):
        """Initialize a Formatter with predicate factory functions.

        Args:
            block_predicate_factory: Factory function (root -> element predicate) for block elements.
            inline_predicate_factory: Factory function (root -> element predicate) for inline elements.
            normalize_whitespace_predicate_factory: Factory for whitespace normalization predicates.
            strip_whitespace_predicate_factory: Factory for whitespace stripping predicates.
            preserve_whitespace_predicate_factory: Factory for whitespace preservation predicates.
            wrap_attributes_predicate_factory: Factory for attribute wrapping predicates.
            text_content_formatters: Dictionary mapping predicate factories to formatter functions.
            indent_size: Number of spaces per indentation level. Defaults to 2.
            default_type: Default type for unclassified elements ("block" or "inline").
        """
        self._block_predicate_factory = block_predicate_factory or (lambda root: lambda e: False)
        self._inline_predicate_factory = inline_predicate_factory or (lambda root: lambda e: False)
        self._normalize_predicate_factory = normalize_whitespace_predicate_factory or (lambda root: lambda e: False)
        self._strip_predicate_factory = strip_whitespace_predicate_factory or (lambda root: lambda e: False)
        self._preserve_predicate_factory = preserve_whitespace_predicate_factory or (lambda root: lambda e: False)
        self._wrap_attributes_factory = wrap_attributes_predicate_factory or (lambda root: lambda e: False)
        self._text_content_formatter_factories = text_content_formatters or {}
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
