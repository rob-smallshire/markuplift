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
    format_element(tree, parts, level=0)
    return "".join(parts)


def _is_block(element: etree._Element) -> bool:
    return element.tag in {"block"}


def format_element(element: etree._Element, parts: list[str], level: int) -> bool:
    is_block = _is_block(element)
    indent = "  " * level
    if is_block:
        if parts[-1] != "\n":
            parts.append("\n")
        parts.append(indent)

    tag = element.tag
    parts.append(f"<{tag}")

    for k, v in element.attrib.items():
        parts.append(f' {k}="{v}"')

    parts.append(">")

    text = (element.text or "")
    if text:
        parts.append(text)

    child_block = False
    for child in element:
        child_block = format_element(child, parts, level + int(_is_block(child)))
        tail = (child.tail or "")
        if tail:
            parts.append(tail)

    if child_block:
        parts.append(indent)

    parts.append(f"</{tag}>")

    if is_block:
        if parts[-1] != "\n":
            parts.append("\n")
        return True

    return False
