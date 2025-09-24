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

    def __init__(
        self,
        block_predicate: Callable[[etree._Element], bool] | None = None,
        inline_predicate: Callable[[etree._Element], bool] | None = None,
        normalize_whitespace_predicate: Callable[[etree._Element], bool] | None = None,
        strip_whitespace_predicate: Callable[[etree._Element], bool] | None = None,
        preserve_whitespace_predicate: Callable[[etree._Element], bool] | None = None,
        wrap_attributes_predicate: Callable[[etree._Element], bool] | None = None,
        text_content_formatters: dict[Callable[[etree._Element], bool], Callable[[str, "Formatter", int], str]] | None = None,
        indent_size = None,
        # TODO: Add an option for attribute_content_formatters (for e.g. wrapping style attributes)
        default_type: str | None = None,
    ):
        """Initialize the formatter.

        Args:
            block_predicate: A function that takes an lxml.etree.Element and returns True if it
                should be treated as a block element. If None, no elements are definitively treated
                as block elements. Elements not selected by either block_predicate or inline_predicate
                will be treated as block elements if they have any block children, and as inline
                elements if they have only inline children or no children.

            inline_predicate: A function that takes an lxml.etree.Element and returns True if it
                should be treated as an inline element. If None, no elements are definitively
                treated as inline elements. Elements not selected by either block_predicate or
                inline_predicate will be treated as block elements if they have any block children,
                and as inline elements if they have only inline children or no children.

            normalize_whitespace_predicate: A function that takes an lxml.etree.Element and returns
                True if the whitespace in its text content should be normalized (i.e., leading and
                trailing whitespace removed, and internal sequences of whitespace replaced with a
                single space). This does not apply to tail text. If None, no elements have their
                whitespace normalized. It is an error for an element to match both normalize_whitespace_predicate
                and preserve_whitespace_predicate.

            strip_whitespace_predicate: A function that takes an lxml.etree.Element and returns
                True if the whitespace in its text content should be stripped (i.e., all leading and
                trailing whitespace removed).

            preserve_whitespace_predicate: A function that takes an lxml.etree.Element and returns
                True if the whitespace in its content if the whitespace in its text content should
                be preserved. Note that this can be overridden by xml:space="preserve"
                or xml:space="default" and is lower precedence than the
                normalize_whitespace_predicate, so if an element matches both predicates
                the normalize_whitespace_predicate takes precedence.

            wrap_attributes_predicate: A function that takes an lxml.etree.Element and returns True
                if its attributes should be wrapped onto multiple lines even if they would fit on a
                single line. If None, no elements have their attributes wrapped.

            text_content_formatters: A dictionary mapping predicates (functions that take an
                lxml.etree.Element and return True or False) to formatter functions (functions that
                take a string a reference to a Formatter object and a physical indentation level).
                If an element matches a predicate in the dictionary, its text content will be passed
                to the corresponding formatter function before being included in the output. If the
                formatter function is None, the
                text content will be included as-is. If multiple predicates match an element, the
                formatter function for the first matching predicate will be used. If None, no special
                formatting is applied to any element's text content.

            indent_size: The number of spaces to use for each indentation level. Must be a non-negative

            default_type: The default type for elements that are not explicitly marked as block or inline,
                and which don't otherwise have their type inferred contextually. Either "block" or "inline".
                Default is "block".
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
        return self._indent_char

    @property
    def indent_size(self) -> int:
        return self._indent_size

    @property
    def one_indent(self) -> str:
        return self._one_indent

    def format_file(self, file_path: str, doctype: str | None = None, xml_declaration: Optional[bool] = None) -> str:
        """Format a markup document from a file.

        Args:
            file_path: The path to the file containing the markup document.
            doctype: An optional DOCTYPE declaration to prepend to the output document. This should
                include the surrounding <!DOCTYPE ...> markup.

        Returns:
            A pretty-printed XML string.
        """
        tree = etree.parse(file_path)
        return self.format_tree(tree, doctype=doctype, xml_declaration=xml_declaration)

    def format_str(self, doc: str, doctype: str | None = None, xml_declaration: Optional[bool] = None) -> str:
        """Format a markup document.

        Args:
            doc: A string that can be parsed as XML.
            doctype: An optional DOCTYPE declaration to prepend to the output document. This should
                 include the surrounding <!DOCTYPE ...> markup.

        Returns:
            A pretty-printed XML string.
        """
        tree = etree.parse(BytesIO(doc.encode()))
        return self.format_tree(tree, doctype, xml_declaration)

    def format_bytes(self, doc: bytes, doctype: str | None = None, xml_declaration: Optional[bool] = None) -> str:
        """Format a markup document.

        Args:
            doc: A bytes object that can be parsed as XML.
            doctype: An optional DOCTYPE declaration to prepend to the output document. This should
                 include the surrounding <!DOCTYPE ...> markup.

        Returns:
            A pretty-printed XML string.
        """
        tree = etree.parse(BytesIO(doc))
        return self.format_tree(tree, doctype, xml_declaration)

    def format_tree(self, tree: etree._ElementTree, doctype: str | None = None, xml_declaration: Optional[bool] = None) -> str:
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
        # Create a parallel tree to which we can add special attributes to each element to control
        # formatting.
        annotations = self._annotate_tree(root)

        # Now we can format the document using the annotated tree to guide the formatting.
        parts = []
        self._format_element(annotations, root, parts)
        pprint(parts)
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
