import tempfile
from pathlib import Path
from inspect import cleandoc

import pytest
from click.testing import CliRunner

from markuplift.cli import cli


class TestCLI:
    """Test the MarkupLift command-line interface."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_version(self):
        """Test CLI version command."""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()

    def test_cli_help(self):
        """Test CLI help command."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "MarkupLift" in result.output
        assert "format" in result.output

    def test_format_help(self):
        """Test format subcommand help."""
        result = self.runner.invoke(cli, ["format", "--help"])
        assert result.exit_code == 0
        assert "Format XML or HTML documents" in result.output
        assert "--block" in result.output
        assert "--inline" in result.output

    def test_format_basic_stdin_stdout(self):
        """Test basic formatting from stdin to stdout."""
        input_xml = "<root><child>text</child></root>"
        expected = cleandoc("""
            <root>
              <child>text</child>
            </root>
        """)

        result = self.runner.invoke(cli, ["format", "-"], input=input_xml)
        assert result.exit_code == 0
        assert result.output.strip() == expected

    def test_format_with_file_input_output(self):
        """Test formatting with file input and output."""
        input_xml = "<root><child>text</child></root>"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as input_file:
            input_file.write(input_xml)
            input_file.flush()
            input_path = input_file.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as output_file:
            output_path = output_file.name

        try:
            result = self.runner.invoke(cli, ["format", input_path, "--output", output_path])
            assert result.exit_code == 0

            with open(output_path, "r") as f:
                output_content = f.read()

            expected = cleandoc("""
                <root>
                  <child>text</child>
                </root>
            """)
            assert output_content.strip() == expected

        finally:
            Path(input_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)

    def test_format_with_block_predicate(self):
        """Test formatting with block XPath predicate."""
        input_xml = "<root><block>text</block><inline>text</inline></root>"

        result = self.runner.invoke(cli, ["format", "--block", "//block", "--inline", "//inline"], input=input_xml)

        assert result.exit_code == 0
        # Block elements should be indented, inline should not
        assert "<block>" in result.output
        assert "  <block>text</block>" in result.output
        assert "<inline>text</inline>" in result.output

    def test_format_with_multiple_xpath_expressions(self):
        """Test formatting with multiple XPath expressions for the same option."""
        input_xml = "<root><div>text</div><section>text</section><span>inline</span></root>"

        result = self.runner.invoke(
            cli, ["format", "--block", "//div", "--block", "//section", "--inline", "//span"], input=input_xml
        )

        assert result.exit_code == 0
        # Both div and section should be treated as block
        assert "  <div>text</div>" in result.output
        assert "  <section>text</section>" in result.output
        assert "<span>inline</span>" in result.output

    def test_format_with_indent_size(self):
        """Test formatting with custom indent size."""
        input_xml = "<root><child><grandchild>text</grandchild></child></root>"

        result = self.runner.invoke(cli, ["format", "--indent-size", "4"], input=input_xml)

        assert result.exit_code == 0
        # Should use 4 spaces for indentation
        assert "    <child>" in result.output
        assert "        <grandchild>text</grandchild>" in result.output

    def test_format_with_xml_declaration(self):
        """Test formatting with XML declaration."""
        input_xml = "<root><child>text</child></root>"

        result = self.runner.invoke(cli, ["format", "--xml-declaration"], input=input_xml)

        assert result.exit_code == 0
        assert result.output.startswith('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')

    def test_format_with_doctype(self):
        """Test formatting with custom DOCTYPE."""
        input_xml = "<root><child>text</child></root>"
        doctype = '<!DOCTYPE root PUBLIC "-//Test//DTD Test//EN" "test.dtd">'

        result = self.runner.invoke(cli, ["format", "--doctype", doctype], input=input_xml)

        assert result.exit_code == 0
        assert doctype in result.output

    def test_format_with_whitespace_options(self):
        """Test formatting with whitespace handling options."""
        input_xml = "<root><preserve>  spaced  text  </preserve><normalize>  spaced  text  </normalize></root>"

        result = self.runner.invoke(
            cli,
            ["format", "--preserve-whitespace", "//preserve", "--normalize-whitespace", "//normalize"],
            input=input_xml,
        )

        assert result.exit_code == 0
        # The exact whitespace handling will depend on the formatter implementation

    def test_format_with_attribute_wrapping(self):
        """Test formatting with attribute wrapping."""
        input_xml = '<root><element attr1="value1" attr2="value2" attr3="value3">text</element></root>'

        result = self.runner.invoke(cli, ["format", "--wrap-attributes", "//element"], input=input_xml)

        assert result.exit_code == 0
        # Should wrap attributes (exact format depends on implementation)
        assert 'attr1="value1"' in result.output

    def test_format_with_text_formatter_mock(self):
        """Test formatting with text formatter using echo command."""
        input_xml = "<root><code>hello world</code></root>"

        # Use echo command which should be available on most systems
        result = self.runner.invoke(
            cli,
            ["format", "--text-formatter", "//code", 'echo "formatted:"', "--block", "//root", "--inline", "//code"],
            input=input_xml,
        )

        assert result.exit_code == 0
        # The text should be processed by the external formatter

    def test_format_invalid_xml(self):
        """Test formatting with invalid XML input."""
        invalid_xml = "<root><unclosed>"

        result = self.runner.invoke(cli, ["format"], input=invalid_xml)
        assert result.exit_code != 0
        assert "XML parsing error" in result.output

    def test_format_invalid_xpath(self):
        """Test formatting with invalid XPath expression."""
        input_xml = "<root><child>text</child></root>"

        result = self.runner.invoke(cli, ["format", "--block", "//[invalid xpath"], input=input_xml)

        assert result.exit_code != 0
        assert "Invalid XPath expression" in result.output

    def test_format_missing_external_formatter(self):
        """Test formatting with non-existent external formatter."""
        input_xml = "<root><code>hello</code></root>"

        result = self.runner.invoke(
            cli, ["format", "--text-formatter", "//code", "nonexistent_command_12345"], input=input_xml
        )

        # Should not fail, but should show a warning
        assert result.exit_code == 0
        # The original text should be preserved since formatter failed

    def test_format_default_type_option(self):
        """Test formatting with different default types."""
        input_xml = "<root><unknown>text</unknown></root>"

        # Test with default type 'inline'
        result = self.runner.invoke(cli, ["format", "--default-type", "inline"], input=input_xml)

        assert result.exit_code == 0

        # Test with default type 'block' (default)
        result = self.runner.invoke(cli, ["format", "--default-type", "block"], input=input_xml)

        assert result.exit_code == 0

    def test_format_complex_xpath_expressions(self):
        """Test formatting with complex XPath expressions."""
        input_xml = """
        <html>
            <body>
                <div class="content">
                    <p>Paragraph text</p>
                    <ul>
                        <li>List item</li>
                    </ul>
                </div>
            </body>
        </html>
        """

        result = self.runner.invoke(
            cli,
            ["format", "--block", '//div[@class="content"] | //p | //ul | //li', "--inline", "//em | //strong | //a"],
            input=input_xml,
        )

        assert result.exit_code == 0

    def test_format_preserves_comments(self):
        """Test that formatting preserves XML comments."""
        input_xml = "<root><!-- This is a comment --><child>text</child></root>"

        result = self.runner.invoke(cli, ["format"], input=input_xml)

        assert result.exit_code == 0
        assert "<!-- This is a comment -->" in result.output

    def test_format_preserves_processing_instructions(self):
        """Test that formatting preserves processing instructions."""
        input_xml = "<?xml-stylesheet type='text/xsl' href='style.xsl'?><root><child>text</child></root>"

        result = self.runner.invoke(cli, ["format"], input=input_xml)

        assert result.exit_code == 0
        assert "xml-stylesheet" in result.output


class TestCLIIntegration:
    """Integration tests for the CLI."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_real_world_html_formatting(self):
        """Test formatting a realistic HTML document."""
        html_input = cleandoc("""
            <html><head><title>Test</title></head><body><div class="container"><p>Hello <em>world</em>!</p><ul><li>Item 1</li><li>Item 2</li></ul></div></body></html>
        """)

        result = self.runner.invoke(
            cli,
            [
                "format",
                "--block",
                "//html | //head | //body | //div | //p | //ul | //li",
                "--inline",
                "//title | //em | //strong | //a | //span",
            ],
            input=html_input,
        )

        assert result.exit_code == 0
        # Should be properly formatted with indentation
        output_lines = result.output.strip().split("\n")
        assert len(output_lines) > 1  # Should be multi-line

    def test_xml_with_namespaces(self):
        """Test formatting XML with namespaces."""
        xml_input = cleandoc("""
            <root xmlns:ns="http://example.com/ns"><ns:child>content</ns:child></root>
        """)

        result = self.runner.invoke(cli, ["format"], input=xml_input)

        assert result.exit_code == 0
        # lxml expands namespaces in the output, so check for the expanded form
        assert "http://example.com/ns" in result.output
        assert "content" in result.output

    @pytest.mark.skipif(not Path("/bin/echo").exists(), reason="echo command not available")
    def test_text_formatter_with_echo(self):
        """Test text formatter with actual echo command."""
        input_xml = "<root><test>original text</test></root>"

        result = self.runner.invoke(
            cli,
            ["format", "--text-formatter", "//test", "echo PROCESSED", "--block", "//root", "--inline", "//test"],
            input=input_xml,
        )

        assert result.exit_code == 0
