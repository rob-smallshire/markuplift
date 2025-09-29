from lxml import etree


def is_block_or_root(element: etree._Element) -> bool:
    return element.tag in {"block", "root"}


def is_inline(element: etree._Element) -> bool:
    return element.tag == "inline"
