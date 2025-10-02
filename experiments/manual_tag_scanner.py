#!/usr/bin/env python3
"""
Prototype: Manual HTML tag scanner to locate subtree byte ranges.

Since lxml's SAX parser buffers input and doesn't provide byte positions,
we need a manual scanner that:
1. Finds tags in the source string
2. Tracks the tree path (child indices) as it scans
3. Records byte positions when we match the target path

This scanner only needs to:
- Recognize <tag>, </tag>, and <tag/> patterns
- Track nesting depth and child indices
- Handle comments, CDATA, processing instructions (skip them)
- Not worry about parsing attributes in detail
"""

import re
from lxml import etree, html


class SimpleTagScanner:
    """
    Scans HTML/XML source to find byte ranges of elements.

    This is a minimal scanner that tracks tree structure without full parsing.
    It handles the edge cases that make regex unreliable (comments, PI, CDATA, etc.)
    but doesn't attempt full attribute parsing.
    """

    # Pattern to find next tag-like construct
    # Matches: <tag>, </tag>, <tag/>, <!--comment-->, <![CDATA[...]]>, <?pi?>
    TAG_PATTERN = re.compile(
        r'<(?:'
        r'!--.*?--|'  # Comment
        r'!\[CDATA\[.*?\]\]|'  # CDATA
        r'\?.*?\?|'  # Processing instruction
        r'(/?)([a-zA-Z][a-zA-Z0-9:-]*)'  # Opening or closing tag (capture / and tag name)
        r'(?:\s[^>]*)?'  # Attributes (skip for now)
        r'(/?)>'  # Self-closing or regular close
        r')',
        re.DOTALL
    )

    def __init__(self, source: str):
        self.source = source
        self.position = 0

    def find_element_range(self, target_path: list[int], debug: bool = False) -> tuple[int, int] | None:
        """
        Find byte range of element at target_path.

        Args:
            target_path: List of child indices from root, e.g., [0, 1, 1] for
                        root → first child → second child → second child
            debug: Print debug info about scanning

        Returns:
            (start_offset, end_offset) tuple, or None if not found
        """
        current_path = []
        depth_child_counts = [0]
        depth_start_positions = []  # Stack of start positions for each depth

        target_start = None
        target_end = None
        target_depth = len(target_path)

        if debug:
            print(f"  Scanning for path: {target_path}")

        for match in self.TAG_PATTERN.finditer(self.source):
            tag_start = match.start()
            tag_text = match.group(0)

            # Skip comments, CDATA, PIs
            if tag_text.startswith('<!--') or tag_text.startswith('<![CDATA[') or tag_text.startswith('<?'):
                continue

            # Extract tag info
            is_closing = match.group(1) == '/'  # Opening tag has / before name
            tag_name = match.group(2)
            is_self_closing = match.group(3) == '/' or not tag_name  # <tag/> or no tag name

            if is_closing:
                # Closing tag: </tag>
                if debug and current_path == target_path:
                    print(f"    Found end tag for target: </{tag_name}> at {match.end()}")

                # Check if we're ending the target element
                if current_path == target_path:
                    target_end = match.end()
                    # Found both start and end!
                    return (target_start, target_end)

                # Pop from path tracking
                depth_child_counts.pop()
                depth_start_positions.pop()
                if current_path:
                    current_path.pop()

            elif is_self_closing:
                # Self-closing tag: <tag/>
                # Treat as both start and end
                depth_child_counts[-1] += 1
                child_index = depth_child_counts[-1] - 1
                test_path = current_path + [child_index]

                if debug:
                    print(f"    Self-closing: <{tag_name}/> at path {test_path}")

                # Check if this IS the target (edge case: target is self-closing)
                if test_path == target_path:
                    return (tag_start, match.end())

                # Don't add to path since it doesn't have children

            else:
                # Opening tag: <tag>
                depth_child_counts[-1] += 1
                child_index = depth_child_counts[-1] - 1
                current_path.append(child_index)
                depth_child_counts.append(0)
                depth_start_positions.append(tag_start)

                if debug:
                    marker = "  *** TARGET ***" if current_path == target_path else ""
                    print(f"    Open: <{tag_name}> at path {current_path}{marker}")

                # Check if we found the target's start
                if current_path == target_path:
                    target_start = tag_start

        return None


def test_scanner():
    """Test the scanner with HTML containing SVG."""
    html_source = """<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <p>Before SVG</p>
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <text x="10" y="20">Text content</text>
        <textPath href="#path">Path text</textPath>
    </svg>
    <p>After SVG</p>
</body>
</html>"""

    print("=== Testing Manual Tag Scanner ===\n")

    # First, parse with HTML parser to find SVG and get its path
    tree = html.fromstring(html_source)

    # Manually determine path to SVG
    # In HTML parser: tree root is <html>
    # We need to walk tree and record path

    def get_element_path(root, target_elem):
        """Get path from root to target element."""
        def walk(elem, path):
            if elem is target_elem:
                return path
            for i, child in enumerate(elem):
                result = walk(child, path + [i])
                if result is not None:
                    return result
            return None
        return walk(root, [])

    svg_elem = tree.find('.//svg')
    target_path = get_element_path(tree, svg_elem)

    print(f"SVG element found in tree")
    print(f"Path from tree root (html element): {target_path}")
    print(f"Source line: {svg_elem.sourceline}")
    print()

    # The scanner scans from the start of the SOURCE, so it sees DOCTYPE, then <html>
    # So we need to adjust path to account for <html> being at [0] in the scanner's view
    scanner_path = [0] + target_path if target_path else [0]
    print(f"Adjusted path for scanner (from source start): {scanner_path}")
    print()

    # Now use scanner to find byte range
    scanner = SimpleTagScanner(html_source)
    byte_range = scanner.find_element_range(scanner_path, debug=True)

    if byte_range:
        start, end = byte_range
        print(f"✓ Scanner found SVG at byte range: {start} to {end}")
        print(f"  Length: {end - start} bytes")
        print()

        # Extract the range
        extracted = html_source[start:end]
        print("Extracted content:")
        print(extracted)
        print()

        # Try to parse as XML
        print("Attempting to parse extracted content as XML...")
        try:
            xml_tree = etree.fromstring(extracted.encode())
            print("✓ Successfully parsed as XML!")
            print(f"  Root tag: {xml_tree.tag}")

            # Check for case-preserved elements
            textpath = xml_tree.find('.//{http://www.w3.org/2000/svg}textPath')
            if textpath is not None:
                print("  ✓ Found <textPath> with correct case!")
            else:
                # Try lowercase
                textpath_lower = xml_tree.find('.//{http://www.w3.org/2000/svg}textpath')
                if textpath_lower is not None:
                    print("  ✗ Found <textpath> (lowercase) - case not preserved")
                else:
                    print("  ? textPath element not found")

        except Exception as e:
            print(f"✗ Failed to parse as XML: {e}")

    else:
        print("✗ Scanner failed to find SVG")


def test_scanner_with_multiple_svg():
    """Test with multiple SVG elements."""
    html_source = """<!DOCTYPE html>
<html>
<body>
    <!-- First SVG -->
    <svg xmlns="http://www.w3.org/2000/svg">
        <textPath>First</textPath>
    </svg>
    <p>Between SVGs</p>
    <!-- Second SVG -->
    <svg xmlns="http://www.w3.org/2000/svg">
        <textPath>Second</textPath>
    </svg>
</body>
</html>"""

    print("\n=== Testing with Multiple SVG Elements ===\n")

    tree = html.fromstring(html_source)

    def get_element_path(root, target_elem):
        def walk(elem, path):
            if elem is target_elem:
                return path
            for i, child in enumerate(elem):
                result = walk(child, path + [i])
                if result is not None:
                    return result
            return None
        return walk(root, [])

    # Find both SVG elements
    svg_elements = tree.findall('.//svg')
    print(f"Found {len(svg_elements)} SVG elements\n")

    scanner = SimpleTagScanner(html_source)

    for i, svg_elem in enumerate(svg_elements):
        path = get_element_path(tree, svg_elem)
        print(f"SVG #{i+1} at path {path}")

        byte_range = scanner.find_element_range(path)
        if byte_range:
            start, end = byte_range
            extracted = html_source[start:end]
            print(f"  Range: {start}-{end}")
            print(f"  Content: {extracted[:60]}...")
        else:
            print(f"  ✗ Not found")
        print()


def test_scanner_edge_cases():
    """Test scanner with edge cases."""
    test_cases = [
        (
            "Self-closing SVG",
            '<html><body><svg xmlns="http://www.w3.org/2000/svg"/></body></html>',
            [0, 0]  # body → svg
        ),
        (
            "SVG with comment inside",
            '<html><body><svg><!-- comment --><text>content</text></svg></body></html>',
            [0, 0]  # body → svg
        ),
        (
            "Attributes with > character",
            '<html><body><div data-expr="x > y"><span>content</span></div></body></html>',
            [0, 0, 0]  # body → div → span
        ),
    ]

    print("\n=== Testing Edge Cases ===\n")

    for name, source, target_path in test_cases:
        print(f"{name}:")
        scanner = SimpleTagScanner(source)
        byte_range = scanner.find_element_range(target_path)

        if byte_range:
            start, end = byte_range
            extracted = source[start:end]
            print(f"  ✓ Found at {start}-{end}")
            print(f"  Content: {extracted}")
        else:
            print(f"  ✗ Not found")
        print()


if __name__ == "__main__":
    test_scanner()
    test_scanner_with_multiple_svg()
    test_scanner_edge_cases()
