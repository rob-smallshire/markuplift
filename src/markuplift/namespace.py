"""XML Namespace handling utilities.

This module provides utilities for working with XML namespaces in lxml,
including converting between Clark notation and prefix:localname format,
detecting namespace declarations, and formatting xmlns attributes.

Key concepts:
    - Clark notation: {namespace_uri}localname format used internally by lxml
    - nsmap: Dictionary mapping namespace prefixes to URIs (None = default namespace)
    - QName: lxml's qualified name value object
    - xml namespace: Special built-in namespace that never needs declaration

Examples:
    Converting tags to serialized form:
        format_tag_name(svg_element) → "svg" (default namespace)
        format_tag_name(grid_element) → "bx:grid" (prefixed namespace)

    Detecting new namespace declarations:
        get_new_namespace_declarations(root) → {None: "http://...", "bx": "http://..."}
        get_new_namespace_declarations(child) → {} (inherits from parent)

    Working with QName objects:
        qname = QName("http://www.w3.org/2000/svg", "rect")
        qname_to_str(qname) → "{http://www.w3.org/2000/svg}rect"
"""

from lxml import etree

# The built-in XML namespace (used for xml:space, xml:lang, etc.)
# This namespace is implicitly available and never needs xmlns:xml declaration
XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"


def qname_to_str(tag: str | etree.QName) -> str:
    """Convert tag name to string, handling both str and QName inputs.

    This utility function provides a consistent way to convert tag names from
    either string or QName format to string format. QName objects are converted
    to their Clark notation representation.

    Args:
        tag: Tag name as string (possibly Clark notation) or QName object

    Returns:
        str: Tag name in Clark notation if namespaced, localname otherwise

    Examples:
        >>> qname_to_str("div")
        "div"

        >>> qname_to_str("{http://www.w3.org/2000/svg}svg")
        "{http://www.w3.org/2000/svg}svg"

        >>> qname = etree.QName("http://www.w3.org/2000/svg", "svg")
        >>> qname_to_str(qname)
        "{http://www.w3.org/2000/svg}svg"

        >>> qname = etree.QName(element)
        >>> qname_to_str(qname)
        "{http://www.w3.org/2000/svg}rect"
    """
    return tag.text if isinstance(tag, etree.QName) else tag


def get_new_namespace_declarations(elem: etree._Element) -> dict[str | None, str]:
    """Get xmlns declarations that are NEW or CHANGED on this element.

    Compares the element's nsmap with its parent's nsmap to determine which
    namespace declarations need to be emitted on this element's opening tag.
    This ensures xmlns attributes are only added where needed.

    Args:
        elem: lxml Element to check for new namespace declarations

    Returns:
        dict: Mapping of {prefix: namespace_uri} for declarations to emit.
              prefix=None indicates default namespace (xmlns="...")
              Empty dict if no new declarations are needed.

    Examples:
        Root element (no parent):
            >>> get_new_namespace_declarations(root_elem)
            {None: 'http://www.w3.org/2000/svg', 'xlink': 'http://www.w3.org/1999/xlink'}

        Child with same nsmap as parent:
            >>> get_new_namespace_declarations(child_elem)
            {}

        Child introducing new namespace:
            >>> get_new_namespace_declarations(svg_in_html)
            {None: 'http://www.w3.org/2000/svg'}

        Child changing default namespace:
            >>> get_new_namespace_declarations(div_elem)
            {None: ''}  # Removes default namespace with xmlns=""
    """
    parent = elem.getparent()
    if parent is None:
        # Root element - all namespaces in nsmap are new
        return dict(elem.nsmap)

    parent_nsmap = parent.nsmap
    new_declarations = {}

    # Find namespace declarations that are new or changed
    for prefix, ns_uri in elem.nsmap.items():
        if prefix not in parent_nsmap or parent_nsmap[prefix] != ns_uri:
            new_declarations[prefix] = ns_uri

    return new_declarations


def format_tag_name(elem: etree._Element) -> str:
    """Convert element tag from Clark notation to prefix:localname format.

    Converts lxml's internal Clark notation format to the serialized XML format
    with namespace prefixes. Handles default namespaces, prefixed namespaces,
    elements without namespaces, and the special xml namespace.

    Args:
        elem: lxml Element whose tag should be formatted

    Returns:
        str: Formatted tag name suitable for XML serialization

    Examples:
        Element in default namespace:
            >>> format_tag_name(svg_element)  # elem.tag = "{http://www.w3.org/2000/svg}svg"
            "svg"

        Element with namespace prefix:
            >>> format_tag_name(grid_element)  # elem.tag = "{https://boxy-svg.com}grid"
            "bx:grid"

        Element without namespace:
            >>> format_tag_name(div_element)  # elem.tag = "div"
            "div"

        Element using xml namespace:
            >>> format_tag_name(text_element)  # Not typical - xml namespace is for attributes
            "text"

    Notes:
        - Default namespace (nsmap[None]) elements are rendered without prefix
        - xml namespace attributes use "xml:" prefix (handled by format_attribute_name)
        - Falls back to localname if namespace not found in nsmap (shouldn't happen
          in well-formed documents)
    """
    tag = elem.tag

    # Handle special node types (comments, processing instructions)
    # These have tag = <built-in function> rather than string
    if not isinstance(tag, str):
        return str(tag)

    qname = etree.QName(tag)

    # No namespace - return localname as-is
    if qname.namespace is None:
        return qname.localname

    # Special case: xml namespace (always uses "xml" prefix)
    # Note: This is rarely used for element tags, more common for attributes
    if qname.namespace == XML_NAMESPACE:
        return f"xml:{qname.localname}"

    # Look up prefix for this namespace in element's nsmap
    for prefix, ns_uri in elem.nsmap.items():
        if ns_uri == qname.namespace:
            if prefix is None:
                # Default namespace - no prefix needed
                return qname.localname
            else:
                # Prefixed namespace
                return f"{prefix}:{qname.localname}"

    # Namespace not found in nsmap - shouldn't happen in well-formed documents
    # Fall back to localname only
    return qname.localname


def format_attribute_name(elem: etree._Element, attr_name: str) -> str:
    """Convert attribute name from Clark notation to prefix:localname format.

    Converts attribute names from lxml's internal Clark notation to the serialized
    XML format with namespace prefixes. Most attributes have no namespace, but some
    (like xlink:href, xml:space) do.

    Args:
        elem: lxml Element (needed to look up namespace prefixes in elem.nsmap)
        attr_name: Attribute name, possibly in Clark notation

    Returns:
        str: Formatted attribute name suitable for XML serialization

    Examples:
        Regular attribute (no namespace):
            >>> format_attribute_name(elem, "width")
            "width"

        Namespaced attribute:
            >>> format_attribute_name(elem, "{http://www.w3.org/1999/xlink}href")
            "xlink:href"

        xml namespace attribute:
            >>> format_attribute_name(elem, "{http://www.w3.org/XML/1998/namespace}space")
            "xml:space"

    Notes:
        - Most attributes have no namespace (namespace=None in QName)
        - xml namespace always uses "xml:" prefix and never needs declaration
        - xmlns declarations are returned as-is (not regular attributes)
        - HTML parsing preserves literal prefix:localname format (e.g., "xlink:href")
        - Falls back to localname if namespace not found in nsmap
    """
    # Special case: xmlns declarations are not regular attributes
    # They should be returned as-is and not processed through QName
    if attr_name == "xmlns" or attr_name.startswith("xmlns:"):
        return attr_name

    # Special case: HTML parsing preserves literal "prefix:localname" format
    # These are not in Clark notation and cannot be converted to QName
    # Return them as-is (they're already in the correct output format)
    if ":" in attr_name and not attr_name.startswith("{"):
        return attr_name

    qname = etree.QName(attr_name)

    # No namespace - return localname as-is (most common case)
    if qname.namespace is None:
        return qname.localname

    # Special case: xml namespace (always uses "xml" prefix, never declared)
    if qname.namespace == XML_NAMESPACE:
        return f"xml:{qname.localname}"

    # Look up prefix for this namespace in element's nsmap
    for prefix, ns_uri in elem.nsmap.items():
        if ns_uri == qname.namespace:
            if prefix is None:
                # Attribute in default namespace (rare)
                return qname.localname
            else:
                # Prefixed namespace attribute
                return f"{prefix}:{qname.localname}"

    # Namespace not found - fall back to localname
    return qname.localname


def format_xmlns_declarations(declarations: dict[str | None, str]) -> list[str]:
    """Format namespace declarations as xmlns attribute strings.

    Converts a dictionary of namespace declarations into properly formatted
    xmlns attributes ready for XML serialization. Handles both default namespaces
    (xmlns="...") and prefixed namespaces (xmlns:prefix="...").

    Args:
        declarations: Mapping of {prefix: namespace_uri} where prefix can be None

    Returns:
        list[str]: Formatted xmlns attributes, sorted with default namespace first,
                   then alphabetically by prefix

    Examples:
        Default namespace only:
            >>> format_xmlns_declarations({None: "http://www.w3.org/2000/svg"})
            ['xmlns="http://www.w3.org/2000/svg"']

        Prefixed namespace:
            >>> format_xmlns_declarations({"xlink": "http://www.w3.org/1999/xlink"})
            ['xmlns:xlink="http://www.w3.org/1999/xlink"']

        Mixed default and prefixed:
            >>> format_xmlns_declarations({
            ...     None: "http://www.w3.org/2000/svg",
            ...     "bx": "https://boxy-svg.com",
            ...     "xlink": "http://www.w3.org/1999/xlink"
            ... })
            [
                'xmlns="http://www.w3.org/2000/svg"',
                'xmlns:bx="https://boxy-svg.com"',
                'xmlns:xlink="http://www.w3.org/1999/xlink"'
            ]

        Removing default namespace:
            >>> format_xmlns_declarations({None: ""})
            ['xmlns=""']

    Notes:
        - Default namespace (prefix=None) is always formatted first
        - Prefixed namespaces are sorted alphabetically for consistency
        - Empty string namespace URI is valid (removes default namespace)
    """
    formatted = []

    # Sort declarations: default namespace (None) first, then alphabetically by prefix
    # The key function: (is_not_none, prefix_or_empty_string)
    # This ensures None sorts before any string prefix
    sorted_decls = sorted(
        declarations.items(),
        key=lambda x: (x[0] is not None, x[0] or '')
    )

    for prefix, ns_uri in sorted_decls:
        if prefix is None:
            # Default namespace
            formatted.append(f'xmlns="{ns_uri}"')
        else:
            # Prefixed namespace
            formatted.append(f'xmlns:{prefix}="{ns_uri}"')

    return formatted
