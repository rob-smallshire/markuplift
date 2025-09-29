"""Command-line interface for MarkupLift.

This module provides the CLI for MarkupLift, allowing users to format XML and HTML
documents from the command line with configurable options for block/inline elements,
whitespace handling, and external text formatters.

The CLI uses ElementPredicateFactory functions from the predicates module to create
optimized formatting rules based on XPath expressions provided by the user.
"""

import subprocess
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from markuplift.document_formatter import DocumentFormatter
from lxml import etree

from markuplift.formatter import Formatter
from markuplift.html5_formatter import Html5Formatter
from markuplift.xml_formatter import XmlFormatter
from markuplift.predicates import matches_xpath, PredicateError
from markuplift.types import ElementType, TextContentFormatter, ElementPredicateFactory


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
@click.option(
    "--attribute-formatter",
    nargs=3,
    multiple=True,
    metavar="XPATH ATTRIBUTE COMMAND",
    help="Apply external formatter to attribute values. XPATH selects elements, ATTRIBUTE is the attribute name, COMMAND is the external program.",
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
    attribute_formatter,
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
    # Format CSS attributes with external formatter
    markuplift format input.html --attribute-formatter "//div" "style" "css-beautify"

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
        text_formatter_factories: dict[ElementPredicateFactory, TextContentFormatter] = {}
        for xpath_expr, command in text_formatter:
            try:
                factory = matches_xpath(xpath_expr)
            except PredicateError as e:
                raise click.ClickException(str(e))

            def create_formatter(cmd=command) -> TextContentFormatter:  # Capture command in closure
                def formatter_func(text: str, doc_formatter: "DocumentFormatter", physical_level: int) -> str:
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

        # Create attribute formatter factories from external programs
        attribute_formatter_factories = {}
        for xpath_expr, attribute_name, command in attribute_formatter:
            try:
                # For CLI, we combine XPath element selection with attribute name matching
                # Create a factory that only matches the specified attribute on elements matching the XPath
                element_factory = matches_xpath(xpath_expr)

                def create_combined_factory(elem_factory=element_factory, attr_name=attribute_name):
                    def combined_factory(root):
                        element_pred = elem_factory(root)

                        def attribute_pred(element, attr_name_test, attr_value):
                            return element_pred(element) and attr_name_test == attr_name

                        return attribute_pred

                    return combined_factory

                attribute_factory = create_combined_factory()
            except PredicateError as e:
                raise click.ClickException(str(e))

            def create_attribute_formatter(cmd=command):  # Capture command in closure
                def formatter_func(text, doc_formatter, physical_level):
                    if not text.strip():
                        return text
                    try:
                        cmd_parts = cmd.split()
                        result = subprocess.run(cmd_parts, input=text, text=True, capture_output=True, timeout=30)
                        if result.returncode != 0:
                            click.echo(
                                f"Warning: External attribute formatter '{cmd}' failed: {result.stderr}", err=True
                            )
                            return text
                        return result.stdout
                    except subprocess.TimeoutExpired:
                        click.echo(f"Warning: External attribute formatter '{cmd}' timed out", err=True)
                        return text
                    except FileNotFoundError:
                        click.echo(
                            f"Warning: External attribute formatter command '{cmd.split()[0]}' not found", err=True
                        )
                        return text
                    except Exception as e:
                        click.echo(f"Warning: External attribute formatter '{cmd}' error: {e}", err=True)
                        return text

                return formatter_func

            attribute_formatter_factories[attribute_factory] = create_attribute_formatter()

        # Create formatter with factory functions - much cleaner!
        formatter = Formatter(
            block_when=combine_factories(block),
            inline_when=combine_factories(inline),
            normalize_whitespace_when=combine_factories(normalize_whitespace),
            strip_whitespace_when=combine_factories(strip_whitespace),
            preserve_whitespace_when=combine_factories(preserve_whitespace),
            wrap_attributes_when=combine_factories(wrap_attributes),
            reformat_text_when=text_formatter_factories,
            reformat_attribute_when=attribute_formatter_factories,
            indent_size=indent_size,
            default_type=ElementType.BLOCK if default_type == "block" else ElementType.INLINE,
        )

        # Format the content - Formatter handles parsing and optimization internally
        formatted = formatter.format_str(content, doctype=doctype, xml_declaration=xml_declaration)

        # Write output
        output.write(formatted)

    except etree.XMLSyntaxError as e:
        raise click.ClickException(f"XML parsing error: {e}")
    except Exception as e:
        raise click.ClickException(f"Formatting error: {e}")


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
@click.option(
    "--attribute-formatter",
    nargs=3,
    multiple=True,
    metavar="XPATH ATTRIBUTE COMMAND",
    help="Apply external formatter to attribute values. XPATH selects elements, ATTRIBUTE is the attribute name, COMMAND is the external program.",
)
@click.option("--indent-size", type=int, default=2, help="Number of spaces for each indentation level (default: 2)")
@click.option(
    "--default-type",
    type=click.Choice(["block", "inline"]),
    default="block",
    help="Default element type for unclassified elements (default: block)",
)
def format_html(
    input_file,
    output,
    block,
    inline,
    normalize_whitespace,
    preserve_whitespace,
    strip_whitespace,
    wrap_attributes,
    text_formatter,
    attribute_formatter,
    indent_size,
    default_type,
):
    """Format HTML documents using HTML5 best practices.

    INPUT_FILE can be a file path or '-' for stdin (default).

    This command uses Html5Formatter which includes:
    - Proper HTML5 DOCTYPE declaration
    - HTML5-aware void element handling
    - HTML-specific entity escaping

    Examples:

    \b
    # Format HTML file to stdout
    markuplift format-html input.html

    \b
    # Format with custom block elements for semantic HTML
    markuplift format-html input.html --block "//article | //section | //aside"

    \b
    # Format CSS style attributes with external formatter
    markuplift format-html input.html --attribute-formatter "//div" "style" "prettier --parser css"

    \b
    # Format from stdin to file
    cat input.html | markuplift format-html --output formatted.html
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
        text_formatter_factories: dict[ElementPredicateFactory, TextContentFormatter] = {}
        for xpath_expr, command in text_formatter:
            try:
                factory = matches_xpath(xpath_expr)
            except PredicateError as e:
                raise click.ClickException(str(e))

            def create_formatter(cmd=command) -> TextContentFormatter:  # Capture command in closure
                def formatter_func(text: str, doc_formatter: "DocumentFormatter", physical_level: int) -> str:
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

        # Create attribute formatter factories from external programs
        attribute_formatter_factories = {}
        for xpath_expr, attribute_name, command in attribute_formatter:
            try:
                # For CLI, we combine XPath element selection with attribute name matching
                # Create a factory that only matches the specified attribute on elements matching the XPath
                element_factory = matches_xpath(xpath_expr)

                def create_combined_factory(elem_factory=element_factory, attr_name=attribute_name):
                    def combined_factory(root):
                        element_pred = elem_factory(root)

                        def attribute_pred(element, attr_name_test, attr_value):
                            return element_pred(element) and attr_name_test == attr_name

                        return attribute_pred

                    return combined_factory

                attribute_factory = create_combined_factory()
            except PredicateError as e:
                raise click.ClickException(str(e))

            def create_attribute_formatter(cmd=command):  # Capture command in closure
                def formatter_func(text, doc_formatter, physical_level):
                    if not text.strip():
                        return text
                    try:
                        cmd_parts = cmd.split()
                        result = subprocess.run(cmd_parts, input=text, text=True, capture_output=True, timeout=30)
                        if result.returncode != 0:
                            click.echo(
                                f"Warning: External attribute formatter '{cmd}' failed: {result.stderr}", err=True
                            )
                            return text
                        return result.stdout
                    except subprocess.TimeoutExpired:
                        click.echo(f"Warning: External attribute formatter '{cmd}' timed out", err=True)
                        return text
                    except FileNotFoundError:
                        click.echo(
                            f"Warning: External attribute formatter command '{cmd.split()[0]}' not found", err=True
                        )
                        return text
                    except Exception as e:
                        click.echo(f"Warning: External attribute formatter '{cmd}' error: {e}", err=True)
                        return text

                return formatter_func

            attribute_formatter_factories[attribute_factory] = create_attribute_formatter()

        # Create HTML5 formatter with factory functions
        formatter = Html5Formatter(
            block_when=combine_factories(block),
            inline_when=combine_factories(inline),
            normalize_whitespace_when=combine_factories(normalize_whitespace),
            strip_whitespace_when=combine_factories(strip_whitespace),
            preserve_whitespace_when=combine_factories(preserve_whitespace),
            wrap_attributes_when=combine_factories(wrap_attributes),
            reformat_text_when=text_formatter_factories,
            reformat_attribute_when=attribute_formatter_factories,
            indent_size=indent_size,
            default_type=ElementType.BLOCK if default_type == "block" else ElementType.INLINE,
        )

        # Format the content
        formatted = formatter.format_str(content)

        # Write output
        output.write(formatted)

    except etree.XMLSyntaxError as e:
        raise click.ClickException(f"HTML parsing error: {e}")
    except Exception as e:
        raise click.ClickException(f"Formatting error: {e}")


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
@click.option(
    "--attribute-formatter",
    nargs=3,
    multiple=True,
    metavar="XPATH ATTRIBUTE COMMAND",
    help="Apply external formatter to attribute values. XPATH selects elements, ATTRIBUTE is the attribute name, COMMAND is the external program.",
)
@click.option("--indent-size", type=int, default=2, help="Number of spaces for each indentation level (default: 2)")
@click.option(
    "--default-type",
    type=click.Choice(["block", "inline"]),
    default="block",
    help="Default element type for unclassified elements (default: block)",
)
@click.option(
    "--xml-declaration/--no-xml-declaration", default=True, help="Include XML declaration in output (default: yes)"
)
def format_xml(
    input_file,
    output,
    block,
    inline,
    normalize_whitespace,
    preserve_whitespace,
    strip_whitespace,
    wrap_attributes,
    text_formatter,
    attribute_formatter,
    indent_size,
    default_type,
    xml_declaration,
):
    """Format XML documents using XML best practices.

    INPUT_FILE can be a file path or '-' for stdin (default).

    This command uses XmlFormatter which includes:
    - Proper XML declaration handling
    - XML-specific entity escaping
    - Self-closing tag support

    Examples:

    \b
    # Format XML file to stdout
    markuplift format-xml input.xml

    \b
    # Format with custom block elements for document structure
    markuplift format-xml input.xml --block "//section | //chapter"

    \b
    # Format configuration attributes with external formatter
    markuplift format-xml input.xml --attribute-formatter "//config" "value" "format-config-value"

    \b
    # Format from stdin to file with XML declaration
    cat input.xml | markuplift format-xml --output formatted.xml --xml-declaration
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
        text_formatter_factories: dict[ElementPredicateFactory, TextContentFormatter] = {}
        for xpath_expr, command in text_formatter:
            try:
                factory = matches_xpath(xpath_expr)
            except PredicateError as e:
                raise click.ClickException(str(e))

            def create_formatter(cmd=command) -> TextContentFormatter:  # Capture command in closure
                def formatter_func(text: str, doc_formatter: "DocumentFormatter", physical_level: int) -> str:
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

        # Create attribute formatter factories from external programs
        attribute_formatter_factories = {}
        for xpath_expr, attribute_name, command in attribute_formatter:
            try:
                # For CLI, we combine XPath element selection with attribute name matching
                # Create a factory that only matches the specified attribute on elements matching the XPath
                element_factory = matches_xpath(xpath_expr)

                def create_combined_factory(elem_factory=element_factory, attr_name=attribute_name):
                    def combined_factory(root):
                        element_pred = elem_factory(root)

                        def attribute_pred(element, attr_name_test, attr_value):
                            return element_pred(element) and attr_name_test == attr_name

                        return attribute_pred

                    return combined_factory

                attribute_factory = create_combined_factory()
            except PredicateError as e:
                raise click.ClickException(str(e))

            def create_attribute_formatter(cmd=command):  # Capture command in closure
                def formatter_func(text, doc_formatter, physical_level):
                    if not text.strip():
                        return text
                    try:
                        cmd_parts = cmd.split()
                        result = subprocess.run(cmd_parts, input=text, text=True, capture_output=True, timeout=30)
                        if result.returncode != 0:
                            click.echo(
                                f"Warning: External attribute formatter '{cmd}' failed: {result.stderr}", err=True
                            )
                            return text
                        return result.stdout
                    except subprocess.TimeoutExpired:
                        click.echo(f"Warning: External attribute formatter '{cmd}' timed out", err=True)
                        return text
                    except FileNotFoundError:
                        click.echo(
                            f"Warning: External attribute formatter command '{cmd.split()[0]}' not found", err=True
                        )
                        return text
                    except Exception as e:
                        click.echo(f"Warning: External attribute formatter '{cmd}' error: {e}", err=True)
                        return text

                return formatter_func

            attribute_formatter_factories[attribute_factory] = create_attribute_formatter()

        # Create XML formatter with factory functions
        formatter = XmlFormatter(
            block_when=combine_factories(block),
            inline_when=combine_factories(inline),
            normalize_whitespace_when=combine_factories(normalize_whitespace),
            strip_whitespace_when=combine_factories(strip_whitespace),
            preserve_whitespace_when=combine_factories(preserve_whitespace),
            wrap_attributes_when=combine_factories(wrap_attributes),
            reformat_text_when=text_formatter_factories,
            reformat_attribute_when=attribute_formatter_factories,
            indent_size=indent_size,
            default_type=ElementType.BLOCK if default_type == "block" else ElementType.INLINE,
        )

        # Format the content
        formatted = formatter.format_str(content, xml_declaration=xml_declaration)

        # Write output
        output.write(formatted)

    except etree.XMLSyntaxError as e:
        raise click.ClickException(f"XML parsing error: {e}")
    except Exception as e:
        raise click.ClickException(f"Formatting error: {e}")


if __name__ == "__main__":
    cli()
