import jsbeautifier
from approvaltests import verify

from markuplift import DocumentFormatter
from markuplift.annotation import INLINE_TYPE_ANNOTATION


def test_generated_html(test_data_path):
    html_file = test_data_path("messy_html_page.html")
    with open(html_file) as f:
        original = f.read()

    def is_block(e):
        return (
            (e.tag in {"html", "head", "meta", "link", "body", "div", "article", "section", "header", "p", "ul", "li", "script", "h1", "h2", "h3", "title"})
            or
            (e.tag in {"img"} and (e.getparent() is not None) and is_block(e.getparent()))
        )

    formatter = DocumentFormatter(
        block_predicate=is_block,
        strip_whitespace_predicate=lambda e: e.tag in {"title", "h1", "h2", "h3", "p", "li"},
        preserve_whitespace_predicate=lambda e: e.tag in {"style", "pre"},
        wrap_attributes_predicate=lambda e: e.tag in {"link"} and sum(1 for k in e.attrib if not k.startswith("_")) >= 3,
        text_content_formatters={
            lambda e: e.tag == "title": lambda text, formatter, level: (text or "").strip(),
            lambda e: e.tag == "script": beautify_js
        }
    )
    actual = formatter.format_str(original)
    verify(actual)



def test_xml_doc(test_data_path):
    xml_file = test_data_path("messy_xml_chunked_content.xml")
    with open(xml_file) as f:
        original = f.read()

    formatter = DocumentFormatter(
        block_predicate=lambda e: e.tag in {"chunked-content", "titles", "title", "chunks", "chunk", "heading", "paragraphs", "p"},
        strip_whitespace_predicate=lambda e: e.tag in {"supertitle", "title", "subtitle"},
        preserve_whitespace_predicate=lambda e: e.tag in {"style", "pre"},
        wrap_attributes_predicate=lambda e: len(e.attrib) >= 2,
        default_type=INLINE_TYPE_ANNOTATION,
    )
    actual = formatter.format_str(original)
    verify(actual)



def beautify_js(text: str, formatter: DocumentFormatter, physical_indent_level: int) -> str:

    text = text or ""
    if text.strip() == "":
        return ""

    options = jsbeautifier.BeautifierOptions(
        dict(
            indent_size=formatter.indent_size,
            indent_char=formatter.indent_char,
            preserve_newlines=True,
            max_preserve_newlines=2,
            space_in_empty_paren=False,
        )
    )

    pretty_text = jsbeautifier.beautify(text, options)
    lines = pretty_text.splitlines()
    indent = formatter.one_indent * (physical_indent_level + 1)
    indented_lines = [indent + line if line.strip() != "" else line for line in lines]
    indented_text = "\n".join(indented_lines)
    return "\n" + indented_text + "\n" + formatter.one_indent * physical_indent_level


if __name__ == "__main__":
    test_generated_html()