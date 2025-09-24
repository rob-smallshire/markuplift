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


class Formatter:
    """A configurable formatter for XML documents.

    The Formatter class provides a flexible and extensible way to pretty-print and normalize XML documents.
    It allows users to control the formatting of elements, attributes, and text content through a variety
    of user-supplied predicate functions and formatting options. The Formatter can:

    - Distinguish between block and inline elements using user-defined predicates, or infer types contextually.
    - Normalize, strip, or preserve whitespace in element text content based on predicates or xml:space attributes.
    - Apply custom formatting to text content using a mapping of predicates to formatter functions.
    - Control attribute wrapping and indentation for improved readability.
    - Handle comments, processing instructions, and DOCTYPE declarations appropriately.
    - Output well-formed, indented XML as a string, with optional XML declaration and DOCTYPE.

    The class is designed to be extensible and composable, making it suitable for a wide range of XML
    formatting and transformation tasks, including:

    - Reformatting XML for human readability or code review.
    - Enforcing consistent whitespace and attribute layout in XML documents.
    - Preparing XML for downstream processing or diffing.
    - Supporting custom markup dialects with specialized formatting needs.

    Clients can customize the Formatter by supplying their own predicate functions for block/inline
    detection, whitespace handling, and attribute wrapping, as well as custom text content
    formatters for embedded source code or data such as JavaScript, CSS, or JSON.
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
        text_content_formatters: dict[Callable[[etree._Element], bool], Callable[[str, "Formatter", int], str]] | None = None,
        # TODO: Add an option for attribute_content_formatters (for e.g. wrapping style attributes)
        indent_size: Optional[int] = None,
        default_type: str | None = None,
    ):
        """Initialize a Formatter instance with customizable formatting logic.

        Args:
            block_predicate: Optional function (element -> bool). If provided, elements for which this returns True
                are always treated as block elements. If None, no elements are explicitly block by this predicate.

            inline_predicate: Optional function (element -> bool). If provided, elements for which this returns True
                are always treated as inline elements. If None, no elements are explicitly inline by this predicate.

            normalize_whitespace_predicate: Optional function (element -> bool). If provided, elements for which this returns True
                will have their text content whitespace normalized (leading/trailing whitespace removed, internal whitespace collapsed).
                This does not affect tail text. It is an error for an element to match both this and preserve_whitespace_predicate.

            strip_whitespace_predicate: Optional function (element -> bool). If provided, elements for which this returns True
                will have all leading and trailing whitespace stripped from their text content.

            preserve_whitespace_predicate: Optional function (element -> bool). If provided, elements for which this returns True
                will have their text content whitespace preserved. This can be overridden by xml:space attributes or by
                normalize_whitespace_predicate (which takes precedence if both match).

            wrap_attributes_predicate: Optional function (element -> bool). If provided, elements for which this returns True
                will have their attributes wrapped onto multiple lines, even if they would fit on a single line.

            text_content_formatters: Optional dictionary mapping predicate functions (element -> bool) to formatter functions.
                Each predicate is a function that takes an element and returns True or False. Each formatter is a function
                that takes (text: str, formatter: Formatter, physical_level: int) and returns a formatted string.
                For each element, the first predicate that matches determines the formatter to use for its text content.
                If None, no special formatting is applied to any element's text content.

            indent_size: Number of spaces to use for each indentation level. Must be non-negative. Defaults to 2.

            default_type: The default type for elements not explicitly marked as block or inline, and not contextually inferred.
                Must be either "block" or "inline". Defaults to "block".
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
            doctype: Optional DOCTYPE declaration to prepend to the output. If not provided, uses the DOCTYPE from the file if available.
            xml_declaration: If True, includes an XML declaration at the top of the output. If None, defaults to False.

        Returns:
            A pretty-printed XML string.
        """
        tree = etree.parse(file_path)
        return self.format_tree(tree, doctype=doctype, xml_declaration=xml_declaration)

    def format_str(self, doc: str, doctype: str | None = None, xml_declaration: Optional[bool] = None) -> str:
        """Format an XML document from a string.

        Args:
            doc: XML document as a string.
            doctype: Optional DOCTYPE declaration to prepend to the output. If not provided, uses the DOCTYPE from the document if available.
            xml_declaration: If True, includes an XML declaration at the top of the output. If None, defaults to False.

        Returns:
            A pretty-printed XML string.
        """
        tree = etree.parse(BytesIO(doc.encode()))
        return self.format_tree(tree, doctype, xml_declaration)

    def format_bytes(self, doc: bytes, doctype: str | None = None, xml_declaration: Optional[bool] = None) -> str:
        """Format an XML document from bytes.

        Args:
            doc: XML document as bytes.
            doctype: Optional DOCTYPE declaration to prepend to the output. If not provided, uses the DOCTYPE from the document if available.
            xml_declaration: If True, includes an XML declaration at the top of the output. If None, defaults to False.

        Returns:
            A pretty-printed XML string.
        """
        tree = etree.parse(BytesIO(doc))
        return self.format_tree(tree, doctype, xml_declaration)

    def format_tree(self, tree: etree._ElementTree, doctype: str | None = None, xml_declaration: Optional[bool] = None) -> str:
        """Format an XML document from an lxml ElementTree.

        Args:
            tree: An lxml.etree._ElementTree representing the XML document.
            doctype: Optional DOCTYPE declaration to prepend to the output. If not provided, uses the DOCTYPE from the tree if available.
            xml_declaration: If True, includes an XML declaration at the top of the output. If None, defaults to False.

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

        # Retrieve all comments and processing instructions that are direct children of the document and before
        # the root element. I've been advised that we need to use iterwalk here. We'll just iterate
        # enough to collect the PIs before the root element and add render them into parts before
        # breaking out of the loop.
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
                # We've reached the root element, so we can stop processing.
                break

        formatted = self.format_element(tree.getroot(), doctype)
        if formatted:
            parts.append(formatted)

        return "".join(flatten(parts))

    def format_element(self, root: etree._Element, doctype: str | None = None) -> str:
        """Format a single XML element and its descendants.

        Args:
            root: The root lxml.etree._Element to format.
            doctype: Optional DOCTYPE declaration to prepend to the output. Not used in this method, but included for API consistency.

        Returns:
            A pretty-printed XML string for the element and its subtree.
        """
        # Create a parallel tree to which we can add special attributes to each element to control
        # formatting.
        annotations = self._annotate_tree(root)

        # Now we can format the document using the annotated tree to guide the formatting.
        parts = []
        self._format_element(annotations, root, parts)
        return "".join(flatten(parts))

    def _annotate_tree(self, root: etree._Element) -> Annotations:
        annotations = Annotations()
        # Later annotations may read or override annotations made earlier, so the order here matters.
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
        # A non-recursive, event-driven approach to formatting the element and its children.
        for event, node in etree.iterwalk(element, events=("start", "end", "comment", "pi")):
            if event == "start" and isinstance(node, etree._Element):
                # FIRST TAG
                opening_tag_parts = []
                opening_tag_parts.append(f"<{node.tag}")

                # Set the attribute spacer to a single space or a newline and indentation depending on whether
                # the attributes should be wrapped.
                must_wrap_attributes = self._must_wrap_attributes(node)
                if must_wrap_attributes:
                    spacer = "\n" + self._one_indent * (int(annotations.annotation(node, "physical_level", 0)) + 1)
                else:
                    spacer = " "

                real_attributes = {k: v for k, v in node.attrib.items() if not k.startswith("_")}
                for k, v in real_attributes.items():
                    k_qname = etree.QName(k)
                    if k_qname.namespace:
                        # Attribute has a namespace, so we need to include the prefix.
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

                # CONTENT
                if not is_self_closing:
                    if text := self._text_content(annotations, node):
                        escaped_text = escape(text)
                        parts.append(escaped_text)

            elif event == "end" and isinstance(node, etree._Element):
                if not self._is_self_closing(annotations, node):
                    # CLOSING TAG (if not self-closing)
                    closing_tag_parts = [f"</{node.tag}>"]
                    parts.append(closing_tag_parts)

                # TAIL
                if tail := self._tail_content(annotations, node):
                    escaped_tail = escape(tail)
                    parts.append(escaped_tail)

            elif event == "comment" and isinstance(node, etree._Comment):
                # For now, assume that comments also have information available in annotations.
                # TODO: Modify the annotation logic to handle comments properly.
                parts.append("<!--")
                if text := self._text_content(annotations, node):
                    escaped_text = escape(text)
                    if escaped_text.startswith("-"):
                        parts.append(" ")
                    parts.append(escaped_text)
                    if escaped_text.endswith("-"):
                        parts.append(" ")
                parts.append("-->")
                # TAIL
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
                # TAIL
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
