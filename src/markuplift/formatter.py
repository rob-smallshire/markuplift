from copy import deepcopy
from itertools import groupby
from typing import Callable

from lxml import etree

FALSE = ""  # Empty string is falsey when evaluated as a bool

TRUE = "true"


class Formatter:

    def __init__(
        self,
        block_predicate: Callable[[etree._Element], bool] | None = None,
        normalize_whitespace_predicate: Callable[[etree._Element], bool] | None = None,
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
                whitespace normalized.
        """
        if block_predicate is None:
            block_predicate = lambda e: False

        if normalize_whitespace_predicate is None:
            normalize_whitespace_predicate = lambda e: False

        self._is_block = block_predicate
        self._must_normalize_whitespace = normalize_whitespace_predicate

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
        annotated_tree = deepcopy(tree)

        print("Original tree:")
        print(etree.tostring(annotated_tree, pretty_print=True).decode())
        print("-----")

        # Label each element as a block or inline using the _is_block function.
        for elem in annotated_tree.iter():
            elem.attrib["_type"] = "block" if self._is_block(elem) else "inline"

        # Pretty print the tree to see its structure and the annotations.
        print("Annotated tree after initial _type assignment:")
        print(etree.tostring(annotated_tree, pretty_print=True).decode())
        print("-----")

        # Any element for which *any* of its siblings have non-blank tail text is inline, because
        # that tail text must be preserved.
        # First check if any siblings of the current element or the current element itself has
        # non-blank tail text.
        for elem in annotated_tree.iter():
            parent = elem.getparent()
            if parent is not None:
                siblings = list(parent)
                if any(sibling.tail and sibling.tail.strip() for sibling in siblings):
                    for sibling in siblings:
                        sibling.attrib["_type"] = "inline"

        print("Annotated tree after marking elements with non-blank tail text as inline:")
        print(etree.tostring(annotated_tree, pretty_print=True).decode())

        # Every element inside an inline element is also inline. This overrides the previous setting.
        for elem in annotated_tree.iter():
            parent = elem.getparent()
            if parent is not None and parent.attrib.get("_type") == "inline":
                elem.attrib["_type"] = "inline"

        # Pretty print the tree to see its structure and the annotations.
        print("Annotated tree after propagating inline types:")
        print(etree.tostring(annotated_tree, pretty_print=True).decode())
        print("-----")

        # Now we need to label each element with _preserve_text_ws: bool depending on whether the
        # first child of a block element is inline or not, because inline elements preserve the
        # surrounding whitespace.
        for elem in annotated_tree.iter():
            if elem.attrib.get("_type") == "block":

                # Actually if *any* child is inline, we need to preserve the surrounding whitespace.
                # This is because if there are multiple children, and any of them is inline, the
                # whitespace within the block must be preserved.
                if any(child.attrib.get("_type") == "inline" for child in elem):
                    elem.attrib["_preserve_text_ws"] = TRUE
                else:
                    elem.attrib["_preserve_text_ws"] = FALSE
            else:
                elem.attrib["_preserve_text_ws"] = TRUE

        # Pretty print the tree to see its structure and the annotations.
        print("Annotated tree after setting _preserve_text_ws:")
        print(etree.tostring(annotated_tree, pretty_print=True).decode())
        print("-----")

        # We need to label each element with _preserve_tail_ws: bool depending on whether the next sibling
        # of a block element is inline or not, because inline elements preserve the surrounding
        # whitespace.
        for elem in annotated_tree.iter():
            if elem.attrib.get("_type") == "block":
                next_sibling = elem.getnext()
                if next_sibling is not None and next_sibling.attrib.get("_type") == "inline":
                    elem.attrib["_preserve_tail_ws"] = TRUE
                else:
                    elem.attrib["_preserve_tail_ws"] = FALSE
            else:
                elem.attrib["_preserve_tail_ws"] = TRUE

        # Pretty print the tree to see its structure and the annotations.
        print("Annotated tree after setting _preserve_tail_ws:")
        print(etree.tostring(annotated_tree, pretty_print=True).decode())
        print("-----")

        # Now we override the _preserve_text_ws attribute to be falsey (i.e. "") for any element and
        # for which the _must_normalize_whitespace function returns True. We also set the
        # "_normalize_text_whitespace" attribute to "true" for this element. We also need to modify
        # all descendants of the matching element to set both _preserve_text_ws and _preserve_tail_ws to
        # falsey (i.e. "") and set the "_normalize_text_whitespace" attribute to "true".
        for elem in annotated_tree.iter():
            if self._must_normalize_whitespace(elem):
                elem.attrib["_normalize_text_whitespace"] = TRUE
                elem.attrib["_preserve_text_ws"] = FALSE
                elem.attrib["_preserve_tail_ws"] = FALSE
                for descendant in elem.iterdescendants():
                    descendant.attrib["_normalize_text_whitespace"] = TRUE
                    descendant.attrib["_normalize_tail_whitespace"] = TRUE
                    descendant.attrib["_preserve_text_ws"] = FALSE
                    descendant.attrib["_preserve_tail_ws"] = FALSE

        print("Annotated tree after setting _normalize_text_whitespace:")
        print(etree.tostring(annotated_tree, pretty_print=True).decode())
        print("-----")

        self._annotate_logical_level(annotated_tree)
        print("Annotated tree after setting _logical_level:")
        print(etree.tostring(annotated_tree, pretty_print=True).decode())
        print("-----")

        self._annotate_physical_level(annotated_tree)
        print("Annotated tree after setting _physical_level:")
        print(etree.tostring(annotated_tree, pretty_print=True).decode())
        print("-----")

        # Annotate each element with a string which contains a newline and the appropriate indentation
        # to follow its text, if any. If the first child is inline, then no newline or indentation
        # is added. If the first child is block, then a newline and indentation is added appropriate for
        # the physical level of the block. If there are no children, no newline or indentation is added.
        # We also need to respect the _preserve_text_ws attribute.
        for elem in annotated_tree.iter():
            first_child = next(iter(elem), None)
            if first_child is not None:
                if first_child.attrib.get("_type") == "inline" or elem.attrib.get(
                    "_preserve_text_ws"
                ):
                    elem.attrib["_text_indent"] = ""
                else:
                    indent = "  " * int(first_child.attrib.get("_physical_level", 0))
                    elem.attrib["_text_indent"] = "\n" + indent
            else:
                elem.attrib["_text_indent"] = ""

        print("Annotated tree after setting _text_indent:")
        print(etree.tostring(annotated_tree, pretty_print=True).decode())
        print("-----")

        # Annotate each element with a string which contains a newline and the appropriate indentation
        # to follow its tail, if any. If the following element is inline, then no newline or indentation
        # is added. If the following element is block, then a newline and indentation is added appropriate
        # for the physical level of the block. If the element is the last child of its parent, and if
        # the parent is a block, a newline
        # and indentation is added appropriate for the physical level of the parent in order to indent
        # the closing tag of the parent. We also need to respect the _preserve_tail_ws attribute.
        for elem in annotated_tree.iter():
            next_sibling = elem.getnext()
            if next_sibling is not None:
                if next_sibling.attrib.get("_type") == "inline" or elem.attrib.get(
                    "_preserve_tail_ws"
                ):
                    elem.attrib["_tail_indent"] = ""
                else:
                    indent = "  " * int(next_sibling.attrib.get("_physical_level", 0))
                    elem.attrib["_tail_indent"] = "\n" + indent
            else:
                parent = elem.getparent()
                if parent is not None and parent.attrib.get("_type") == "block" and not elem.attrib.get("_preserve_tail_ws"):
                    indent = "  " * int(parent.attrib.get("_physical_level", 0))
                    elem.attrib["_tail_indent"] = "\n" + indent
                else:
                    elem.attrib["_tail_indent"] = ""

        print("Annotated tree after setting _tail_indent:")
        print(etree.tostring(annotated_tree, pretty_print=True).decode())
        print("-----")

        # Now we can format the document using the annotated tree to guide the formatting.
        parts = []
        self._format_element(annotated_tree, parts)
        return "".join(parts)

    def _format_element(
        self,
        element: etree._Element,
        parts: list[str],
    ):
        parts.append(f"<{element.tag}")
        for k, v in element.attrib.items():
            if not k.startswith("_"):
                parts.append(f' {k}="{v}"')
        parts.append(">")
        if element.text:
            text = element.text or ""
            if element.attrib.get("_type") == "block" and not element.attrib.get("_preserve_text_ws"):
                text = text.strip()
            if element.attrib.get("_normalize_text_whitespace"):
                text = normalize_ws(text)
                text = text.lstrip()
            if text:
                parts.append(text)
        parts.append(element.attrib.get("_text_indent", ""))
        for child in element:
            self._format_element(child, parts)
        parts.append(f"</{element.tag}>")
        if element.tail:
            tail = element.tail or ""
            if element.attrib.get("_type") == "block" and not element.attrib.get("_preserve_tail_ws"):
                tail = tail.strip()
            if element.attrib.get("_normalize_tail_whitespace"):
                tail = normalize_ws(tail)
                tail = tail.rstrip()
            if tail:
                parts.append(tail)
        if not element.attrib.get("_normalize_tail_whitespace"):
            parts.append(element.attrib.get("_tail_indent", ""))


    # Now we can annotate each element with its logical level (0 for root, 1 for children of root, etc.)
    def _annotate_logical_level(self, element: etree._Element, level: int = 0):
        element.attrib["_logical_level"] = str(level)
        for child in element:
            self._annotate_logical_level(child, level + 1)


    # Now we can annotate each element with its indentation level, where block elements are indented
    # one level more than their parent, and inline elements are at the same level as their parent.
    def _annotate_physical_level(self, element: etree._Element, level: int = 0):
        element.attrib["_physical_level"] = str(level)
        for child in element:
            if child.attrib.get("_type") == "block":
                self._annotate_physical_level(child, level + 1)
            else:
                self._annotate_physical_level(child, level)


def is_block_or_root(element: etree._Element) -> bool:
    return element.tag in {"block", "root"}


def split_whitespace(s):
    return [(' ' if k else ''.join(g)) for k, g in groupby(s, str.isspace)]


def normalize_ws(s: str) -> str:
    return "".join(split_whitespace(s))