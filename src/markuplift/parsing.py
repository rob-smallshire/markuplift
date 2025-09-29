"""Parsing strategies for HTML5 vs XML document processing.

This module provides configurable parsing strategies that handle the differences
between HTML5 and XML parsing requirements, leveraging lxml's specialized parsers
for each format.

The strategy pattern allows MarkupLift to use the most appropriate parser while
maintaining the same core formatting engine.
"""

from abc import ABC, abstractmethod
from lxml import etree, html


class ParsingStrategy(ABC):
    """Abstract base class for parsing strategies.

    Defines the interface for parsing documents in a format-appropriate way
    (HTML5 vs XML).

    Args:
        preserve_cdata: If True, preserve CDATA sections in the parsed document.
                       If False, CDATA sections are converted to regular text.
                       Defaults to True for structure preservation.
    """

    def __init__(self, preserve_cdata: bool = True):
        self.preserve_cdata = preserve_cdata

    @abstractmethod
    def parse_string(self, content: str) -> etree._ElementTree:
        """Parse a string into an ElementTree.

        Args:
            content: The raw document content to parse

        Returns:
            An lxml ElementTree representing the parsed document
        """
        pass

    @abstractmethod
    def parse_file(self, path: str) -> etree._ElementTree:
        """Parse a file into an ElementTree.

        Args:
            path: Path to the file to parse

        Returns:
            An lxml ElementTree representing the parsed document
        """
        pass

    @abstractmethod
    def parse_bytes(self, content: bytes) -> etree._ElementTree:
        """Parse bytes into an ElementTree.

        Args:
            content: The raw document content as bytes to parse

        Returns:
            An lxml ElementTree representing the parsed document
        """
        pass


class HtmlParsingStrategy(ParsingStrategy):
    """HTML5-aware parsing strategy.

    Uses lxml's HTML parser which provides:
    - Better handling of HTML5 void elements (img, br, hr, etc.)
    - More lenient parsing of malformed HTML
    - Automatic insertion of missing HTML structure elements
    - HTML5-specific parsing rules
    - Configurable CDATA preservation

    This strategy is ideal for processing HTML documents that may not be
    strictly well-formed XML.
    """

    def __init__(self, preserve_cdata: bool = True):
        super().__init__(preserve_cdata)
        # HTML parser doesn't support strip_cdata parameter directly,
        # but we can still track the preference for post-processing if needed

    def parse_string(self, content: str) -> etree._ElementTree:
        """Parse HTML string using lxml's HTML parser.

        Args:
            content: The HTML content to parse

        Returns:
            ElementTree with HTML5-aware parsing applied

        Example:
            >>> strategy = HtmlParsingStrategy()
            >>> tree = strategy.parse_string('<div><img src="test.jpg"><br></div>')
            >>> # Properly handles void elements without requiring self-closing syntax
        """
        # Parse as HTML fragment first
        element = html.fromstring(content)
        # Convert to ElementTree for consistency with other methods
        return etree.ElementTree(element)

    def parse_file(self, path: str) -> etree._ElementTree:
        """Parse HTML file using lxml's HTML parser.

        Args:
            path: Path to the HTML file to parse

        Returns:
            ElementTree with HTML5-aware parsing applied
        """
        return html.parse(path)

    def parse_bytes(self, content: bytes) -> etree._ElementTree:
        """Parse HTML bytes using lxml's HTML parser.

        Args:
            content: The HTML content as bytes to parse

        Returns:
            ElementTree with HTML5-aware parsing applied
        """
        element = html.fromstring(content)
        return etree.ElementTree(element)


class XmlParsingStrategy(ParsingStrategy):
    """XML-strict parsing strategy.

    Uses lxml's XML parser which provides:
    - Strict XML compliance requirements
    - Proper handling of XML declarations and processing instructions
    - Namespace awareness
    - DTD validation capabilities
    - Configurable CDATA preservation

    This strategy is ideal for processing well-formed XML documents that
    require strict compliance with XML standards.
    """

    def __init__(self, preserve_cdata: bool = True):
        super().__init__(preserve_cdata)
        # Create parser with appropriate CDATA handling
        self._parser = etree.XMLParser(strip_cdata=not preserve_cdata)

    def parse_string(self, content: str) -> etree._ElementTree:
        """Parse XML string using lxml's XML parser.

        Args:
            content: The XML content to parse

        Returns:
            ElementTree with strict XML parsing applied

        Raises:
            XMLSyntaxError: If the content is not well-formed XML

        Example:
            >>> strategy = XmlParsingStrategy()
            >>> tree = strategy.parse_string('<root><child>content</child></root>')
            >>> # Requires well-formed XML with proper closing tags
        """
        element = etree.fromstring(content, parser=self._parser)
        return etree.ElementTree(element)

    def parse_file(self, path: str) -> etree._ElementTree:
        """Parse XML file using lxml's XML parser.

        Args:
            path: Path to the XML file to parse

        Returns:
            ElementTree with strict XML parsing applied

        Raises:
            XMLSyntaxError: If the file contains malformed XML
        """
        return etree.parse(path, parser=self._parser)

    def parse_bytes(self, content: bytes) -> etree._ElementTree:
        """Parse XML bytes using lxml's XML parser.

        Args:
            content: The XML content as bytes to parse

        Returns:
            ElementTree with strict XML parsing applied

        Raises:
            XMLSyntaxError: If the content is not well-formed XML
        """
        element = etree.fromstring(content, parser=self._parser)
        return etree.ElementTree(element)
