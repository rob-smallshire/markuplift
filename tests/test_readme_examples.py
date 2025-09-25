"""Tests for examples shown in README.md.

This ensures that all examples in the README are accurate and working.
"""

from markuplift import Formatter
from markuplift.predicates import html_block_elements, html_inline_elements, tag_in, any_of


class TestReadmeExamples:
    """Test all examples from README.md to ensure accuracy."""

    def test_python_api_nested_list_example(self):
        """Test the Python API example with whitespace preservation from README."""
        # This is the exact example from the README
        formatter = Formatter(
            block_when=html_block_elements(),
            inline_when=html_inline_elements(),
            preserve_whitespace_when=tag_in("pre", "code"),
            indent_size=2
        )

        # Format complex HTML with code examples (preserves whitespace in <code>)
        messy_html = (
            '<div><h3>Documentation</h3><p>Here are some    spaced    examples:</p>'
            '<ul><li>Installation: <code>   pip install markuplift   </code></li>'
            '<li>Basic <em>configuration</em> and setup</li><li>Code example:'
            '<pre>    def format_xml():\n        return "beautiful"\n    </pre></li></ul></div>'
        )
        formatted = formatter.format_str(messy_html)

        expected_output = """<div>
  <h3>Documentation</h3>
  <p>Here are some    spaced    examples:</p>
  <ul>
    <li>Installation: <code>   pip install markuplift   </code></li>
    <li>Basic <em>configuration</em> and setup</li>
    <li>Code example:
      <pre>    def format_xml():
        return "beautiful"
    </pre>
    </li>
  </ul>
</div>"""

        assert formatted.strip() == expected_output.strip()

    def test_real_world_article_example(self):
        """Test the real-world article example with normalize and preserve whitespace from README."""
        formatter = Formatter(
            block_when=html_block_elements(),
            inline_when=html_inline_elements(),
            preserve_whitespace_when=tag_in("pre", "code"),
            normalize_whitespace_when=any_of(tag_in("p", "li"), html_inline_elements()),
            indent_size=2
        )

        # Real-world messy HTML with code blocks and excessive whitespace
        messy_html = (
            '<article><h1>Using   Markuplift</h1><section><h2>Code    Formatting</h2>'
            '<p>Here\'s how to    use   our   API   with   proper   spacing:</p>'
            '<pre><code>from markuplift import Formatter\nformatter = Formatter(\n    '
            'preserve_whitespace=True\n)</code></pre><p>The   <em>preserve_whitespace</em>   '
            'feature   keeps   code   formatting   intact   while   <strong>normalizing</strong>   '
            'text   content!</p></section></article>'
        )

        formatted = formatter.format_str(messy_html)

        expected_output = """<article>
  <h1>Using   Markuplift</h1>
  <section>
    <h2>Code    Formatting</h2>
    <p>Here's how to use our API with proper spacing:</p>
    <pre><code>from markuplift import Formatter formatter = Formatter( preserve_whitespace=True )</code></pre>
    <p>The <em>preserve_whitespace</em> feature keeps code formatting intact while <strong>normalizing</strong> text content!</p>
  </section>
</article>"""

        assert formatted.strip() == expected_output.strip()

    def test_advanced_form_example(self):
        """Test the advanced example with comprehensive whitespace control from README."""
        formatter = Formatter(
            block_when=html_block_elements(),
            inline_when=html_inline_elements(),
            preserve_whitespace_when=tag_in("pre", "code", "textarea"),
            normalize_whitespace_when=any_of(tag_in("p", "li", "h1", "h2", "h3"), html_inline_elements()),
            indent_size=2
        )

        # Technical documentation with code, forms, and mixed content
        messy_html = (
            '<div><h2>API   Documentation</h2><p>Use this    form   to   test   the   API:</p>'
            '<form><fieldset><legend>Configuration</legend><div><label>Code Sample: '
            '<textarea name="code">    def example():\n        return "test"\n        # preserve formatting'
            '</textarea></label></div><div><p>Inline   code   like   <code>   format()   </code>   '
            'works   perfectly!</p></div></fieldset></form><h3>Expected   Output:</h3>'
            '<pre>{\n  "status": "formatted",\n  "whitespace": "preserved"\n}</pre></div>'
        )

        formatted = formatter.format_str(messy_html)

        expected_output = """<div>
  <h2>API Documentation</h2>
  <p>Use this form to test the API:</p>
  <form>
    <fieldset>
      <legend>Configuration</legend>
      <div>
        <label>Code Sample: <textarea name="code">    def example():
        return "test"
        # preserve formatting</textarea></label>
      </div>
      <div>
        <p>Inline code like <code> format() </code> works perfectly!</p>
      </div>
    </fieldset>
  </form>
  <h3>Expected Output:</h3>
  <pre>{
  "status": "formatted",
  "whitespace": "preserved"
}</pre>
</div>"""

        assert formatted.strip() == expected_output.strip()

    def test_block_inline_classification(self):
        """Test that our examples correctly demonstrate block vs inline element handling."""
        formatter = Formatter(
            block_when=html_block_elements(),
            inline_when=html_inline_elements(),
            indent_size=2
        )

        # Test specific element classification used in our examples
        test_html = '<ul><li>Text with <em>inline</em> and <strong>more inline</strong> <code>code</code></li></ul>'
        formatted = formatter.format_str(test_html)

        # ul and li should be block (indented), em/strong/code should be inline (same line)
        expected = """<ul>
  <li>Text with <em>inline</em> and <strong>more inline</strong> <code>code</code></li>
</ul>"""

        assert formatted.strip() == expected.strip()

    def test_mixed_content_in_lists(self):
        """Test the specific case mentioned: li with both text and sublist."""
        formatter = Formatter(
            block_when=html_block_elements(),
            inline_when=html_inline_elements(),
            indent_size=2
        )

        # This tests the exact scenario the user mentioned
        test_html = '<ol><li>Item with text <ul><li>Subitem</li></ul></li></ol>'
        formatted = formatter.format_str(test_html)

        expected = """<ol>
  <li>Item with text
    <ul>
      <li>Subitem</li>
    </ul>
  </li>
</ol>"""

        assert formatted.strip() == expected.strip()

    def test_custom_css_class_predicate_example(self):
        """Test the custom CSS class predicate example from README."""
        # Implementation of has_css_class from README
        def has_css_class(class_name: str):
            """Factory for predicate matching elements with a specific CSS class."""
            from markuplift.predicates import PredicateError
            # Level 1: Configuration and validation
            if not class_name or not class_name.strip():
                raise PredicateError("CSS class name cannot be empty")
            if ' ' in class_name:
                raise PredicateError("CSS class name cannot contain spaces")

            clean_class = class_name.strip()

            def create_document_predicate(root):
                # Level 2: Document-specific preparation - find all matching elements once
                matching_elements = set()
                for element in root.iter():
                    class_attr = element.get('class', '')
                    if class_attr and clean_class in class_attr.split():
                        matching_elements.add(element)

                def element_predicate(element):
                    # Level 3: Fast membership test
                    return element in matching_elements
                return element_predicate
            return create_document_predicate

        # Test the exact usage example from README
        formatter = Formatter(
            block_when=html_block_elements(),
            inline_when=html_inline_elements(),
            preserve_whitespace_when=has_css_class("code-block"),
            normalize_whitespace_when=any_of(has_css_class("prose"), html_inline_elements()),
            indent_size=2
        )

        # Format HTML with CSS classes (exact example from README)
        html = '<div class="container"><p class="prose">Text content</p><pre class="code-block">preserved code</pre></div>'
        formatted = formatter.format_str(html)

        expected_output = """<div class="container">
  <p class="prose">Text content</p>
  <pre class="code-block">preserved code</pre>
</div>"""

        assert formatted.strip() == expected_output.strip()

    def test_custom_predicate_validation(self):
        """Test validation in the custom CSS class predicate example."""
        # Implementation of has_css_class from README
        def has_css_class(class_name: str):
            """Factory for predicate matching elements with a specific CSS class."""
            from markuplift.predicates import PredicateError
            # Level 1: Configuration and validation
            if not class_name or not class_name.strip():
                raise PredicateError("CSS class name cannot be empty")
            if ' ' in class_name:
                raise PredicateError("CSS class name cannot contain spaces")

            clean_class = class_name.strip()

            def create_document_predicate(root):
                # Level 2: Document-specific preparation - find all matching elements once
                matching_elements = set()
                for element in root.iter():
                    class_attr = element.get('class', '')
                    if class_attr and clean_class in class_attr.split():
                        matching_elements.add(element)

                def element_predicate(element):
                    # Level 3: Fast membership test
                    return element in matching_elements
                return element_predicate
            return create_document_predicate

        from markuplift.predicates import PredicateError
        import pytest

        # Test empty class name validation
        with pytest.raises(PredicateError, match="CSS class name cannot be empty"):
            has_css_class("")

        with pytest.raises(PredicateError, match="CSS class name cannot be empty"):
            has_css_class("   ")

        # Test spaces in class name validation
        with pytest.raises(PredicateError, match="CSS class name cannot contain spaces"):
            has_css_class("class with spaces")