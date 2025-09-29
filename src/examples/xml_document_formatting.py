"""XML document formatting example for README.md.

This module contains the exact example code shown in the README's XML Document Formatting section.
"""

from pathlib import Path
from markuplift import XmlFormatter, ElementType
from markuplift.predicates import tag_in


def format_xml_document_example(input_file: Path):
    """Format XML document with custom structure using XmlFormatter.

    This demonstrates XmlFormatter with XML-strict parsing and escaping,
    showing how to define custom XML element classifications.

    Args:
        input_file: Path to the XML file to format

    Returns:
        str: The formatted XML output
    """
    # Define custom XML structure with ElementType enum
    formatter = XmlFormatter(
        block_when=tag_in("document", "section", "paragraph", "metadata"),
        inline_when=tag_in("emphasis", "code", "link"),
        preserve_whitespace_when=tag_in("code-block", "verbatim"),
        default_type=ElementType.BLOCK,  # Use enum for type safety
        indent_size=2,
    )

    # Format the XML document
    formatted = formatter.format_file(input_file)
    return formatted


if __name__ == "__main__":
    # This allows the example to be run directly
    examples_dir = Path(__file__).parent.parent.parent / "tests" / "data" / "readme_examples"
    input_file = examples_dir / "xml_document_example.xml"
    print(format_xml_document_example(input_file))
