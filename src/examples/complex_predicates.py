"""Parameterized predicate examples for README.md.

This module demonstrates how to create parameterized predicates that can be
customized for different document types and formatting requirements.
"""

from markuplift.types import ElementPredicateFactory, ElementPredicate


def elements_with_attribute_values(attribute_name: str, *values: str) -> ElementPredicateFactory:
    """Factory for predicate matching elements with specific attribute values.

    This creates a predicate that matches elements where the specified attribute
    contains any of the given values. Useful for formatting based on element
    roles, types, or semantic meaning.

    Args:
        attribute_name: Name of the attribute to check (e.g., 'class', 'role', 'type')
        *values: Attribute values to match against

    Returns:
        ElementPredicateFactory that creates optimized predicates

    Example:
        >>> # Format table cells differently based on their role
        >>> formatter = Html5Formatter(
        ...     block_when=elements_with_attribute_values('role', 'header', 'columnheader')
        ... )

        >>> # Special handling for form elements by type
        >>> formatter = Html5Formatter(
        ...     wrap_attributes_when=elements_with_attribute_values('type', 'email', 'password', 'url')
        ... )
    """

    def create_document_predicate(root) -> ElementPredicate:
        # Pre-scan document to find all matching elements
        matching_elements = set()

        for element in root.iter():
            attr_value = element.get(attribute_name, "")
            if attr_value:
                # Check if any of the target values appear in the attribute
                attr_words = attr_value.lower().split()
                if any(value.lower() in attr_words for value in values):
                    matching_elements.add(element)

        def element_predicate(element) -> bool:
            return element in matching_elements

        return element_predicate

    return create_document_predicate


def table_cells_in_columns(*column_types: str) -> ElementPredicateFactory:
    """Factory for predicate matching table cells in columns with specific semantic types.

    This matches <td> or <th> elements that are in table columns designated for
    specific types of data (like 'price', 'date', 'name', etc.). Column types
    are determined by class attributes on the <col>, <th>, or <td> elements.

    Args:
        *column_types: Column type names to match (e.g., 'price', 'currency', 'date', 'number')

    Returns:
        ElementPredicateFactory that creates optimized predicates

    Example:
        >>> # Right-align numeric and currency columns
        >>> formatter = Html5Formatter(
        ...     wrap_attributes_when=table_cells_in_columns('price', 'currency', 'number')
        ... )

        >>> # Preserve formatting in date and time columns
        >>> formatter = Html5Formatter(
        ...     preserve_whitespace_when=table_cells_in_columns('date', 'time', 'timestamp')
        ... )
    """

    def create_document_predicate(root) -> ElementPredicate:
        matching_elements = set()

        # Find all tables and analyze their column structure
        for table in root.iter("table"):
            column_classes = []

            # Method 1: Check <col> elements for column classes
            colgroup = table.find("colgroup")
            if colgroup is not None:
                for col in colgroup.findall("col"):
                    col_class = col.get("class", "")
                    column_classes.append(col_class.lower().split())

            # Method 2: Check header row for column classes
            if not column_classes:
                thead = table.find("thead")
                if thead is not None:
                    header_row = thead.find("tr")
                    if header_row is not None:
                        for th in header_row.findall("th"):
                            th_class = th.get("class", "")
                            column_classes.append(th_class.lower().split())

            # If we found column structure, match cells in target columns
            if column_classes:
                for row in table.iter("tr"):
                    cells = row.findall("td") + row.findall("th")
                    for col_index, cell in enumerate(cells):
                        if col_index < len(column_classes):
                            cell_classes = column_classes[col_index]
                            # Also check the cell's own class attribute
                            cell_own_classes = cell.get("class", "").lower().split()
                            all_classes = cell_classes + cell_own_classes

                            # Check if any column type matches
                            if any(col_type.lower() in all_classes for col_type in column_types):
                                matching_elements.add(cell)

        def element_predicate(element) -> bool:
            return element in matching_elements

        return element_predicate

    return create_document_predicate


if __name__ == "__main__":
    # Example usage demonstration
    from markuplift import Html5Formatter

    # Create formatter with parameterized predicates
    formatter = Html5Formatter(
        preserve_whitespace_when=code_with_language("python", "yaml"),
        normalize_whitespace_when=elements_in_containers_with_class("sidebar", "highlight"),
        indent_size=2,
    )

    print("Parameterized predicate examples created successfully!")
    print("Use these predicates with custom parameters for flexible document formatting.")
