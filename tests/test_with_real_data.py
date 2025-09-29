import jsbeautifier
from approvaltests import verify

from markuplift import Html5Formatter, XmlFormatter, ElementType
from markuplift.predicates import html_block_elements, any_of, all_of, tag_in, attribute_count_min


def test_generated_html(test_data_path):
    html_file = test_data_path("messy_html_page.html")
    with open(html_file) as f:
        original = f.read()

    # Custom predicate factory for img elements that are block when parent is block
    def img_block_when_parent_block():
        def create_document_predicate(root):
            # Get the standard HTML block elements predicate
            html_block_pred = html_block_elements()(root)

            def element_predicate(element):
                if element.tag == "img":
                    parent = element.getparent()
                    return parent is not None and html_block_pred(parent)
                return False

            return element_predicate

        return create_document_predicate

    # Custom block predicate that extends html_block_elements with img logic
    custom_block_elements = any_of(html_block_elements(), img_block_when_parent_block())

    formatter = Html5Formatter(
        block_when=custom_block_elements,
        strip_whitespace_when=tag_in("title", "h1", "h2", "h3", "p", "li"),
        preserve_whitespace_when=tag_in("style", "pre"),
        wrap_attributes_when=all_of(tag_in("link"), attribute_count_min(3)),
        reformat_text_when={tag_in("script"): beautify_js},
    )
    actual = formatter.format_str(original)
    verify(actual)


def test_xml_doc(test_data_path):
    xml_file = test_data_path("messy_xml_chunked_content.xml")

    # Define custom XML block elements for this document structure
    xml_block_elements = tag_in("chunked-content", "titles", "title", "chunks", "chunk", "heading", "paragraphs", "p")

    formatter = XmlFormatter(
        block_when=xml_block_elements,
        strip_whitespace_when=tag_in("supertitle", "title", "subtitle"),
        preserve_whitespace_when=tag_in("style", "pre"),
        wrap_attributes_when=attribute_count_min(2),
        default_type=ElementType.INLINE,  # Using ElementType enum
    )
    actual = formatter.format_file(xml_file)
    verify(actual)


def beautify_js(text: str, formatter, physical_indent_level: int) -> str:
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
