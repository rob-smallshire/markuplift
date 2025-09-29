"""Basic Python API example for README.md.

This module contains the exact example code shown in the README's Python API section.
"""

from pathlib import Path
from markuplift import Html5Formatter
from markuplift.predicates import tag_in


def format_documentation_example(input_file: Path):
    """Format HTML with proper block/inline classification and whitespace preservation.

    This is the main Python API example shown in the README.

    Args:
        input_file: Path to the HTML file to format

    Returns:
        str: The formatted HTML output
    """
    # Create HTML5 formatter with custom whitespace handling
    # Html5Formatter includes sensible HTML5 defaults:
    # - Block elements: <div>, <p>, <ul>, <li>, <h1>-<h6>, etc. get newlines + indentation
    # - Inline elements: <em>, <strong>, <code>, <a>, etc. flow within text
    formatter = Html5Formatter(
        preserve_whitespace_when=tag_in("pre", "code"),  # Keep original spacing inside these
        indent_size=2,
    )

    # Load and format HTML from file
    formatted = formatter.format_file(input_file)
    return formatted


if __name__ == "__main__":
    # This allows the example to be run directly
    from pathlib import Path

    examples_dir = Path(__file__).parent.parent.parent / "tests" / "data" / "readme_examples"
    input_file = examples_dir / "documentation_example.html"
    print(format_documentation_example(str(input_file)))
