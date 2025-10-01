"""Escaping strategies for HTML5 vs XML output formatting.

This module provides configurable escaping strategies that handle the differences
between HTML5 and XML formatting requirements, particularly around attribute
value escaping and text content escaping.

The strategy pattern allows MarkupLift to produce format-appropriate output
while maintaining the same core formatting engine.
"""

from abc import ABC, abstractmethod
from xml.sax.saxutils import escape, quoteattr
from markuplift.utilities import html_friendly_quoteattr


class EscapingStrategy(ABC):
    """Abstract base class for escaping strategies.

    Defines the interface for escaping text content and attribute values
    in a format-appropriate way (HTML5 vs XML).
    """

    @abstractmethod
    def quote_attribute(self, value: str) -> str:
        """Quote an attribute value appropriately for the target format.

        Args:
            value: The raw attribute value to quote

        Returns:
            The properly quoted and escaped attribute value
        """
        pass

    @abstractmethod
    def escape_text(self, text: str, element=None) -> str:
        """Escape text content appropriately for the target format.

        Args:
            text: The raw text content to escape
            element: Optional element containing the text (for context-aware escaping)

        Returns:
            The properly escaped text content
        """
        pass

    @abstractmethod
    def escape_comment_text(self, text: str) -> str:
        """Escape comment text appropriately for the target format.

        Args:
            text: The raw comment text to escape

        Returns:
            The properly escaped comment text
        """
        pass


class HtmlEscapingStrategy(EscapingStrategy):
    """HTML5-friendly escaping strategy.

    Uses HTML5-compatible escaping rules:
    - Allows literal newlines in attribute values for better readability
    - Standard XML entity escaping for text content (except in script/style tags)
    - Appropriate comment text handling
    - Preserves raw content in <script> and <style> tags per HTML5 spec

    This strategy produces more readable output for HTML5 documents,
    particularly for multiline CSS styles and other complex attribute values.

    Note: In HTML5, <script> and <style> elements use special parsing states
    (script data state, RAWTEXT state) where character references are NOT decoded.
    This means lxml's HTML parser preserves the literal text as-is, and we must
    NOT re-escape it during serialization to avoid double-encoding.
    """

    def quote_attribute(self, value: str) -> str:
        """Quote attribute value with HTML5-friendly newline handling.

        Uses literal newlines in attribute values, which are valid in HTML5
        and produce much more readable output for complex values like CSS styles.

        Args:
            value: The raw attribute value to quote

        Returns:
            Quoted attribute value with literal newlines preserved

        Example:
            >>> strategy = HtmlEscapingStrategy()
            >>> css = "color: red;\\nbackground: blue;"
            >>> strategy.quote_attribute(css)
            '"color: red;\\nbackground: blue;"'
        """
        return html_friendly_quoteattr(value)

    def escape_text(self, text: str, element=None) -> str:
        """Escape text content using standard XML entities.

        Special handling for HTML5 script/style tags: their content is NOT escaped
        because the HTML5 parser preserves the raw text (including any entity
        references like &gt;) as-is. Escaping would cause double-encoding.

        Args:
            text: The raw text content to escape
            element: Optional element containing the text (for context-aware escaping)

        Returns:
            Text with XML entities escaped (&, <, >), or raw text for script/style tags

        Example:
            >>> strategy = HtmlEscapingStrategy()
            >>> strategy.escape_text("x > 5")
            'x &gt; 5'
            >>> from lxml import etree
            >>> script = etree.Element("script")
            >>> strategy.escape_text("x &gt; 5", script)  # Already in raw form from HTML parser
            'x &gt; 5'
        """
        # HTML5 spec: script and style elements use special parsing states where
        # character references are NOT decoded. Content is preserved as-is by the parser.
        if element is not None and element.tag in ('script', 'style'):
            return text
        return escape(text)

    def escape_comment_text(self, text: str) -> str:
        """Escape comment text content.

        For HTML5 comments, we use the same escaping as regular text.

        Args:
            text: The raw comment text to escape

        Returns:
            Comment text with appropriate escaping
        """
        return escape(text)


class XmlEscapingStrategy(EscapingStrategy):
    """XML-strict escaping strategy.

    Uses XML-compliant escaping rules:
    - Escapes newlines in attribute values as &#10; entities
    - Standard XML entity escaping for text content
    - Strict XML comment handling

    This strategy ensures full XML compliance but may produce less readable
    output for complex attribute values containing newlines.
    """

    def quote_attribute(self, value: str) -> str:
        """Quote attribute value with XML-strict escaping.

        Uses xml.sax.saxutils.quoteattr which escapes newlines as &#10; entities
        to ensure strict XML compliance.

        Args:
            value: The raw attribute value to quote

        Returns:
            Quoted attribute value with newlines as &#10; entities

        Example:
            >>> strategy = XmlEscapingStrategy()
            >>> css = "color: red;\\nbackground: blue;"
            >>> strategy.quote_attribute(css)
            '"color: red;&#10;background: blue;"'
        """
        return quoteattr(value)

    def escape_text(self, text: str, element=None) -> str:
        """Escape text content using standard XML entities.

        Args:
            text: The raw text content to escape
            element: Optional element containing the text (unused in XML strategy)

        Returns:
            Text with XML entities escaped (&, <, >)
        """
        return escape(text)

    def escape_comment_text(self, text: str) -> str:
        """Escape comment text content for XML.

        Args:
            text: The raw comment text to escape

        Returns:
            Comment text with appropriate XML escaping
        """
        return escape(text)
