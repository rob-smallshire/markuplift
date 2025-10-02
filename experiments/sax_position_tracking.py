#!/usr/bin/env python3
"""
Prototype: Can we use lxml's SAX parser to track byte positions and extract subtrees?

Goal: Determine if we can locate the byte range of an SVG element in HTML source
using SAX parsing, then extract that range for re-parsing as XML.

This will test whether SAX parsing provides enough position information to make
the hybrid HTML/XML parsing approach viable.
"""

from io import BytesIO
from lxml import etree, html
import xml.sax


class PositionTrackingSAXHandler(xml.sax.ContentHandler):
    """SAX handler that tracks element paths and attempts to capture positions."""

    def __init__(self, target_path: list[int]):
        super().__init__()
        self.target_path = target_path
        self.current_path = []
        self.depth_child_counts = [0]  # Track child count at each depth
        self.start_offset = None
        self.end_offset = None
        self.in_target = False
        self.target_depth = None

    def startElement(self, name, attrs):
        # Update child count at current depth
        if self.depth_child_counts:
            self.depth_child_counts[-1] += 1
            child_index = self.depth_child_counts[-1] - 1
            self.current_path.append(child_index)

        # Check if we've reached target element
        if self.current_path == self.target_path:
            self.in_target = True
            self.target_depth = len(self.current_path)
            print(f"✓ Found target element: <{name}> at path {self.current_path}")

            # Try to get position from locator
            if hasattr(self, '_locator') and self._locator:
                print(f"  Locator available:")
                print(f"    Line: {self._locator.getLineNumber()}")
                print(f"    Column: {self._locator.getColumnNumber()}")
                # Note: SAX locator doesn't provide byte offset directly

        # Prepare for tracking children of this element
        self.depth_child_counts.append(0)

    def endElement(self, name):
        # Check if we're ending the target element
        if self.in_target and len(self.current_path) == self.target_depth:
            print(f"✓ End of target element: </{name}>")
            if hasattr(self, '_locator') and self._locator:
                print(f"  Line: {self._locator.getLineNumber()}")
                print(f"  Column: {self._locator.getColumnNumber()}")
            self.in_target = False

        # Pop from path tracking
        self.depth_child_counts.pop()
        if self.current_path:
            self.current_path.pop()

    def setDocumentLocator(self, locator):
        """Called by parser to provide a locator object."""
        self._locator = locator
        print(f"✓ Document locator set: {locator}")
        print(f"  Locator type: {type(locator)}")


def test_sax_with_html_parser():
    """Test if lxml's HTML→SAX conversion provides position info."""
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

    print("=== Test 1: SAX with HTML Parser ===\n")

    # Parse HTML to get tree
    tree = html.fromstring(html_source)

    # Find SVG element and its path
    svg_elem = tree.find('.//svg')

    # Calculate path to SVG: html → body → svg (2nd child of body, after <p>)
    # In HTML parser: root is <html>
    # Path: [0] (body, first child of html) → [1] (svg, second child of body)
    target_path = [1, 1]  # body is child 1 of html, svg is child 1 of body

    print(f"Target path to SVG: {target_path}")
    print(f"SVG element found: {svg_elem.tag}")
    print()

    # Try to generate SAX events and track position
    handler = PositionTrackingSAXHandler(target_path)

    # lxml provides saxify to generate SAX events from tree
    try:
        from lxml.sax import saxify
        print("Converting ElementTree to SAX events...")
        saxify(tree, handler)
    except Exception as e:
        print(f"✗ Error: {e}")

    print()


def test_iterparse_position_tracking():
    """Test if iterparse with events can help track positions."""
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

    print("=== Test 2: iterparse with Position Tracking ===\n")

    # Use HTML parser for iterparse
    parser = etree.HTMLParser()

    # Track path through tree
    current_path = []
    depth_child_counts = [0]
    target_path = [1, 1]  # Path to SVG element

    events = ('start', 'end')
    context = etree.iterparse(
        BytesIO(html_source.encode()),
        events=events,
        html=True
    )

    print(f"Target path to SVG: {target_path}\n")

    for event, elem in context:
        if event == 'start':
            # Update child count and path
            depth_child_counts[-1] += 1
            child_index = depth_child_counts[-1] - 1
            current_path.append(child_index)
            depth_child_counts.append(0)

            # Check if we found target
            if current_path == target_path:
                print(f"✓ Found target via iterparse: <{elem.tag}>")
                print(f"  Path: {current_path}")
                print(f"  Source line: {elem.sourceline}")
                print(f"  Attributes: {dict(elem.attrib)}")

        elif event == 'end':
            # Pop from path
            depth_child_counts.pop()
            if current_path:
                current_path.pop()

    print()


def test_manual_streaming_parser():
    """Test a custom streaming approach that tracks byte position manually."""
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

    print("=== Test 3: Manual Streaming Parser with Byte Tracking ===\n")

    class BytePositionTracker:
        """Wraps bytes and tracks position."""
        def __init__(self, data: bytes):
            self.data = data
            self.position = 0

        def read(self, size=-1):
            if size == -1:
                result = self.data[self.position:]
                self.position = len(self.data)
            else:
                result = self.data[self.position:self.position + size]
                self.position += len(result)
            return result

    class PositionTrackingTarget:
        """Parser target that tracks positions."""
        def __init__(self, target_path: list[int], tracker: BytePositionTracker):
            self.target_path = target_path
            self.tracker = tracker
            self.current_path = []
            self.depth_child_counts = [0]
            self.found = False
            self.start_pos = None
            self.end_pos = None
            self.callback_count = 0

        def start(self, tag, attrib):
            self.callback_count += 1
            # Track position BEFORE parser processes
            current_pos = self.tracker.position

            # Update path
            self.depth_child_counts[-1] += 1
            child_index = self.depth_child_counts[-1] - 1
            self.current_path.append(child_index)
            self.depth_child_counts.append(0)

            print(f"  start: <{tag}> at path {self.current_path}, byte pos {current_pos}")

            # Check for target
            if self.current_path == self.target_path:
                self.found = True
                self.start_pos = current_pos
                print(f"  ✓ FOUND TARGET at byte position: {current_pos}")

        def end(self, tag):
            self.callback_count += 1
            # Track position at end
            current_pos = self.tracker.position

            print(f"  end: </{tag}> at path {self.current_path}, byte pos {current_pos}")

            # Check if ending target
            if self.found and len(self.current_path) == len(self.target_path):
                self.end_pos = current_pos
                print(f"  ✓ TARGET ENDED at byte position: {current_pos}")
                self.found = False

            # Update path
            self.depth_child_counts.pop()
            if self.current_path:
                self.current_path.pop()

        def data(self, data):
            pass  # Ignore text content

        def comment(self, text):
            pass

        def close(self):
            print(f"\n  Parser target close() called. Total callbacks: {self.callback_count}")
            return "done"

    # Create tracker and target
    tracker = BytePositionTracker(html_source.encode())
    target_path = [1, 1]  # Path to SVG
    target = PositionTrackingTarget(target_path, tracker)

    # Create parser with target
    parser = etree.HTMLParser(target=target)

    print(f"Target path to SVG: {target_path}\n")
    print("Parsing with position tracking...\n")

    # Parse with our tracking wrapper
    result = etree.parse(tracker, parser)

    # Check results
    if target.start_pos is not None and target.end_pos is not None:
        print(f"\n✓ Successfully tracked byte range!")
        print(f"  Start: {target.start_pos}")
        print(f"  End: {target.end_pos}")
        print(f"  Length: {target.end_pos - target.start_pos} bytes")

        # Try to extract the range
        extracted = html_source.encode()[target.start_pos:target.end_pos]
        print(f"\n  Extracted content:")
        print(f"  {extracted.decode()[:100]}...")
    else:
        print("\n✗ Failed to track byte range")

    print()


if __name__ == "__main__":
    test_sax_with_html_parser()
    test_iterparse_position_tracking()
    test_manual_streaming_parser()

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("""
The key question: Can we track byte positions during SAX/streaming parsing?

Approaches tested:
1. SAX events from tree (saxify) - No position info available
2. iterparse with events - Gives line numbers but not byte offsets
3. Custom parser target with wrapper - This should work if parser reads
   sequentially from our wrapper, but lxml may buffer internally

Next steps:
- Verify if the custom wrapper approach actually tracks positions correctly
- If not, fall back to manual tag scanning of source string
- Consider whether line/column from iterparse + manual offset calculation works
""")
