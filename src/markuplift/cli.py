import subprocess

import click
from lxml import etree

from markuplift.formatter import Formatter


def xpath_to_predicate(xpath_expr: str):
    """Convert an XPath expression to a predicate function."""

    def predicate(element: etree._Element) -> bool:
        try:
            # Get the root of the tree to evaluate XPath from
            root = element.getroottree().getroot()
            # Find all elements matching the XPath
            matches = root.xpath(xpath_expr)
            # Check if this element is in the matches
            return element in matches
        except etree.XPathEvalError as e:
            raise click.ClickException(f"Invalid XPath expression '{xpath_expr}': {e}")

    return predicate


def create_external_formatter(xpath_expr: str, command: str):
    """Create a text formatter that uses an external program."""
    predicate = xpath_to_predicate(xpath_expr)

    def formatter_func(text: str, formatter: Formatter, physical_level: int) -> str:
        """Format text using external program."""
        if not text.strip():
            return text

        try:
            # Split command into parts for subprocess
            cmd_parts = command.split()
            result = subprocess.run(cmd_parts, input=text, text=True, capture_output=True, timeout=30)

            if result.returncode != 0:
                click.echo(f"Warning: External formatter '{command}' failed: {result.stderr}", err=True)
                return text

            return result.stdout

        except subprocess.TimeoutExpired:
            click.echo(f"Warning: External formatter '{command}' timed out", err=True)
            return text
        except FileNotFoundError:
            click.echo(f"Warning: External formatter command '{cmd_parts[0]}' not found", err=True)
            return text
        except Exception as e:
            click.echo(f"Warning: External formatter '{command}' error: {e}", err=True)
            return text

    return predicate, formatter_func


@click.group()
@click.version_option()
def cli():
    """MarkupLift - A configurable XML and HTML formatter.

    MarkupLift provides flexible formatting of XML and HTML documents with
    configurable predicates for block vs inline elements, whitespace handling,
    and custom text content formatters.
    """
    pass


@cli.command()
@click.argument("input_file", type=click.File("r"), default="-")
@click.option("--output", "-o", type=click.File("w"), default="-", help="Output file (default: stdout)")
@click.option("--block", multiple=True, help="XPath expression for block elements (can be used multiple times)")
@click.option("--inline", multiple=True, help="XPath expression for inline elements (can be used multiple times)")
@click.option(
    "--normalize-whitespace", multiple=True, help="XPath expression for elements that should have normalized whitespace"
)
@click.option(
    "--preserve-whitespace", multiple=True, help="XPath expression for elements that should preserve whitespace"
)
@click.option(
    "--strip-whitespace", multiple=True, help="XPath expression for elements that should have whitespace stripped"
)
@click.option("--wrap-attributes", multiple=True, help="XPath expression for elements that should wrap attributes")
@click.option(
    "--text-formatter",
    nargs=2,
    multiple=True,
    metavar="XPATH COMMAND",
    help="Apply external formatter to text content. XPATH selects elements, COMMAND is the external program.",
)
@click.option("--indent-size", type=int, default=2, help="Number of spaces for each indentation level (default: 2)")
@click.option(
    "--default-type",
    type=click.Choice(["block", "inline"]),
    default="block",
    help="Default element type for unclassified elements (default: block)",
)
@click.option(
    "--xml-declaration/--no-xml-declaration", default=False, help="Include XML declaration in output (default: no)"
)
@click.option("--doctype", help="Custom DOCTYPE declaration to include")
def format(
    input_file,
    output,
    block,
    inline,
    normalize_whitespace,
    preserve_whitespace,
    strip_whitespace,
    wrap_attributes,
    text_formatter,
    indent_size,
    default_type,
    xml_declaration,
    doctype,
):
    """Format XML or HTML documents with configurable formatting rules.

    INPUT_FILE can be a file path or '-' for stdin (default).

    Examples:

    \b
    # Format from file to stdout
    markuplift format input.xml

    \b
    # Format with custom block/inline elements
    markuplift format input.html --block "//div | //section" --inline "//em | //strong"

    \b
    # Use external formatter for JavaScript in script tags
    markuplift format input.html --text-formatter "//script[@type='javascript']" "js-beautify"

    \b
    # Format from stdin to file
    cat input.xml | markuplift format --output formatted.xml
    """
    try:
        # Read input content
        content = input_file.read()

        # Build predicate functions from XPath expressions
        block_predicates = [xpath_to_predicate(xpath) for xpath in block]
        inline_predicates = [xpath_to_predicate(xpath) for xpath in inline]
        normalize_predicates = [xpath_to_predicate(xpath) for xpath in normalize_whitespace]
        preserve_predicates = [xpath_to_predicate(xpath) for xpath in preserve_whitespace]
        strip_predicates = [xpath_to_predicate(xpath) for xpath in strip_whitespace]
        wrap_attr_predicates = [xpath_to_predicate(xpath) for xpath in wrap_attributes]

        # Combine multiple predicates with OR logic
        def combine_predicates(predicates):
            if not predicates:
                return lambda e: False
            return lambda e: any(pred(e) for pred in predicates)

        # Create text formatters from external programs
        text_formatters = {}
        for xpath_expr, command in text_formatter:
            predicate, formatter_func = create_external_formatter(xpath_expr, command)
            text_formatters[predicate] = formatter_func

        # Create formatter with all options
        formatter = Formatter(
            block_predicate=combine_predicates(block_predicates),
            inline_predicate=combine_predicates(inline_predicates),
            normalize_whitespace_predicate=combine_predicates(normalize_predicates),
            preserve_whitespace_predicate=combine_predicates(preserve_predicates),
            strip_whitespace_predicate=combine_predicates(strip_predicates),
            wrap_attributes_predicate=combine_predicates(wrap_attr_predicates),
            text_content_formatters=text_formatters,
            indent_size=indent_size,
            default_type=default_type,
        )

        # Format the content
        formatted = formatter.format_str(content, doctype=doctype, xml_declaration=xml_declaration)

        # Write output
        output.write(formatted)

    except etree.XMLSyntaxError as e:
        raise click.ClickException(f"XML parsing error: {e}")
    except Exception as e:
        raise click.ClickException(f"Formatting error: {e}")


if __name__ == "__main__":
    cli()
