#!/usr/bin/env python3
"""
README.md Generator for MarkupLift

This script generates README.md from a Jinja2 template using:
1. Real messy XML/HTML input files from tests/data/readme_examples/
2. Verified pretty output from ApprovalTests .approved.txt files
3. Reusable example functions from src/examples/

The generated README contains tested, working examples that stay in sync with the code.
"""

import inspect
import sys
from pathlib import Path

import jinja2

# Add src to path so we can import examples
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from examples.attribute_formatters import num_css_properties, css_multiline_formatter, format_attribute_formatting_example
from examples.python_api_basic import format_documentation_example
from examples.real_world_article import format_article_example
from examples.complex_predicates import elements_with_attribute_values, table_cells_in_columns
from examples.complex_predicates_usage import format_complex_predicates_example
from examples.xml_document_formatting import format_xml_document_example
from markuplift import Formatter
from markuplift.predicates import html_block_elements


def load_file(file_path: Path) -> str:
    """Load content from a file."""
    return file_path.read_text().strip()


def load_test_data(filename: str) -> str:
    """Load messy input HTML/XML from test data."""
    test_data_dir = Path(__file__).parent.parent / "tests" / "data" / "readme_examples"
    return load_file(test_data_dir / filename)


def load_cli_test_data(filename: str) -> str:
    """Load CLI example files."""
    cli_data_dir = Path(__file__).parent.parent / "tests" / "data" / "cli_examples"
    return load_file(cli_data_dir / filename)


def format_cli_demo_for_readme() -> str:
    """Format CLI demo output for README with proper Markdown structure."""
    tests_dir = Path(__file__).parent.parent / "tests"
    approved_file = tests_dir / "TestCLIDemo.test_cli_demo_execution.approved.txt"
    raw_output = load_file(approved_file)

    # Split content into sections and format appropriately
    lines = raw_output.split('\n')
    result = []

    # Add introduction
    result.append('Here are three comprehensive examples showing different ways to use MarkupLift from the command line:')
    result.append('')

    demo_count = 0
    i = 0
    while i < len(lines):
        line = lines[i]

        # Skip the header
        if '=== MarkupLift CLI Demo ===' in line:
            i += 1
            continue

        # Skip the file list section entirely
        if line.startswith('📁'):
            # Skip to next meaningful section
            while i < len(lines) and not line.startswith('📝'):
                i += 1
                if i < len(lines):
                    line = lines[i]
            # Don't increment i here since we want to process the 📝 line

        # Process input sections with context
        if line.startswith('📝 Before formatting'):
            demo_count += 1
            # Extract filename from the line
            filename = line.split('(')[1].split(')')[0] if '(' in line and ')' in line else 'file'

            # Add demo context based on filename
            if 'config.xml' in filename:
                result.append('#### Demo 1: Basic XML Formatting')
                result.append('')
                result.append('This demonstrates the most basic usage - formatting a messy XML configuration file with default settings.')
                result.append('')
                result.append('**Input:**')
            elif 'article.html' in filename:
                result.append('#### Demo 2: Custom Block Elements')
                result.append('')
                result.append('This shows how to customize which elements are treated as block elements using XPath expressions. This is particularly useful for HTML documents where you want specific semantic elements to be formatted as blocks.')
                result.append('')
                result.append('**Input:**')

            result.append('')

        # Handle command lines with context
        elif line.strip().startswith('$ '):
            if 'stdin' in ' '.join(lines[max(0, i-3):i+1]):  # Check context for stdin demo
                result.append('#### Demo 3: Stdin/Stdout Processing')
                result.append('')
                result.append('This demonstrates pipeline usage, reading from stdin and formatting the output. This is useful for integrating MarkupLift into shell scripts and build processes.')
                result.append('')

            result.append('**Command:**')
            result.append('```bash')
            result.append(line.strip())
            result.append('```')
            result.append('')

        # Handle XML/HTML content blocks with filename comments
        elif (line.strip().startswith('<?xml') or
              line.strip().startswith('<!DOCTYPE') or
              line.strip().startswith('<configuration>') or
              line.strip().startswith('<html>')):

            # Determine format and filename from context
            format_type = "html" if "<!DOCTYPE html>" in line else "xml"

            # Look back for filename context
            filename = None
            for j in range(max(0, i-10), i):
                if 'config.xml' in lines[j]:
                    filename = "messy_config.xml"
                    break
                elif 'article.html' in lines[j]:
                    filename = "messy_article.html"
                    break

            # Look ahead for output context
            is_output = False
            for j in range(max(0, i-5), i):
                if 'Basic formatting:' in lines[j] or 'Format with custom' in lines[j] or 'Saved to formatted' in lines[j]:
                    is_output = True
                    break

            # Collect the entire block
            xml_lines = []
            while i < len(lines) and lines[i].strip():
                if (lines[i].startswith('✨') or
                    lines[i].startswith('📝') or
                    lines[i].startswith('🧹')):
                    break
                xml_lines.append(lines[i])
                i += 1

            result.append(f'```{format_type}')
            result.append('\n'.join(xml_lines).strip())
            result.append('```')
            result.append('')
            i -= 1  # Back up one since we'll increment at the end

        # Skip separator lines and unwanted content
        elif (line.strip() and all(c == '-' for c in line.strip()) or
              line.startswith('✨') or
              line.startswith('🧹') or
              line.startswith('✅') or
              'Created demo files:' in line or
              'Saved to formatted_config.xml:' in line):
            pass

        i += 1

    return '\n'.join(result)


def load_approved_output(test_name: str) -> str:
    """Load approved output from ApprovalTests."""
    tests_dir = Path(__file__).parent.parent / "tests"
    approved_file = tests_dir / f"TestReadmeExamples.{test_name}.approved.txt"
    return load_file(approved_file)


def get_function_source(func) -> str:
    """Get clean source code for a function."""
    source = inspect.getsource(func)
    # Remove leading whitespace to normalize indentation
    lines = source.splitlines()
    if lines:
        # Find minimum indentation (excluding empty lines)
        indents = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
        if indents:
            min_indent = min(indents)
            lines = [line[min_indent:] if len(line) > min_indent else line for line in lines]
    return '\n'.join(lines)


def generate_readme():
    """Generate README.md from template and test data."""

    # Prepare template data
    template_data = {
        # Formatted CLI demo content
        'cli_demo_content': format_cli_demo_for_readme(),

        # Example inputs (messy HTML/XML)
        'documentation_input': load_test_data('documentation_example.html'),
        'article_input': load_test_data('article_example.html'),
        'form_input': load_test_data('form_example.html'),
        'complex_predicates_input': load_test_data('complex_predicates_example.html'),
        'xml_document_input': load_test_data('xml_document_example.xml'),
        'attribute_formatting_input': load_test_data('attribute_formatting_example.html'),

        # Example outputs (verified by ApprovalTests)
        'documentation_output': load_approved_output('test_python_api_nested_list_example'),
        'article_output': load_approved_output('test_real_world_article_example'),
        'form_output': load_approved_output('test_advanced_form_example'),
        'complex_predicates_output': load_approved_output('test_complex_predicates_example'),
        'xml_document_output': load_approved_output('test_xml_document_formatting_example'),
        'attribute_formatting_output': load_approved_output('test_attribute_formatting_example'),

        # Example function source code
        'code_in_documentation_sections_source': f"{get_function_source(elements_with_attribute_values)}\n\n{get_function_source(table_cells_in_columns)}",
        'complex_predicates_usage_source': get_function_source(format_complex_predicates_example),
        'xml_document_formatting_source': get_function_source(format_xml_document_example),
        'num_css_properties_source': get_function_source(num_css_properties),
        'css_multiline_formatter_source': get_function_source(css_multiline_formatter),
        'attribute_formatting_source': get_function_source(format_attribute_formatting_example),
        'python_api_basic_source': get_function_source(format_documentation_example),
        'real_world_article_source': get_function_source(format_article_example),
    }

    # Setup Jinja2
    template_dir = Path(__file__).parent
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Load and render template
    template = env.get_template('README.md.j2')
    readme_content = template.render(**template_data)

    # Write README.md
    readme_path = Path(__file__).parent.parent / "README.md"
    readme_path.write_text(readme_content)

    print(f"Generated {readme_path}")
    print("✅ README.md updated with tested examples!")


if __name__ == "__main__":
    generate_readme()