"""Parameterized predicates usage example for README.md.

This module demonstrates how to use parameterized predicates for flexible
document formatting that can be customized for different content types.
"""

from pathlib import Path
from markuplift import Html5Formatter
from examples.complex_predicates import elements_with_attribute_values, table_cells_in_columns


def format_complex_predicates_example(input_file: Path):
    """Format HTML using parameterized predicates for content-aware formatting.

    This example shows how to use predicates with parameters to apply different
    formatting rules based on semantic meaning and document structure.

    Args:
        input_file: Path to the HTML file to format

    Returns:
        str: The formatted HTML output
    """
    # Create formatter with parameterized predicate-based rules
    formatter = Html5Formatter(
        # Treat navigation and sidebar elements as block elements
        block_when=elements_with_attribute_values("role", "navigation", "complementary"),
        # Apply special formatting to currency and numeric table columns
        wrap_attributes_when=table_cells_in_columns("price", "currency", "number"),
        # Standard Html5Formatter defaults for other elements
        indent_size=2,
    )

    # Format the document with semantic-aware predicate rules
    formatted = formatter.format_file(input_file)
    return formatted


if __name__ == "__main__":
    # This allows the example to be run directly
    examples_dir = Path(__file__).parent.parent.parent / "tests" / "data" / "readme_examples"
    input_file = examples_dir / "complex_predicates_example.html"
    print(format_complex_predicates_example(input_file))
