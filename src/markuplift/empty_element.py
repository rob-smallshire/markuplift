"""Empty element rendering strategies for XML and HTML5.

This module provides a strategy pattern for handling empty elements (elements
with no text content and no children) differently across document formats.

XML allows all empty elements to self-close with a trailing slash (<tag />),
while HTML5 has specific rules:
- Void elements (br, img, etc.) use a single tag with no slash (<tag>)
- Non-void empty elements must use explicit start and end tags (<tag></tag>)
"""

from abc import ABC, abstractmethod
from enum import Enum
from lxml import etree


class EmptyElementTagStyle(Enum):
    """How to render empty elements (no content, no children).

    This enum defines the three different ways empty elements can be rendered
    in markup languages, based on format-specific rules.
    """

    EXPLICIT_TAGS = "explicit"
    """Render with separate start and end tags: <tag></tag>

    Used for HTML5 non-void empty elements like <script>, <style>, <div>, etc.
    These elements can contain content semantically, so both tags are required
    even when empty.
    """

    SELF_CLOSING_TAG = "self_closing"
    """Render as self-closing with trailing slash: <tag />

    Used for XML where all empty elements can self-close. The trailing slash
    indicates no end tag is needed. Common in XML, XHTML, and SVG.
    """

    VOID_TAG = "void"
    """Render as single tag without trailing slash: <tag>

    Used for HTML5 void elements (br, img, hr, etc.) which cannot have content
    or children. These elements use only a start tag with no closing tag and
    no trailing slash in standard HTML5.
    """


class EmptyElementStrategy(ABC):
    """Abstract base class for empty element rendering strategies.

    Empty element strategies determine how elements with no text content and
    no children should be rendered in the output. Different document formats
    (XML, HTML5) have different rules and conventions for empty elements.

    Implementations must decide the tag style for each empty element based on
    format-specific rules (e.g., HTML5 void elements vs. non-void elements,
    XML self-closing conventions).
    """

    @abstractmethod
    def tag_style(self, element: etree._Element) -> EmptyElementTagStyle:
        """Determine how to render this empty element.

        This method is called only for elements that are truly empty (no text
        content after transformations and no child elements). The strategy
        decides which rendering style is appropriate.

        Args:
            element: The empty element to render. This is guaranteed to have
                    no text content and no children when this method is called.

        Returns:
            EmptyElementTagStyle indicating how to render the element:
            - EXPLICIT_TAGS: Use <tag></tag>
            - SELF_CLOSING_TAG: Use <tag />
            - VOID_TAG: Use <tag>

        Example:
            >>> strategy = Html5EmptyElementStrategy()
            >>> br_elem = etree.Element("br")
            >>> strategy.tag_style(br_elem)
            <EmptyElementTagStyle.VOID_TAG: 'void'>

            >>> script_elem = etree.Element("script")
            >>> strategy.tag_style(script_elem)
            <EmptyElementTagStyle.EXPLICIT_TAGS: 'explicit'>
        """
        pass


class XmlEmptyElementStrategy(EmptyElementStrategy):
    """XML empty element strategy: all empty elements self-close with slash.

    In XML, any element without content can be represented as a self-closing
    tag using the trailing slash syntax: <tag />. This is valid for all
    elements and is a common XML convention.

    This strategy is appropriate for:
    - Pure XML documents
    - XHTML (XML-compliant HTML)
    - SVG and MathML when used standalone
    - Custom XML vocabularies

    Example:
        >>> strategy = XmlEmptyElementStrategy()
        >>> elem = etree.Element("custom")
        >>> strategy.tag_style(elem)
        <EmptyElementTagStyle.SELF_CLOSING_TAG: 'self_closing'>
    """

    def tag_style(self, element: etree._Element) -> EmptyElementTagStyle:
        """Return SELF_CLOSING_TAG for all empty elements.

        All empty elements in XML can and should use self-closing syntax
        for brevity and clarity.

        Args:
            element: The empty element (unused, all elements treated the same)

        Returns:
            Always returns EmptyElementTagStyle.SELF_CLOSING_TAG
        """
        return EmptyElementTagStyle.SELF_CLOSING_TAG


class Html5EmptyElementStrategy(EmptyElementStrategy):
    """HTML5 empty element strategy: void elements vs. non-void elements.

    HTML5 has strict rules for empty elements based on whether they are
    "void elements" (elements that cannot have content or children):

    - Void elements (13 total): Use single tag without slash
      Examples: <br>, <img src="x">, <hr>

    - Non-void empty elements: Use explicit start and end tags
      Examples: <script></script>, <style></style>, <div></div>

    The void element list is defined by the HTML5 specification and cannot
    be extended. Using self-closing syntax on non-void elements (e.g., <div />)
    is invalid HTML5 and will cause parsing errors in browsers.

    Reference: https://html.spec.whatwg.org/multipage/syntax.html#void-elements

    Example:
        >>> strategy = Html5EmptyElementStrategy()
        >>> br = etree.Element("br")
        >>> strategy.tag_style(br)
        <EmptyElementTagStyle.VOID_TAG: 'void'>

        >>> script = etree.Element("script")
        >>> strategy.tag_style(script)
        <EmptyElementTagStyle.EXPLICIT_TAGS: 'explicit'>
    """

    # HTML5 void elements as defined by WHATWG spec (2025)
    # These are the ONLY elements in HTML5 that can use single-tag syntax
    _HTML5_VOID_ELEMENTS = frozenset({
        "area",   # Image map area
        "base",   # Document base URL
        "br",     # Line break
        "col",    # Table column
        "embed",  # External content embedding
        "hr",     # Thematic break (horizontal rule)
        "img",    # Image
        "input",  # Form input
        "link",   # External resource link
        "meta",   # Metadata
        "source", # Media source
        "track",  # Text track
        "wbr",    # Word break opportunity
    })

    def tag_style(self, element: etree._Element) -> EmptyElementTagStyle:
        """Determine tag style based on HTML5 void element rules.

        Returns VOID_TAG for HTML5 void elements (renders as <tag>),
        and EXPLICIT_TAGS for all other elements (renders as <tag></tag>).

        Args:
            element: The empty element to check

        Returns:
            - VOID_TAG if element is an HTML5 void element
            - EXPLICIT_TAGS for all other elements
        """
        if element.tag in self._HTML5_VOID_ELEMENTS:
            return EmptyElementTagStyle.VOID_TAG
        else:
            return EmptyElementTagStyle.EXPLICIT_TAGS
