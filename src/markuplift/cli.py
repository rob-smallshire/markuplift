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


def create_external_formatter(xpath_expr: str, command: str, root: etree._Element):
    """Create a text formatter that uses an external program with optimized XPath evaluation."""
    # Create optimized predicate bound to this document
    predicate_factory = create_xpath_predicate_factory(xpath_expr)
    predicate = predicate_factory(root)

    def formatter_func(text: str, formatter: Formatter, physical_level: int) -> str:
        """Format text using external program."""
        if not text.strip():
            return text

        cmd_parts = command.split()
        try:
            result = subprocess.run(cmd_parts, input=text, text=True, capture_output=True, timeout=30)
        except subprocess.TimeoutExpired:
            click.echo(f"Warning: External formatter '{command}' timed out", err=True)
            return text
        except FileNotFoundError:
            click.echo(f"Warning: External formatter command '{cmd_parts[0]}' not found", err=True)
            return text
        except Exception as e:
            click.echo(f"Warning: External formatter '{command}' error: {e}", err=True)
            return text

        if result.returncode != 0:
            click.echo(f"Warning: External formatter '{command}' failed: {result.stderr}", err=True)
            return text

        return result.stdout

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

        # Parse the document early to get the root for XPath evaluation
        tree = etree.parse(BytesIO(content.encode()))
        root = tree.getroot()

        # Create predicate factories from XPath expressions
        block_factories = [create_xpath_predicate_factory(xpath) for xpath in block]
        inline_factories = [create_xpath_predicate_factory(xpath) for xpath in inline]
        normalize_factories = [create_xpath_predicate_factory(xpath) for xpath in normalize_whitespace]
        preserve_factories = [create_xpath_predicate_factory(xpath) for xpath in preserve_whitespace]
        strip_factories = [create_xpath_predicate_factory(xpath) for xpath in strip_whitespace]
        wrap_attr_factories = [create_xpath_predicate_factory(xpath) for xpath in wrap_attributes]

        # Create optimized document-bound predicates (XPath evaluated once per expression)
        block_predicates = [factory(root) for factory in block_factories]
        inline_predicates = [factory(root) for factory in inline_factories]
        normalize_predicates = [factory(root) for factory in normalize_factories]
        preserve_predicates = [factory(root) for factory in preserve_factories]
        strip_predicates = [factory(root) for factory in strip_factories]
        wrap_attr_predicates = [factory(root) for factory in wrap_attr_factories]

        # Combine multiple predicates with OR logic
        def combine_predicates(predicates):
            if not predicates:
                return lambda e: False
            return lambda e: any(pred(e) for pred in predicates)

        # Create text formatters from external programs
        text_formatters = {}
        for xpath_expr, command in text_formatter:
            predicate, formatter_func = create_external_formatter(xpath_expr, command, root)
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

        # Format the already-parsed tree (no need to re-parse)
        formatted = formatter.format_tree(tree, doctype=doctype, xml_declaration=xml_declaration)

        # Write output
        output.write(formatted)

    except etree.XMLSyntaxError as e:
        raise click.ClickException(f"XML parsing error: {e}")
    except Exception as e:
        raise click.ClickException(f"Formatting error: {e}")


if __name__ == "__main__":
    cli()
