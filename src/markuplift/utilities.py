"""Utility functions for XML/HTML processing.

This module provides various utility functions for working with XML elements,
including sibling relationships, text content analysis, whitespace processing,
and element classification helpers.

These utilities are used throughout MarkupLift to support the formatting and
annotation processes.
"""

import re
from itertools import groupby

from lxml import etree


def siblings(node: etree._Element) -> list[etree._Element]:
    """
    Given an lxml.etree node (element, comment, or PI),
    return a list of all its siblings in document order,
    including the node itself.
    """
    parent = node.getparent()
    if parent is None:
        # root element, comment, or PI: siblings are just itself
        return [node]
    return list(parent)  # iteration yields all child nodes


def tagname(node: etree._Element) -> str:
    """
    Return a string tag name for any lxml.etree node:
    - Elements: their normal tag
    - Comments: '#comment'
    - Processing instructions: '?<target>'
    """
    if isinstance(node, etree._Comment) and node.tag is etree.Comment:
        return "#comment"
    elif isinstance(node, etree._ProcessingInstruction) and node.tag is etree.PI:
        return f"?{node.target}"
    else:
        return str(node.tag)


def is_xml_whitespace(text: str) -> bool:
    """Check if the given text is None or consists only of XML whitespace characters."""
    return not bool(text.strip())


def is_significant_text(text: str | None) -> bool:
    """Check if the given text contains any non-whitespace characters."""
    return (text is not None) and (not is_xml_whitespace(text))


def has_direct_significant_text(element: etree._Element) -> bool:
    """Determine if the given element has text content as its immediate children.

    Text content means that it has both significant text itself or its element-like children (elements, comments, or
    processing instructions) have significant text in their .tail.

    The text nodes must contain non-whitespace characters to count according to XML standards.

    Args:
        element: The lxml.etree element to check.

    Returns:
        True if the element has direct text content, False otherwise.
    """
    if is_significant_text(element.text):
        return True
    for child in element:
        if is_significant_text(child.tail):
            return True
    return False


def is_in_mixed_content(element: etree._Element) -> bool:
    """Determine if the given element is in mixed content.

    An element is considered to be in mixed content if its parent has direct significant text.

    Args:
        element: The lxml.etree element to check.

    Returns:
        True if the element is in mixed content, False otherwise.
    """
    parent = element.getparent()
    if parent is None:
        return False
    return has_direct_significant_text(parent)


def parent_is_annotated_with(element: etree._Element, annotations, annotation_key: str, annotation_value: str) -> bool:
    """Check if the parent of the given element is annotated with the specified key and value.

    Args:
        element: The lxml.etree element whose parent to check.
        annotations: The Annotations object to query.
        annotation_key: The key of the annotation to check.
        annotation_value: The value of the annotation to check.

    Returns:
        True if the parent is annotated with the specified key and value, otherwise False.
    """
    parent = element.getparent()
    if parent is None:
        return False
    return annotations.annotation(parent, annotation_key) == annotation_value


def print_tree_with_annotations(element, annotations, indent=0, title=None):
    """Recursively print the tree structure with annotations for each element."""
    banner = ""
    if title:
        banner = "=" * len(title)
        print(banner)
        print(f"{title}:")
        print("-" * len(title))
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
    if banner:
        print(banner)


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


def has_xml_declaration_bytes(xml: bytes) -> bool:
    # Remove optional UTF-8 BOM and leading whitespace bytes
    xml = xml.lstrip(b'\xef\xbb\xbf\r\n\t ')
    # Match only the XML declaration at the very start (as bytes)
    return bool(re.match(br'^<\?xml\s+version\s*=\s*["\']1\.[0-9]["\'].*\?>', xml, re.IGNORECASE))
