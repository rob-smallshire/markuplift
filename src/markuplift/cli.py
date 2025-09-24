"""Command-line interface for MarkupLift.

This module provides the CLI for MarkupLift, allowing users to format XML and HTML
documents from the command line with configurable options for block/inline elements,
whitespace handling, and external text formatters.

The CLI uses ElementPredicateFactory functions from the predicates module to create
optimized formatting rules based on XPath expressions provided by the user.
"""

import subprocess

import click
from lxml import etree

from markuplift.formatter import Formatter
from markuplift.predicates import matches_xpath, PredicateError



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

        # Create combined predicate factories from XPath expressions
        def combine_factories(xpath_list):
            if not xpath_list:
                return None
            try:
                factories = [matches_xpath(xpath) for xpath in xpath_list]
            except PredicateError as e:
                raise click.ClickException(str(e))
            def combined_factory(root):
                predicates = [factory(root) for factory in factories]
                return lambda e: any(pred(e) for pred in predicates)
            return combined_factory

        # Create text formatter factories from external programs
        text_formatter_factories = {}
        for xpath_expr, command in text_formatter:
            try:
                factory = matches_xpath(xpath_expr)
            except PredicateError as e:
                raise click.ClickException(str(e))
            def create_formatter(cmd=command):  # Capture command in closure
                def formatter_func(text, doc_formatter, physical_level):
                    if not text.strip():
                        return text
                    try:
                        cmd_parts = cmd.split()
                        result = subprocess.run(cmd_parts, input=text, text=True, capture_output=True, timeout=30)
                        if result.returncode != 0:
                            click.echo(f"Warning: External formatter '{cmd}' failed: {result.stderr}", err=True)
                            return text
                        return result.stdout
                    except subprocess.TimeoutExpired:
                        click.echo(f"Warning: External formatter '{cmd}' timed out", err=True)
                        return text
                    except FileNotFoundError:
                        click.echo(f"Warning: External formatter command '{cmd.split()[0]}' not found", err=True)
                        return text
                    except Exception as e:
                        click.echo(f"Warning: External formatter '{cmd}' error: {e}", err=True)
                        return text
                return formatter_func
            text_formatter_factories[factory] = create_formatter()

        # Create formatter with factory functions - much cleaner!
        formatter = Formatter(
            block_predicate_factory=combine_factories(block),
            inline_predicate_factory=combine_factories(inline),
            normalize_whitespace_predicate_factory=combine_factories(normalize_whitespace),
            strip_whitespace_predicate_factory=combine_factories(strip_whitespace),
            preserve_whitespace_predicate_factory=combine_factories(preserve_whitespace),
            wrap_attributes_predicate_factory=combine_factories(wrap_attributes),
            text_content_formatters=text_formatter_factories,
            indent_size=indent_size,
            default_type=default_type,
        )

        # Format the content - Formatter handles parsing and optimization internally
        formatted = formatter.format_str(content, doctype=doctype, xml_declaration=xml_declaration)

        # Write output
        output.write(formatted)

    except etree.XMLSyntaxError as e:
        raise click.ClickException(f"XML parsing error: {e}")
    except Exception as e:
        raise click.ClickException(f"Formatting error: {e}")


if __name__ == "__main__":
    cli()
