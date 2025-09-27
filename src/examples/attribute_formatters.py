"""Custom attribute formatting examples for MarkupLift.

This module demonstrates how to create custom attribute value formatters,
particularly useful for complex attributes like CSS styles.
"""


def num_css_properties(style_value: str) -> int:
    """Count the number of CSS properties in a style attribute value.

    Args:
        style_value: The CSS style attribute value

    Returns:
        Number of CSS properties found

    Example:
        >>> num_css_properties("color: red; background: blue")
        2
        >>> num_css_properties("color: red;")
        1
    """
    return len([prop.strip() for prop in style_value.split(';') if prop.strip()])


def css_multiline_formatter(value, formatter, level):
    """Format CSS as multiline when it has many properties.

    This formatter takes CSS style attributes and formats them with proper
    indentation when they contain multiple properties.

    Args:
        value: The CSS style attribute value to format
        formatter: The MarkupLift formatter instance (for accessing indent settings)
        level: The current indentation level in the document

    Returns:
        Formatted CSS string with proper indentation

    Example:
        Input:  "color: green; background: black; margin: 10px; padding: 5px"
        Output: "\\n    color: green;\\n    background: black;\\n    margin: 10px;\\n    padding: 5px\\n  "
    """
    properties = [prop.strip() for prop in value.split(';') if prop.strip()]
    base_indent = formatter.one_indent * level
    property_indent = formatter.one_indent * (level + 1)
    formatted_props = [f"{property_indent}{prop}" for prop in properties]
    return '\n' + ';\n'.join(formatted_props) + '\n' + base_indent