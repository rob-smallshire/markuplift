from .cli import cli
cli()
import re
from dataclasses import dataclass, field
from typing import List, Optional
from lxml import html

@dataclass
class FormatterConfig:
    block_xpaths: List[str] = field(default_factory=lambda: [
        "//div", "//p", "//section", "//article",
        "//h1", "//h2", "//h3", "//ul", "//ol", "//li"
    ])
    inline_xpaths: List[str] = field(default_factory=lambda: [
        "//span", "//a", "//em", "//strong", "//b", "//i"
    ])
    self_closing_tags: List[str] = field(default_factory=lambda: [
        "br", "img", "hr", "meta", "link", "input"
    ])
    preserve_whitespace_xpaths: List[str] = field(default_factory=lambda: [
        "//pre", "//code", "//textarea"
    ])
    wrap_attributes_xpaths: List[str] = field(default_factory=list)
    wrap_attributes_threshold: int = 3
    max_line_length: int = 80
    indent: str = "  "


class HTMLFormatter:
    def __init__(self, config: Optional[FormatterConfig] = None):
        self.config = config or FormatterConfig()

    def format_html(self, html_string: str) -> str:
        parser = html.HTMLParser(remove_blank_text=True)
        tree = html.fromstring(html_string, parser=parser)

        # Precompute element sets for efficiency
        block_elems = self._collect_elements(tree, self.config.block_xpaths)
        inline_elems = self._collect_elements(tree, self.config.inline_xpaths)
        preserve_elems = self._collect_elements(tree, self.config.preserve_whitespace_xpaths)
        wrap_attr_elems = self._collect_elements(tree, self.config.wrap_attributes_xpaths)
        self_closing_tags = set(self.config.self_closing_tags)

        def normalize_ws(text):
            return re.sub(r'\s+', ' ', text).strip()

        def classify(elem):
            if elem in block_elems:
                return "block"
            elif elem in inline_elems:
                return "inline"
            else:
                return "other"

        def should_wrap_attributes(elem, is_block):
            if elem in wrap_attr_elems:
                return True
            if is_block and len(elem.attrib) >= self.config.wrap_attributes_threshold:
                return True
            tag_open = f"<{elem.tag}"
            attr_str = "".join(f' {k}="{v}"' for k, v in elem.attrib.items())
            if is_block and self.config.max_line_length and len(tag_open + attr_str + ">") > self.config.max_line_length:
                return True
            return False

        def format_attributes(elem, level, wrap):
            if not elem.attrib:
                return ""
            if not wrap:
                return "".join(f' {k}="{v}"' for k, v in elem.attrib.items())
            # Multi-line attributes
            parts = []
            for k, v in elem.attrib.items():
                parts.append(f"\n{self.config.indent * (level+1)}{k}=\"{v}\"")
            return "".join(parts) + "\n" + self.config.indent * (level+1)

        def recurse(elem, level=0, preserve_ws=False, parent_block=False):
            elem_type = classify(elem)
            is_self_closing = elem.tag in self_closing_tags
            preserve_ws = preserve_ws or elem in preserve_elems
            is_block = elem_type == "block"
            is_inline = elem_type == "inline"

            new_level = level + 1 if is_block else level
            parent_block = parent_block or is_block

            wrap_attrs = should_wrap_attributes(elem, is_block)

            # Start tag
            if is_block:
                result = "\n" + self.config.indent * level + f"<{elem.tag}"
            elif parent_block:
                result = f"<{elem.tag}"
            else:
                result = "\n" + self.config.indent * level + f"<{elem.tag}"

            # Attributes
            result += format_attributes(elem, level, wrap_attrs)

            if is_self_closing:
                result += "/>"
                return result

            result += ">"

            # Children or text
            children = list(elem)
            text = elem.text or ""
            if text:
                text_to_add = text if preserve_ws else normalize_ws(text)
                if text_to_add:
                    if is_block:
                        result += "\n" + self.config.indent * new_level + text_to_add
                    else:
                        result += text_to_add

            for child in children:
                result += recurse(child, new_level, preserve_ws, parent_block=is_block or parent_block)

            # Closing tag
            if is_block and children:
                result += "\n" + self.config.indent * level
            result += f"</{elem.tag}>"

            # Tail text
            if elem.tail:
                tail_to_add = elem.tail if preserve_ws else normalize_ws(elem.tail)
                if tail_to_add:
                    if parent_block:
                        result += "\n" + self.config.indent * level + tail_to_add
                    else:
                        result += tail_to_add

            return result

        return recurse(tree, 0).strip() + "\n"

    def _collect_elements(self, tree, xpaths: List[str]):
        elems = set()
        for xp in xpaths:
            elems.update(tree.xpath(xp))
        return elems


# Convenience API
def format_html(html_string: str, config: Optional[FormatterConfig] = None) -> str:
    return HTMLFormatter(config).format_html(html_string)
