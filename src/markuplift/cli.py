import subprocess
from io import BytesIO

import click
from lxml import etree

from markuplift.formatter import Formatter


def create_xpath_predicate_factory(xpath_expr: str):
    """Level 1: Create a factory for XPath-based predicates.

    Returns a function that takes a document root and returns an optimized predicate.
    This triple-nested approach evaluates XPath expressions only once per document
    rather than once per element, dramatically improving performance.
    """

    def create_document_predicate(root: etree._Element):
        """Level 2: Document context - evaluate XPath once per document."""
        try:
            # Evaluate XPath once and store results as a set for O(1) lookups
            matches = set(root.xpath(xpath_expr))
        except etree.XPathEvalError as e:
            raise click.ClickException(f"Invalid XPath expression '{xpath_expr}': {e}")

        def element_predicate(element: etree._Element) -> bool:
            """Level 3: Fast O(1) membership test."""
            return element in matches

        return element_predicate

    return create_document_predicate



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
            factories = [create_xpath_predicate_factory(xpath) for xpath in xpath_list]
            def combined_factory(root):
                predicates = [factory(root) for factory in factories]
                return lambda e: any(pred(e) for pred in predicates)
            return combined_factory

        # Create text formatter factories from external programs
        text_formatter_factories = {}
        for xpath_expr, command in text_formatter:
            factory = create_xpath_predicate_factory(xpath_expr)
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
