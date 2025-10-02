"""Source location utilities for finding elements in markup source.

This module provides tools for locating elements in HTML/XML source by tracking
their position in the tree structure and returning byte offsets.
"""

import xml.parsers.expat


class SimpleTagScanner:
    """XML/HTML tokenizer for locating elements in source bytes using expat.

    This scanner finds the byte range of elements by tracking tree structure
    (parent-child relationships via indices) while parsing through the source.
    It uses Python's expat parser which provides accurate byte position tracking.
    """

    def __init__(self, source: bytes):
        """Initialize scanner with source bytes.

        Args:
            source: The HTML/XML source as bytes to scan
        """
        self.source = source

    def find_element_range(self, target_path: list[int]) -> tuple[int, int] | None:
        """Find byte range of element at target_path.

        The target_path is a list of child indices from the root element,
        representing the path through the tree to reach the target element.

        For example, if scanning this document:
            <root>
                <first>...</first>
                <second>
                    <nested>...</nested>
                </second>
            </root>

        - [0] would be <root>
        - [0, 0] would be <first>
        - [0, 1] would be <second>
        - [0, 1, 0] would be <nested>

        Args:
            target_path: List of child indices from root, e.g., [0, 1, 1] for
                        root → second child → second child

        Returns:
            Tuple of (start_byte, end_byte) for the element, or None if not found.
            The byte range includes the opening and closing tags.
        """
        current_path: list[int] = []
        depth_child_counts = [0]

        target_start: int | None = None
        target_end: int | None = None

        # Create expat parser
        parser = xml.parsers.expat.ParserCreate()

        def start_element(name, attrs):
            nonlocal target_start

            # Get current byte position BEFORE updating path
            byte_pos = parser.CurrentByteIndex

            # Update path tracking
            depth_child_counts[-1] += 1
            child_index = depth_child_counts[-1] - 1
            current_path.append(child_index)
            depth_child_counts.append(0)

            # Check if this is the target element
            if current_path == target_path:
                target_start = byte_pos

        def end_element(name):
            nonlocal target_end

            # Check if we're ending the target element
            if current_path == target_path:
                # For regular closing tags: CurrentByteIndex points to START of </tag>
                # For self-closing tags: CurrentByteIndex points AFTER the />
                close_pos = parser.CurrentByteIndex

                # Disambiguate: check if there's a '</' at CurrentByteIndex
                # If yes, it's a regular closing tag; if no, it's self-closing
                if close_pos + 1 < len(self.source) and self.source[close_pos:close_pos+2] == b'</':
                    # Regular closing tag: search forward for '>'
                    close_tag_end = self.source.find(b'>', close_pos)
                    if close_tag_end != -1:
                        target_end = close_tag_end + 1
                else:
                    # Self-closing: CurrentByteIndex is already past />
                    target_end = close_pos

            # Pop from path tracking
            depth_child_counts.pop()
            if current_path:
                current_path.pop()

        # Set up handlers
        parser.StartElementHandler = start_element
        parser.EndElementHandler = end_element

        # Parse the source
        try:
            parser.Parse(self.source, True)
        except xml.parsers.expat.ExpatError:
            # If parsing fails, return None
            return None

        # Return the byte range if found
        if target_start is not None and target_end is not None:
            return (target_start, target_end)

        return None
