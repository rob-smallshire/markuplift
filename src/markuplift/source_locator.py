"""Source location utilities for finding elements in markup source.

This module provides tools for locating elements in HTML/XML source by tracking
their position in the tree structure and returning byte offsets.
"""

import xml.parsers.expat


class XmlTagScanner:
    """XML tokenizer for locating elements in source bytes using expat.

    This scanner finds the byte range of elements by tracking tree structure
    (parent-child relationships via indices) while parsing through the source.
    It uses Python's expat parser which provides accurate byte position tracking.

    Note: This only works for valid XML. For HTML5 syntax (void elements without
    self-closing slashes, etc.), use Html5TagScanner instead.
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


class Html5TagScanner:
    """HTML5 tokenizer for locating elements in source bytes using html5lib.

    This scanner finds the byte range of elements by tracking tree structure
    (parent-child relationships via indices) while parsing through the source.
    It uses html5lib which correctly handles HTML5 syntax including void elements
    without self-closing slashes.

    This provides the same interface as XmlTagScanner for compatibility.
    """

    def __init__(self, source: bytes):
        """Initialize scanner with source bytes.

        Args:
            source: The HTML5 source as bytes to scan
        """
        self.source = source

    def find_element_range(self, target_path: list[int]) -> tuple[int, int] | None:
        """Find byte range of element at target_path.

        The target_path is a list of child indices from the root element,
        representing the path through the tree to reach the target element.

        Args:
            target_path: List of child indices from root, e.g., [0, 1, 1] for
                        root → second child → second child

        Returns:
            Tuple of (start_byte, end_byte) for the element, or None if not found.
            The byte range includes the opening and closing tags.
        """
        try:
            from html5lib._tokenizer import HTMLTokenizer  # type: ignore[import-untyped]
            from html5lib.constants import voidElements  # type: ignore[import-untyped]
        except ImportError:
            # html5lib not available, can't scan HTML5
            return None

        # Track path through the tree
        current_path: list[int] = []
        depth_child_counts = [0]

        target_start: int | None = None
        target_end: int | None = None
        target_name: str | None = None

        # Create tokenizer
        tokenizer = HTMLTokenizer(self.source)

        try:
            for token in tokenizer:
                token_type = token.get('type')
                token_name = token.get('name')

                # Type 3 = StartTag
                if token_type == 3:
                    self_closing = token.get('selfClosing', False)

                    # Update path tracking
                    depth_child_counts[-1] += 1
                    child_index = depth_child_counts[-1] - 1
                    current_path.append(child_index)
                    depth_child_counts.append(0)

                    # Check if this is the target element
                    if current_path == target_path:
                        # Get position (line, col) and convert to byte offset
                        line, col = tokenizer.stream.position()
                        # Position is AFTER the tag, we need to go back to find the start
                        target_start = self._find_tag_start_before(line, col, token_name)
                        target_name = token_name

                        # For void/self-closing elements, we've already reached the end
                        if token_name in voidElements or self_closing:
                            target_end = self._line_col_to_byte_offset(line, col)

                    # For void/self-closing elements, immediately pop since there's no EndTag
                    if token_name in voidElements or self_closing:
                        depth_child_counts.pop()
                        if current_path:
                            current_path.pop()

                # Type 4 = EndTag
                elif token_type == 4:
                    # Check if we're ending the target element
                    if current_path == target_path and token_name == target_name:
                        # Get position after the closing tag
                        line, col = tokenizer.stream.position()
                        target_end = self._line_col_to_byte_offset(line, col)

                    # Pop from path tracking
                    depth_child_counts.pop()
                    if current_path:
                        current_path.pop()

        except Exception:
            # If tokenization fails, return None
            return None

        # Return the byte range if found
        if target_start is not None and target_end is not None:
            return (target_start, target_end)

        return None

    def _line_col_to_byte_offset(self, line: int, col: int) -> int:
        """Convert (line, col) to byte offset.

        html5lib uses 1-indexed lines and 0-indexed columns.

        Args:
            line: Line number (1-indexed)
            col: Column number (0-indexed)

        Returns:
            Byte offset in the source
        """
        lines = self.source.split(b'\n')
        offset = 0

        # Sum lengths of all previous lines (including newlines)
        for i in range(line - 1):
            if i < len(lines):
                offset += len(lines[i]) + 1  # +1 for newline

        # Add column offset
        offset += col

        return offset

    def _find_tag_start_before(self, line: int, col: int, tag_name: str) -> int:
        """Find the start of an opening tag given position after it.

        html5lib's position() returns position AFTER processing the tag,
        so we need to search backwards to find where '<tagname' starts.

        Args:
            line: Line number after the tag (1-indexed)
            col: Column number after the tag (0-indexed)
            tag_name: Name of the tag to find

        Returns:
            Byte offset of the '<' that starts the tag
        """
        # Get approximate position
        end_offset = self._line_col_to_byte_offset(line, col)

        # Search backwards for '<tagname'
        search_pattern = f'<{tag_name}'.encode('utf-8')

        # Search backwards from end_offset
        # Look back up to 1000 bytes (should be enough for any tag)
        search_start = max(0, end_offset - 1000)
        segment = self.source[search_start:end_offset]

        # Find last occurrence of '<tagname' in the segment
        last_pos = segment.rfind(search_pattern)

        if last_pos != -1:
            return search_start + last_pos

        # Fallback: couldn't find it, return best guess
        return end_offset


# Backward compatibility alias
SimpleTagScanner = XmlTagScanner
