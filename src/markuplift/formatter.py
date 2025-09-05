from lxml import etree


def format_doc(doc: str) -> str:
    """Format a markup document.

    Args:
        doc: A string that can be parsed as XML.

    Returns:
        A pretty-printed XML string.
    """
    tree = etree.fromstring(doc)
    parts = []
    format_element(tree, parts)
    return "".join(parts)


def _is_block(element: etree._Element) -> bool:
    return element.tag in {"block", "root"}


def format_element(
    element: etree._Element,
    parts: list[str],
    logical_level: int = 0,
    physical_level: int = 0,
    previous: etree._Element = None,
) -> etree._Element:
    is_block = _is_block(element)
    indent = "  " * physical_level
    physical_increment = 0
    if is_block and ((previous is None) or (_is_block(previous) and not previous.tail)):
        if parts and parts[-1] != "\n":
            parts.append("\n")
        parts.append(indent)
        physical_increment = 1

    tag = element.tag
    parts.append(f"<{tag}")

    for k, v in element.attrib.items():
        parts.append(f' {k}="{v}"')

    parts.append(">")

    text = (element.text or "")
    if text:
        parts.append(text)

    previous_child = None

    for child in element:
        previous_child = format_element(child, parts, logical_level + 1, physical_level + physical_increment, previous_child)

    if is_block and (previous_child is not None) and _is_block(previous_child) and (not previous_child.tail):
        parts.append(indent)

    parts.append(f"</{tag}>")

    if element.tail:
        parts.append(element.tail)

    if logical_level != 0 and is_block and not element.tail:
        if parts and parts[-1] != "\n":
            parts.append("\n")

    return element
