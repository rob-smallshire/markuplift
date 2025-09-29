#!/usr/bin/env python3
"""Example demonstrating CDATA support in MarkupLift.

This example shows how to:
1. Use TextContentFormatter functions to create CDATA output
2. Use the singledispatch pattern for type-specific CDATA handling
3. Configure formatters with CDATA-related parameters
"""

from functools import singledispatch
from lxml.etree import CDATA

from markuplift import XmlFormatter
from markuplift.predicates import tag_in
from markuplift.types import TextContent


def create_cdata_for_scripts():
    """Example: Convert script content to CDATA for safe XML embedding."""

    def script_to_cdata(content: TextContent, formatter, level: int) -> CDATA:
        """Convert script text content to CDATA for XML safety."""
        if isinstance(content, str):
            return CDATA(content.strip())
        return content  # Already CDATA

    input_xml = """<root>
<script>
function example() {
    if (x &lt; 5 &amp;&amp; y &gt; 10) {
        alert("Hello &amp; welcome!");
    }
}
</script>
<script>
var data = "&lt;element&gt;content&lt;/element&gt;";
console.log(data);
</script>
</root>"""

    formatter = XmlFormatter(
        reformat_text_when={
            tag_in("script"): script_to_cdata
        }
    )

    result = formatter.format_str(input_xml)
    return result


def singledispatch_cdata_example():
    """Example: Use singledispatch for elegant type-specific CDATA handling."""

    @singledispatch
    def process_code_content(content: TextContent, formatter, level: int) -> TextContent:
        """Process code content based on its type."""
        raise NotImplementedError(f"No handler for type {type(content)}")

    @process_code_content.register
    def _(content: str, formatter, level: int) -> CDATA:
        """Convert string content to CDATA with a comment."""
        return CDATA(f"// Added by formatter\n{content.strip()}")

    @process_code_content.register
    def _(content: CDATA, formatter, level: int) -> CDATA:
        """Process existing CDATA content."""
        inner_content = str(content)  # Extract content via temporary element
        return CDATA(f"// CDATA processed\n{inner_content}")

    # Test with both string and CDATA input
    string_input = """<code>console.log("hello");</code>"""

    formatter = XmlFormatter(
        reformat_text_when={
            tag_in("code"): process_code_content
        }
    )

    result = formatter.format_str(string_input)
    return result


def format_mixed_content_example():
    """Example: Handle mixed content with selective CDATA formatting."""

    def format_dangerous_content(content: TextContent, formatter, level: int) -> TextContent:
        """Apply CDATA to content that might contain XML-like text."""
        content_str = str(content).strip()

        # Apply CDATA if content contains angle brackets or ampersands
        if '<' in content_str or '&' in content_str or ']]>' in content_str:
            return CDATA(content_str)
        else:
            return content_str

    input_xml = """<document>
<safe-content>This is safe text content</safe-content>
<dangerous-content>This contains &lt;tags&gt; and &amp;entities; that need protection</dangerous-content>
<code-sample>var xml = "&lt;root&gt;&lt;child&gt;value&lt;/child&gt;&lt;/root&gt;";</code-sample>
<normal-text>Regular content without special characters</normal-text>
</document>"""

    formatter = XmlFormatter(
        reformat_text_when={
            tag_in("dangerous-content", "code-sample"): format_dangerous_content
        }
    )

    result = formatter.format_str(input_xml)
    return result


if __name__ == "__main__":
    print("=== CDATA Support Examples ===\n")

    print("1. Script Content to CDATA:")
    print(create_cdata_for_scripts())
    print()

    print("2. SingleDispatch Pattern:")
    print(singledispatch_cdata_example())
    print()

    print("3. Mixed Content with Selective CDATA:")
    print(format_mixed_content_example())
    print()

    print("Note: Due to DocumentFormatter's current architecture, CDATA from")
    print("input documents is converted to escaped text. However, TextContentFormatter")
    print("functions can create new CDATA sections for output.")