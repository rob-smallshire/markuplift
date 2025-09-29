"""Real-world article example for README.md.

This module contains the exact example code shown in the README's Real-World Example section.
"""

from pathlib import Path
from markuplift import Html5Formatter
from markuplift.predicates import tag_in, any_of, html_inline_elements


def format_article_example(input_file: Path):
    """Format complex article structure with mixed content.

    This is the real-world example shown in the README demonstrating
    Html5Formatter with custom whitespace handling.

    Args:
        input_file: Path to the HTML file to format

    Returns:
        str: The formatted HTML output
    """
    # Html5Formatter provides HTML5-optimized defaults
    formatter = Html5Formatter(
        preserve_whitespace_when=tag_in("pre", "code"),
        normalize_whitespace_when=any_of(tag_in("p", "li", "h1", "h2", "h3"), html_inline_elements()),
        indent_size=2,
    )

    # Format real-world messy HTML directly from file
    formatted = formatter.format_file(input_file)
    return formatted


if __name__ == "__main__":
    # This allows the example to be run directly
    examples_dir = Path(__file__).parent.parent.parent / "tests" / "data" / "readme_examples"
    input_file = examples_dir / "article_example.html"
    print(format_article_example(input_file))
