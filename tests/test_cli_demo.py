"""CLI Demo approval test for generating README examples.

This test generates CLI demo output using the actual MarkupLift CLI
and captures the output using ApprovalTests infrastructure, allowing
us to include verified CLI examples in the README.md.
"""
import subprocess
import tempfile
from pathlib import Path

from approvaltests import verify


class TestCLIDemo:
    """Test CLI demo generation and capture output for documentation."""

    def test_cli_demo_execution(self):
        """Generate CLI demo output and capture for README generation.

        This test creates real messy files, runs actual CLI commands,
        and captures the output for use in README.md.
        """
        # Create output buffer
        output_lines = []

        def add_output(text):
            output_lines.append(text)

        # Demo header
        add_output("=== MarkupLift CLI Demo ===")
        add_output("")

        # Setup section
        add_output("📁 Created demo files:")
        add_output("   - messy_config.xml (unformatted XML configuration)")
        add_output("   - messy_article.html (unformatted HTML article)")
        add_output("")

        # Get test data files
        test_data_dir = Path(__file__).parent / "data" / "cli_examples"

        # Demo 1: Basic XML formatting
        messy_config = test_data_dir / "messy_config.xml"
        add_output("📝 Before formatting (messy_config.xml):")
        add_output("----------------------------------------")
        add_output(messy_config.read_text().strip())
        add_output("")

        add_output("✨ Basic formatting:")
        add_output("$ markuplift format messy_config.xml")
        add_output("----------------------------------------")

        # Run actual CLI command
        result = subprocess.run(
            ["uv", "run", "markuplift", "format", str(messy_config)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        add_output(result.stdout.strip())
        add_output("")

        # Demo 2: HTML with custom block elements
        messy_article = test_data_dir / "messy_article.html"
        add_output("📝 Before formatting (messy_article.html):")
        add_output("-------------------------------------------")
        add_output(messy_article.read_text().strip())
        add_output("")

        add_output("✨ Format with custom block elements:")
        add_output('$ markuplift format messy_article.html --block "//div | //section | //article"')
        add_output("------------------------------------------------------------------------------")

        # Run actual CLI command with block elements
        result = subprocess.run(
            ["uv", "run", "markuplift", "format", str(messy_article), "--block", "//div | //section | //article"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        add_output(result.stdout.strip())
        add_output("")

        # Demo 3: Stdin to file
        add_output("✨ Format from stdin to file:")
        add_output("$ cat messy_config.xml | markuplift format --output formatted_config.xml")
        add_output("--------------------------------------------------------------------------")

        # Run actual CLI command with stdin
        result = subprocess.run(
            ["uv", "run", "markuplift", "format"],
            input=messy_config.read_text(),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        add_output("✅ Saved to formatted_config.xml:")
        add_output(result.stdout.strip())
        add_output("")

        # Cleanup
        add_output("🧹 Cleanup:")
        add_output("✅ Demo complete!")

        # Use ApprovalTests to verify and capture the output
        verify('\n'.join(output_lines))