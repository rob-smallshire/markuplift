"""Document-specific XML/HTML formatter implementation.

This module provides the DocumentFormatter class, which performs the actual
formatting work for XML and HTML documents. It operates with concrete ElementPredicate
functions that have been optimized for a specific document, avoiding the overhead
of re-evaluating predicates for every element.

The DocumentFormatter handles the low-level details of XML serialization, whitespace
processing, indentation, and text content formatting using TextContentFormatter functions.
"""

from io import BytesIO
from typing import Optional, Sequence
from functools import singledispatchmethod
from lxml.etree import CDATA

# Import type aliases
from markuplift.types import (
    ElementPredicate,
    TextContentFormatter,
    AttributePredicate,
    AttributeValueFormatter,
    AttributeReorderer,
    ElementType,
    TextContent,
)

# Import standard predicates
from markuplift.predicates import never_match

# Import utilities
# Import escaping strategies
from markuplift.escaping import EscapingStrategy, XmlEscapingStrategy

# Import doctype strategies
from markuplift.doctype import DoctypeStrategy, NullDoctypeStrategy

# Import attribute formatting strategies
from markuplift.attribute_formatting import AttributeFormattingStrategy, NullAttributeStrategy

from lxml import etree
from markuplift.annotation import (
    BLOCK_TYPES,
    Annotations,
    annotate_explicit_block_elements,
    annotate_explicit_inline_elements,
    annotate_elements_in_mixed_content_as_inline,
    annotate_inline_descendants_as_inline,
    annotate_unmixed_block_descendants_as_block,
    annotate_explicit_whitespace_preserving_elements,
    annotate_whitespace_preserving_descendants_as_whitespace_preserving,
    annotate_explicit_whitespace_normalizing_elements,
    annotate_explicit_stripped_elements,
    annotate_xml_space,
    annotate_untyped_elements_as_default,
    annotate_logical_level,
    annotate_physical_level,
    annotate_text_transforms,
    annotate_tail_transforms,
    PHYSICAL_LEVEL_ANNOTATION_KEY,
)


class DocumentFormatter:
    """A formatter configured for a specific XML document with concrete ElementPredicate functions.

    DocumentFormatter is optimized for formatting a single document efficiently by
    working with concrete ElementPredicate functions that have already been bound to the
    document's structure. This avoids the overhead of re-evaluating predicates
    (such as XPath expressions) for every element.

    The formatter uses TextContentFormatter functions to process element text content
    and applies various whitespace processing rules based on the provided predicates.

    This class is typically used internally by the Formatter class, but can also
    be used directly when you have concrete ElementPredicate functions.

    Args:
        block_predicate: ElementPredicate for identifying block-level elements
        inline_predicate: ElementPredicate for identifying inline elements
        normalize_whitespace_predicate: ElementPredicate for whitespace normalization
        strip_whitespace_predicate: ElementPredicate for whitespace stripping
        preserve_whitespace_predicate: ElementPredicate for whitespace preservation
        wrap_attributes_predicate: ElementPredicate for attribute wrapping
        text_content_formatters: Dict mapping ElementPredicate to TextContentFormatter
        attribute_reorderers: Dict mapping ElementPredicate to AttributeReorderer
        indent_size: Number of spaces per indentation level
        default_type: Default element type for unclassified elements
    """

    def __init__(
        self,
        *,
        block_predicate: ElementPredicate | None = None,
        inline_predicate: ElementPredicate | None = None,
        normalize_whitespace_predicate: ElementPredicate | None = None,
        strip_whitespace_predicate: ElementPredicate | None = None,
        preserve_whitespace_predicate: ElementPredicate | None = None,
        wrap_attributes_predicate: ElementPredicate | None = None,
        text_content_formatters: dict[ElementPredicate, TextContentFormatter] | None = None,
        attribute_content_formatters: dict[AttributePredicate, AttributeValueFormatter] | None = None,
        attribute_reorderers: dict[ElementPredicate, AttributeReorderer] | None = None,
        escaping_strategy: EscapingStrategy | None = None,
        doctype_strategy: DoctypeStrategy | None = None,
        attribute_strategy: AttributeFormattingStrategy | None = None,
        indent_size: Optional[int] = None,
        default_type: ElementType | None = None,
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
            attribute_content_formatters: Dictionary mapping attribute predicates to formatter functions.
            attribute_reorderers: Dictionary mapping element predicates to attribute reorderer functions.
            escaping_strategy: Strategy for escaping text and attribute values. Defaults to XmlEscapingStrategy.
            doctype_strategy: Strategy for handling DOCTYPE declarations. Defaults to NullDoctypeStrategy.
            attribute_strategy: Strategy for formatting attributes. Defaults to NullAttributeStrategy.
            indent_size: Number of spaces per indentation level. Defaults to 2.
            default_type: Default type for unclassified elements (ElementType enum).
        """
        if block_predicate is None:
            block_predicate = never_match

        if inline_predicate is None:
            inline_predicate = never_match

        if normalize_whitespace_predicate is None:
            normalize_whitespace_predicate = never_match

        if strip_whitespace_predicate is None:
            strip_whitespace_predicate = never_match

        if preserve_whitespace_predicate is None:
            preserve_whitespace_predicate = never_match

        if wrap_attributes_predicate is None:
            wrap_attributes_predicate = never_match

        if text_content_formatters is None:
            text_content_formatters = {}

        if attribute_content_formatters is None:
            attribute_content_formatters = {}

        if attribute_reorderers is None:
            attribute_reorderers = {}

        if escaping_strategy is None:
            escaping_strategy = XmlEscapingStrategy()

        if doctype_strategy is None:
            doctype_strategy = NullDoctypeStrategy()

        if attribute_strategy is None:
            attribute_strategy = NullAttributeStrategy()

        if indent_size is None:
            indent_size = 2

        if indent_size < 0:
            raise ValueError(f"indent_size {indent_size} is less than 0")

        # Note: None is a valid value in BLOCK_TYPES and means "let context decide"

        if default_type not in BLOCK_TYPES:
            raise ValueError(f"default_type {default_type} is not one of '{', '.join(str(t) for t in BLOCK_TYPES)}'")

        self._mark_as_block = block_predicate
        self._mark_as_inline = inline_predicate
        self._must_normalize_whitespace = normalize_whitespace_predicate
        self._must_strip_whitespace = strip_whitespace_predicate
        self._must_preserve_whitespace = preserve_whitespace_predicate
        self._must_wrap_attributes = wrap_attributes_predicate
        self._text_content_formatters = text_content_formatters
        self._attribute_content_formatters = attribute_content_formatters
        self._attribute_reorderers = attribute_reorderers
        self._escaping_strategy = escaping_strategy
        self._doctype_strategy = doctype_strategy
        self._attribute_strategy = attribute_strategy
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
        parts = []

        if xml_declaration is None:
            xml_declaration = False

        if xml_declaration:
            parts.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')

        resolved_doctype = self._resolve_doctype(tree, doctype, is_full_document=True)
        if resolved_doctype:
            parts.extend([resolved_doctype, "\n"])

        # Handle comments and PIs before root element
        for event, node in etree.iterwalk(tree, events=("comment", "pi", "start")):
            if event == "comment" and isinstance(node, etree._Comment):
                parts.append("<!--")
                if text := node.text:
                    escaped_text = self._escaping_strategy.escape_comment_text(text)
                    if escaped_text.startswith("-"):
                        parts.append(" ")
                    parts.append(escaped_text)
                    if escaped_text.endswith("-"):
                        parts.append(" ")
                parts.append("-->\n")
            elif event == "pi" and isinstance(node, etree._ProcessingInstruction):
                parts.append(f"<?{node.target}")
                if node.text:
                    parts.append(f" {node.text}")
                parts.append("?>\n")
            elif event == "start" and isinstance(node, etree._Element):
                # Reached root element, stop processing
                break

        formatted = self.format_element(tree.getroot())
        if formatted:
            parts.append(formatted)

        return "".join(parts)

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

        # Only add DOCTYPE if explicitly provided (no automatic DOCTYPE for subtrees)
        if doctype:
            parts.extend([doctype, "\n"])

        self._format_element(annotations, root, parts)
        return "".join(parts)

    def _resolve_doctype(
        self, tree: etree._ElementTree, explicit_doctype: str | None, is_full_document: bool
    ) -> str | None:
        """Resolve the appropriate DOCTYPE declaration using the DOCTYPE strategy.

        Args:
            tree: The ElementTree being formatted
            explicit_doctype: Explicitly provided DOCTYPE override, or None
            is_full_document: True if formatting a complete document, False for subtrees

        Returns:
            The DOCTYPE string to use, or None if no DOCTYPE should be included

        Resolution logic:
            1. Explicit doctype parameter always takes precedence
            2. Never add DOCTYPE to subtree formatting
            3. If strategy should_ensure_doctype(), use strategy default
            4. Otherwise preserve existing DOCTYPE from tree
            5. Fall back to strategy default if no existing DOCTYPE
        """
        # User override always wins
        if explicit_doctype is not None:
            return explicit_doctype

        # Never add DOCTYPE to subtrees
        if not is_full_document:
            return None

        # Get existing DOCTYPE from the parsed tree
        existing_doctype = tree.docinfo.doctype if hasattr(tree, "docinfo") else None

        # If strategy enforces a specific DOCTYPE, use it
        if self._doctype_strategy.should_ensure_doctype():
            return self._doctype_strategy.get_default_doctype()

        # Otherwise preserve existing or use strategy default
        return existing_doctype or self._doctype_strategy.get_default_doctype()

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
                parts.append(f"<{node.tag}")

                # Attribute handling
                must_wrap_attributes = self._must_wrap_attributes(node)
                if must_wrap_attributes:
                    spacer = "\n" + self._one_indent * (int(annotations.annotation(node, "physical_level", 0)) + 1)
                else:
                    spacer = " "

                real_attributes = {k: v for k, v in node.attrib.items() if not k.startswith("_")}

                # Apply attribute reordering if reorderer matches
                attribute_names = list(real_attributes.keys())
                for predicate, reorderer_func in self._attribute_reorderers.items():
                    if predicate(node):
                        reordered_names = reorderer_func(attribute_names)
                        self._validate_attribute_reordering(reordered_names, attribute_names, node.tag)
                        attribute_names = list(reordered_names)
                        break

                for k in attribute_names:
                    v = real_attributes[k]
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
                    # Apply attribute formatters using strategy pattern
                    physical_level = annotations.annotation(node, PHYSICAL_LEVEL_ANNOTATION_KEY, 0)
                    formatted_value, should_minimize = self._attribute_strategy.format_attribute(
                        node, k, v, self._attribute_content_formatters, self, physical_level + int(must_wrap_attributes)
                    )

                    if should_minimize:
                        # Strategy determined this attribute should be minimized (e.g., HTML5 boolean attributes)
                        parts.append(f"{spacer}{k}")
                    else:
                        escaped_value = self._escaping_strategy.quote_attribute(formatted_value)
                        parts.append(f"{spacer}{k}={escaped_value}")
                if real_attributes and must_wrap_attributes:
                    parts.append("\n" + self._one_indent * int(annotations.annotation(node, "physical_level", 0)))

                is_self_closing = self._is_self_closing(annotations, node)

                if is_self_closing:
                    if not must_wrap_attributes:
                        parts.append(" ")
                    parts.append("/")

                parts.append(">")

                # Content
                if not is_self_closing:
                    if text := self._text_content(annotations, node):
                        escaped_text = self._escape_text_content(text)
                        parts.append(escaped_text)

            elif event == "end" and isinstance(node, etree._Element):
                if not self._is_self_closing(annotations, node):
                    # Closing tag
                    parts.append(f"</{node.tag}>")

                # Tail
                if tail := self._tail_content(annotations, node):
                    escaped_tail = self._escape_text_content(tail)
                    parts.append(escaped_tail)

            elif event == "comment" and isinstance(node, etree._Comment):
                parts.append("<!--")
                if text := self._text_content(annotations, node):
                    escaped_text = self._escape_comment_text_content(text)
                    if escaped_text.startswith("-"):
                        parts.append(" ")
                    parts.append(escaped_text)
                    if escaped_text.endswith("-"):
                        parts.append(" ")
                parts.append("-->")
                # Tail
                if tail := self._tail_content(annotations, node):
                    escaped_tail = self._escape_text_content(tail)
                    parts.append(escaped_tail)

            elif event == "pi" and isinstance(node, etree._ProcessingInstruction):
                parts.append(f"<?{node.target}")
                if node.text:
                    parts.append(f" {node.text}")
                parts.append("?>")
                # Tail
                if tail := self._tail_content(annotations, node):
                    escaped_tail = self._escape_text_content(tail)
                    parts.append(escaped_tail)

            else:
                raise RuntimeError(f"Unexpected event {event} for node {node}")

    def _is_self_closing(self, annotations, element: etree._Element) -> bool:
        text = self._text_content(annotations, element)
        return (not bool(text)) and len(element) == 0

    def _validate_attribute_reordering(
        self, reordered: Sequence[str], original: Sequence[str], element_tag: str
    ) -> None:
        """Validate that reordered is a valid permutation of original.

        Args:
            reordered: The reordered list of attribute names returned by reorderer
            original: The original list of attribute names
            element_tag: The tag name of the element (for error messages)

        Raises:
            ValueError: If reordered is not a valid permutation of original
        """
        if len(original) != len(reordered):
            raise ValueError(
                f"Attribute reorderer for <{element_tag}> returned {len(reordered)} "
                f"attributes but received {len(original)}"
            )

        original_set = set(original)
        reordered_set = set(reordered)

        if original_set != reordered_set:
            missing = original_set - reordered_set
            extra = reordered_set - original_set
            msg_parts = [f"Attribute reorderer for <{element_tag}> returned invalid reordering:"]
            if missing:
                msg_parts.append(f"  Missing: {sorted(missing)}")
            if extra:
                msg_parts.append(f"  Extra: {sorted(extra)}")
            raise ValueError("\n".join(msg_parts))

        if len(reordered) != len(reordered_set):
            # Find duplicates
            from collections import Counter

            counts = Counter(reordered)
            duplicates = [name for name, count in counts.items() if count > 1]
            raise ValueError(
                f"Attribute reorderer for <{element_tag}> returned duplicate "
                f"attributes: {sorted(duplicates)}"
            )

    def _text_content(self, annotations, element) -> TextContent:
        # Get the original text content, which may be a CDATA object
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

    def _tail_content(self, annotations, element) -> TextContent:
        tail = element.tail or ""

        tail_transforms = annotations.annotation(element, "tail_transforms", [])
        for transform in tail_transforms:
            tail = transform(tail)
        return tail

    @singledispatchmethod
    def _escape_text_content(self, content) -> str:
        """Escape text content appropriately based on type.

        Args:
            content: Text content to escape

        Returns:
            Escaped string content appropriate for XML output

        Raises:
            NotImplementedError: If no handler is registered for the content type
        """
        raise NotImplementedError(f"No text content handler for type {type(content)}")

    @_escape_text_content.register
    def _(self, content: str) -> str:
        """Handle regular string content with normal escaping."""
        return self._escaping_strategy.escape_text(content)

    @_escape_text_content.register
    def _(self, content: CDATA) -> str:
        """Handle CDATA content with safe CDATA serialization."""
        # Extract content via temporary element
        from lxml.etree import Element
        temp_element = Element("temp")
        temp_element.text = content
        actual_content = temp_element.text

        # Use separate method for safe CDATA rendering
        return self._render_safe_cdata(actual_content)

    def _render_safe_cdata(self, content: str) -> str:
        """Safely render content as CDATA, handling ]]> sequences.

        The XML specification prohibits the string ']]>' inside CDATA sections.
        When this sequence appears, we split at each occurrence: everything up to
        and including ']]' goes in a CDATA section, then we escape just the '>'.

        Args:
            content: The string content to wrap in CDATA

        Returns:
            Safe CDATA representation that is valid XML

        Examples:
            >>> formatter._render_safe_cdata("simple content")
            '<![CDATA[simple content]]>'

            >>> formatter._render_safe_cdata("before]]>after")
            '<![CDATA[before]]]]>&gt;<![CDATA[after]]>'

            >>> formatter._render_safe_cdata("]]>")
            ']]&gt;'
        """
        # Handle empty content
        if not content:
            return "<![CDATA[]]>"

        # If no problematic sequences, simple case
        if "]]>" not in content:
            return f"<![CDATA[{content}]]>"

        # Handle content that starts with ]]>
        if content.startswith("]]>"):
            if len(content) == 3:  # Just "]]>"
                return "]]&gt;"
            # Process remainder
            remainder = content[3:]
            return "]]&gt;" + self._render_safe_cdata(remainder)

        # Split on ]]> and rebuild safely
        result = ""
        remaining = content

        while "]]>" in remaining:
            # Find the first ]]> occurrence
            pos = remaining.find("]]>")

            if pos == 0:
                # Starts with ]]>, just escape it
                result += "]]&gt;"
                remaining = remaining[3:]
            else:
                # Everything up to and including ]] goes in CDATA
                before_and_brackets = remaining[:pos + 2]  # includes the ]]
                result += f"<![CDATA[{before_and_brackets}]]>"

                # Escape the >
                result += "&gt;"

                # Continue with the rest
                remaining = remaining[pos + 3:]

        # Add any remaining content in CDATA
        if remaining:
            result += f"<![CDATA[{remaining}]]>"

        return result

    def _escape_comment_text_content(self, content: TextContent) -> str:
        """Escape comment text content appropriately, handling CDATA objects.

        Args:
            content: Comment text content that may be a string or CDATA object

        Returns:
            Escaped string content appropriate for comments
        """
        if isinstance(content, CDATA):
            # CDATA objects don't need escaping for comments
            return str(content)
        else:
            # Regular strings need comment-specific escaping
            return self._escaping_strategy.escape_comment_text(content)
