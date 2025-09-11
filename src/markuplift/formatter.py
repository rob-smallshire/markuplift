from itertools import groupby
from pprint import pprint
from typing import Callable, Any
from xml.sax.saxutils import quoteattr, escape

from les_iterables import flatten
from lxml import etree

FALSE = ""  # Empty string is falsey when evaluated as a bool

TRUE = "true"


class Annotations:

    def __init__(self):
        self._annotations: dict[etree._Element, dict[str, str]] = {}

    def annotate(self, element: etree._Element, attribute_name: str, attribute_value: Any):
        if element not in self._annotations:
            self._annotations[element] = {}
        self._annotations[element][attribute_name] = attribute_value

    def annotation(self, element: etree._Element, attribute_name: str, default: Any = None) ->Any:
        return self._annotations.get(element, {}).get(attribute_name, default)


class Formatter:

    def __init__(
        self,
        block_predicate: Callable[[etree._Element], bool] | None = None,
        normalize_whitespace_predicate: Callable[[etree._Element], bool] | None = None,
        preserve_whitespace_predicate: Callable[[etree._Element], bool] | None = None,
        wrap_attributes_predicate: Callable[[etree._Element], bool] | None = None,
        text_content_formatters: dict[Callable[[etree._Element], bool], Callable[[etree._Element], str]] | None = None,
        indent_size = None,
        # TODO: Add an option for attribute_content_formatters (for e.g. wrapping style attributes)
    ):
        """Initialize the formatter.

        Args:
            block_predicate: A function that takes an lxml.etree.Element and returns True if it
                should be treated as a block element, or False if it should be treated as an inline
                element. If None, no elements are treated as block elements.

            normalize_whitespace_predicate: A function that takes an lxml.etree.Element and returns
                True if the whitespace in its text content should be normalized (i.e., leading and
                trailing whitespace removed, and internal sequences of whitespace replaced with a
                single space). This does not apply to tail text. If None, no elements have their
                whitespace normalized. It is an error for an element to match both normalize_whitespace_predicate
                and preserve_whitespace_predicate.

            preserve_whitespace_predicate: A function that takes an lxml.etree.Element and returns
                True if the whitespace in its content (i.e., not
                stripped or normalized). If None, no elements have their whitespace preserved. It is
                an error for an element to match both normalize_whitespace_predicate and
                preserve_whitespace_predicate.

            wrap_attributes_predicate: A function that takes an lxml.etree.Element and returns True
                if its attributes should be wrapped onto multiple lines even if they would fit on a
                single line. If None, no elements have their attributes wrapped.

            text_content_formatters: A dictionary mapping predicates (functions that take an
                lxml.etree.Element and return True or False) to formatter functions (functions that
                take a string and return a formatted string, or None). If an element matches a predicate
                in the dictionary, its text content will be passed to the corresponding formatter
                function before being included in the output. If the formatter function is None, the
                text content will be included as-is. If multiple predicates match an element, the
                formatter function for the first matching predicate will be used. If None, no special
                formatting is applied to any element's text content.

            indent_size: The number of spaces to use for each indentation level. Must be a non-negative
        """
        if block_predicate is None:
            block_predicate = lambda e: False

        if normalize_whitespace_predicate is None:
            normalize_whitespace_predicate = lambda e: False

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

        self._is_block = block_predicate
        self._must_normalize_whitespace = normalize_whitespace_predicate
        self._must_preserve_whitespace = preserve_whitespace_predicate
        self._must_wrap_attributes = wrap_attributes_predicate
        self._text_content_formatters = text_content_formatters
        self._indent_char = " "
        self._indent_size = indent_size
        self._one_indent = self._indent_char * self._indent_size

    @property
    def indent_char(self) -> str:
        return self._indent_char

    @property
    def indent_size(self) -> int:
        return self._indent_size

    @property
    def one_indent(self) -> str:
        return self._one_indent

    def format_doc(self, doc: str) -> str:
        """Format a markup document.

        Args:
            doc: A string that can be parsed as XML.

        Returns:
            A pretty-printed XML string.
        """
        tree = etree.fromstring(doc)

        # Create a parallel tree to which we can add special attributes to each element to control
        # formatting.
        annotations = Annotations()

        print("Original tree:")
        print_tree_with_annotations(tree, annotations)
        print("-----")

        # Label each element as a block or inline using the _is_block function.
        for elem in tree.iter():
            annotations.annotate(elem, "_type", "block" if self._is_block(elem) else "inline")

        # Pretty print the tree to see its structure and the annotations.
        print("Annotated tree after initial _type assignment:")
        print_tree_with_annotations(tree, annotations)
        print("-----")

        # Any element for which *any* of its siblings have non-blank tail text is inline, because
        # that tail text must be preserved.
        # First check if any siblings of the current element or the current element itself has
        # non-blank tail text.
        for elem in tree.iter():
            parent = elem.getparent()
            if parent is not None:
                siblings = list(parent)
                if any(sibling.tail and sibling.tail.strip() for sibling in siblings):
                    for sibling in siblings:
                        annotations.annotate(sibling, "_type", "inline")

        print("Annotated tree after marking elements with non-blank tail text as inline:")
        print_tree_with_annotations(tree, annotations)

        # Every element inside an inline element is also inline. This overrides the previous setting.
        for elem in tree.iter():
            parent = elem.getparent()
            if parent is not None and annotations.annotation(parent, "_type") == "inline":
                annotations.annotate(elem, "_type", "inline")

        # Pretty print the tree to see its structure and the annotations.
        print("Annotated tree after propagating inline types:")
        print_tree_with_annotations(tree, annotations)
        print("-----")

        # Now we need to label each element with _preserve_text_ws: bool depending on whether the
        # first child of a block element is inline or not, because inline elements preserve the
        # surrounding whitespace.
        for elem in tree.iter():
            if annotations.annotation(elem, "_type") == "block":

                # Actually if *any* child is inline, we need to preserve the surrounding whitespace.
                # This is because if there are multiple children, and any of them is inline, the
                # whitespace within the block must be preserved.
                if any(annotations.annotation(child, "_type") == "inline" for child in elem):
                    annotations.annotate(elem, "_preserve_text_ws", TRUE)
                else:
                    annotations.annotate(elem, "_preserve_text_ws", FALSE)
            else:
                annotations.annotate(elem, "_preserve_text_ws", TRUE)

        # Pretty print the tree to see its structure and the annotations.
        print("Annotated tree after setting _preserve_text_ws:")
        print_tree_with_annotations(tree, annotations)
        print("-----")

        # We need to label each element with _preserve_tail_ws: bool depending on whether the next sibling
        # of a block element is inline or not, because inline elements preserve the surrounding
        # whitespace.
        for elem in tree.iter():
            if annotations.annotation(elem, "_type") == "block":
                next_sibling = elem.getnext()
                if next_sibling is not None and annotations.annotation(next_sibling, "_type") == "inline":
                    annotations.annotate(elem, "_preserve_tail_ws", TRUE)
                else:
                    annotations.annotate(elem, "_preserve_tail_ws", FALSE)
            else:
                annotations.annotate(elem, "_preserve_tail_ws", TRUE)

        # Pretty print the tree to see its structure and the annotations.
        print("Annotated tree after setting _preserve_tail_ws:")
        print_tree_with_annotations(tree, annotations)
        print("-----")

        # Now we set _preserve_text_ws to TRUE for any element for which the _must_preserve_whitespace
        # function returns True. We also need to modify all descendants of the matching element to set both
        # _preserve_text_ws and _preserve_tail_ws to TRUE.
        for elem in tree.iter():
            if self._must_preserve_whitespace(elem):
                if self._must_normalize_whitespace(elem):
                    raise RuntimeError(
                        f"Element <{elem.tag}> matches both normalize_whitespace_predicate and preserve_whitespace_predicate"
                    )
                annotations.annotate(elem, "_preserve_text_ws", TRUE)
                for descendant in elem.iterdescendants():
                    annotations.annotate(descendant, "_preserve_text_ws", TRUE)
                    annotations.annotate(descendant, "_preserve_tail_ws", TRUE)

        print("Annotated tree after setting _preserve_text_ws for preserve_whitespace_predicate:")
        print_tree_with_annotations(tree, annotations)
        print("-----")

        # Now we override the _preserve_text_ws attribute to be falsey (i.e. "") for any element and
        # for which the _must_normalize_whitespace function returns True. We also set the
        # "_normalize_text_whitespace" attribute to "true" for this element. We also need to modify
        # all descendants of the matching element to set both _preserve_text_ws and _preserve_tail_ws to
        # falsey (i.e. "") and set the "_normalize_text_whitespace" attribute to "true".
        for elem in tree.iter():
            if self._must_normalize_whitespace(elem):
                if self._must_preserve_whitespace(elem):
                    raise RuntimeError(
                        f"Element <{elem.tag}> matches both normalize_whitespace_predicate and preserve_whitespace_predicate"
                    )
                annotations.annotate(elem, "_normalize_text_whitespace", TRUE)
                annotations.annotate(elem, "_preserve_text_ws", FALSE)
                annotations.annotate(elem, "_preserve_tail_ws", FALSE)
                for descendant in elem.iterdescendants():
                    annotations.annotate(descendant, "_normalize_text_whitespace", TRUE)
                    annotations.annotate(descendant, "_normalize_tail_whitespace", TRUE)
                    annotations.annotate(descendant, "_preserve_text_ws", FALSE)
                    annotations.annotate(descendant, "_preserve_tail_ws", FALSE)

        print("Annotated tree after setting _normalize_text_whitespace:")
        print_tree_with_annotations(tree, annotations)
        print("-----")



        self._annotate_logical_level(annotations, tree)
        print("Annotated tree after setting _logical_level:")
        print_tree_with_annotations(tree, annotations)
        print("-----")

        self._annotate_physical_level(annotations, tree)
        print("Annotated tree after setting _physical_level:")
        print_tree_with_annotations(tree, annotations)
        print("-----")

        # Annotate each element with a string which contains a newline and the appropriate indentation
        # to follow its text, if any. If the first child is inline, then no newline or indentation
        # is added. If the first child is block, then a newline and indentation is added appropriate for
        # the physical level of the block. If there are no children, no newline or indentation is added.
        # We also need to respect the _preserve_text_ws attribute.
        for elem in tree.iter():
            first_child = next(iter(elem), None)
            if first_child is not None:
                if annotations.annotation(first_child, "_type") == "inline" or annotations.annotation(elem, "_preserve_text_ws"):
                    annotations.annotate(elem, "_text_indent", "")
                else:
                    indent = self._one_indent * int(annotations.annotation(first_child, "_physical_level", 0))
                    annotations.annotate(elem, "_text_indent", "\n" + indent)
            else:
                annotations.annotate(elem, "_text_indent", "")

        print("Annotated tree after setting _text_indent:")
        print_tree_with_annotations(tree, annotations)
        print("-----")

        # Annotate each element with a string which contains a newline and the appropriate indentation
        # to follow its tail, if any. If the following element is inline, then no newline or indentation
        # is added. If the following element is block, then a newline and indentation is added appropriate
        # for the physical level of the block. If the element is the last child of its parent, and if
        # the parent is a block, a newline
        # and indentation is added appropriate for the physical level of the parent in order to indent
        # the closing tag of the parent. We also need to respect the _preserve_tail_ws attribute.
        for elem in tree.iter():
            next_sibling = elem.getnext()
            if next_sibling is not None:
                if annotations.annotation(next_sibling, "_type") == "inline" or annotations.annotation(elem, "_preserve_tail_ws"):
                    annotations.annotate(elem, "_tail_indent", "")
                else:
                    indent = self._one_indent * int(annotations.annotation(next_sibling, "_physical_level", 0))
                    annotations.annotate(elem, "_tail_indent", "\n" + indent)
            else:
                parent = elem.getparent()
                if parent is not None and annotations.annotation(parent, "_type") == "block" and not annotations.annotation(elem, "_preserve_tail_ws"):
                    indent = self._one_indent * int(annotations.annotation(parent, "_physical_level", 0))
                    annotations.annotate(elem, "_tail_indent", "\n" + indent)
                else:
                    annotations.annotate(elem, "_tail_indent", "")

        print("Annotated tree after setting _tail_indent:")
        print_tree_with_annotations(tree, annotations)
        print("-----")

        # Now we can format the document using the annotated tree to guide the formatting.
        parts = []
        self._format_element(annotations, tree, parts)
        pprint(parts)
        return "".join(flatten(parts))

    def _format_element(self, annotations: Annotations, element: etree._Element, parts: list[str]):
        opening_tag_parts = []
        opening_tag_parts.append(f"<{element.tag}")

        # Set the attribute spacer to a single space or a newline and indentation depending on whether
        # the attributes should be wrapped.
        must_wrap_attributes = self._must_wrap_attributes(element)
        if must_wrap_attributes:
            spacer = "\n" + self._one_indent * (int(annotations.annotation(element, "_physical_level", 0)) + 1)
        else:
            spacer = " "

        real_attributes = {k: v for k, v in element.attrib.items() if not k.startswith("_")}
        for k, v in real_attributes.items():
            escaped_value = quoteattr(v)
            opening_tag_parts.append(f'{spacer}{k}={escaped_value}')
        if real_attributes and must_wrap_attributes:
            opening_tag_parts.append("\n" + self._one_indent * int(annotations.annotation(element, "_physical_level", 0)))

        is_self_closing = self._is_self_closing(annotations, element)

        if is_self_closing:
            if not must_wrap_attributes:
                opening_tag_parts.append(" ")
            opening_tag_parts.append("/")

        opening_tag_parts.append(">")
        parts.append(opening_tag_parts)

        if not is_self_closing:
            contents_parts = []
            text = self.text_content(annotations, element)
            if text:
                escaped_text = escape(text)
                contents_parts.append(escaped_text)
            contents_parts.append(annotations.annotation(element, "_text_indent", ""))
            for child in element:
                self._format_element(annotations, child, contents_parts)
            parts.append(contents_parts)
            closing_tag_parts = [f"</{element.tag}>"]
            parts.append(closing_tag_parts)
        tail_parts = []
        if element.tail:
            tail = element.tail or ""
            if annotations.annotation(element,"_type") == "block" and not annotations.annotation(element, "_preserve_tail_ws"):
                tail = tail.strip()
            if annotations.annotation(element, "_normalize_tail_whitespace"):
                tail = normalize_ws(tail)
                tail = tail.rstrip()
            if tail:
                escaped_tail = escape(tail)
                tail_parts.append(escaped_tail)
                parts.append(tail_parts)
        if annotations.annotation(element, "_type") == "block" and not annotations.annotation(element, "_normalize_tail_whitespace"):
            parts.append(annotations.annotation(element, "_tail_indent", ""))

    # Now we can annotate each element with its logical level (0 for root, 1 for children of root, etc.)
    def _annotate_logical_level(self, annotations, element: etree._Element, level: int = 0):
        annotations.annotate(element, "_logical_level", str(level))
        for child in element:
            self._annotate_logical_level(annotations, child, level + 1)


    # Now we can annotate each element with its indentation level, where block elements are indented
    # one level more than their parent, and inline elements are at the same level as their parent.
    def _annotate_physical_level(self, annotations, element: etree._Element, level: int = 0):
        annotations.annotate(element, "_physical_level", str(level))
        for child in element:
            if annotations.annotation(child, "_type") == "block":
                self._annotate_physical_level(annotations, child, level + 1)
            else:
                self._annotate_physical_level(annotations, child, level)


    def _is_self_closing(self, annotations, element: etree._Element) -> bool:
        text = self.text_content(annotations, element)
        return (not bool(text)) and len(element) == 0

    def text_content(self, annotations, element):
        text = element.text or ""
        if annotations.annotation(element, "_type") == "block" and not annotations.annotation(element, "_preserve_text_ws"):
            text = text.strip()
        if annotations.annotation(element, "_normalize_text_whitespace"):
            text = normalize_ws(text)
            text = text.lstrip()
        # Apply any content formatter if the element matches its predicate.
        for predicate, formatter in self._text_content_formatters.items():
            if predicate(element):
                text = formatter(element, annotations, self)
                break
        return text


def is_block_or_root(element: etree._Element) -> bool:
    return element.tag in {"block", "root"}


def split_whitespace(s):
    return [(' ' if k else ''.join(g)) for k, g in groupby(s, str.isspace)]


def normalize_ws(s: str) -> str:
    """Normalize whitespace in a string by replacing sequences of whitespace with a single space.

    Args:
        s: The input string to normalize.

    Returns:
        The string with normalized whitespace. Note that the result may have leading or trailing
        spaces if the input string had leading or trailing whitespace.
    """
    return "".join(split_whitespace(s))


def print_tree_with_annotations(element, annotations, indent=0):
    """Recursively print the tree structure with annotations for each element."""
    ind = '  ' * indent
    attribs = ' '.join(f'{k}="{v}"' for k, v in element.attrib.items())
    ann = annotations._annotations.get(element, {})
    ann_str = f" [annotations: {ann}]" if ann else ""
    print(f"{ind}<{element.tag}{' ' + attribs if attribs else ''}>{ann_str}")
    text = (element.text or '').strip()
    if text:
        print(f"{ind}  text: {text}")
    for child in element:
        print_tree_with_annotations(child, annotations, indent + 1)
    print(f"{ind}</{element.tag}>")
