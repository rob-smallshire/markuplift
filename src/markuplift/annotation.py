"""Element annotation system for XML/HTML formatting.

This module provides a comprehensive annotation system that attaches metadata
to XML elements during the formatting process. Annotations are used to store
information about element types (block/inline), whitespace handling, indentation
levels, and other formatting-related properties.

The annotation system works with ElementPredicate functions to efficiently
categorize and process elements based on their characteristics and context.

Key Components:
    Annotations: Storage class for element metadata
    Element type annotation functions (block/inline classification)
    Whitespace processing annotation functions
    Indentation level calculation functions
    Text transformation functions
"""

from typing import Any, Callable
from functools import partial
from enum import Enum

from lxml import etree

# Import ElementPredicate type alias
from markuplift.types import ElementPredicate

from markuplift.utilities import (
    is_in_mixed_content, parent_is_annotated_with, normalize_ws,
    siblings,
)

LOGICAL_LEVEL_ANNOTATION_KEY = "logical_level"

PHYSICAL_LEVEL_ANNOTATION_KEY = "physical_level"

XML_SPACE_DEFAULT = "default"
XML_SPACE_PRESERVE = "preserve"

WHITESPACE_ANNOTATION_KEY = "whitespace"
PRESERVE_WHITESPACE_ANNOTATION = "preserve"
NORMALIZE_WHITESPACE_ANNOTATION = "normalize"
STRIP_WHITESPACE_ANNOTATION = "strip"  # Strip implies normalize
STRICT_WHITESPACE_ANNOTATION = "strict" # No transformations at all
# If there is no value associated with WHITESPACE_ANNOTATION_KEY , the formatter can take action
# contextually, e.g. based on whether the element is block or inline.

TYPE_ANNOTATION_KEY = "type"
BLOCK_TYPE_ANNOTATION = "block"
INLINE_TYPE_ANNOTATION = "inline"
# If there is no value associated with TYPE_ANNOTATION_KEY , the formatter can take action
# contextually, e.g. based on whether the element is in mixed content or not.
BLOCK_TYPES = {None, BLOCK_TYPE_ANNOTATION, INLINE_TYPE_ANNOTATION}

class Annotations:

    def __init__(self):
        self._annotations: dict[etree._Element, dict[str, str]] = {}

    def annotate(self, element: etree._Element, attribute_name: str, attribute_value: Any):
        if element not in self._annotations:
            self._annotations[element] = {}
        self._annotations[element][attribute_name] = attribute_value

    def annotation(self, element: etree._Element, attribute_name: str, default: Any = None) ->Any:
        return self._annotations.get(element, {}).get(attribute_name, default)


class AnnotationConflictMode(Enum):
    RAISE = "raise"
    SKIP = "skip"
    OVERWRITE = "overwrite"


class AnnotationConflictError(Exception):
    pass


def annotate_explicit_block_elements(
    root: etree._Element,
    annotations: Annotations,
    block_predicate: ElementPredicate,
):
    annotate_matches(root, annotations, block_predicate, TYPE_ANNOTATION_KEY, BLOCK_TYPE_ANNOTATION, conflict_mode=AnnotationConflictMode.RAISE)


def annotate_explicit_inline_elements(
    root: etree._Element,
    annotations: Annotations,
    inline_predicate: ElementPredicate,
):
    annotate_matches(root, annotations, inline_predicate, TYPE_ANNOTATION_KEY, INLINE_TYPE_ANNOTATION, conflict_mode=AnnotationConflictMode.RAISE)


def annotate_elements_in_mixed_content_as_inline(
    root: etree._Element,
    annotations: Annotations,
):
    annotate_matches(root, annotations, is_in_mixed_content, TYPE_ANNOTATION_KEY, INLINE_TYPE_ANNOTATION, conflict_mode=AnnotationConflictMode.SKIP)


def annotate_inline_descendants_as_inline(
    root: etree._Element,
    annotations: Annotations,
):
    """The inline nature of an element is inherited by its descendants unless they are already annotated with a type."""
    annotate_matches(
        root,
        annotations,
        partial(parent_is_annotated_with, annotations=annotations, annotation_key=TYPE_ANNOTATION_KEY, annotation_value=INLINE_TYPE_ANNOTATION),
        TYPE_ANNOTATION_KEY,
        INLINE_TYPE_ANNOTATION,
        conflict_mode=AnnotationConflictMode.SKIP,
    )


def annotate_unmixed_block_descendants_as_block(
    root: etree._Element,
    annotations: Annotations,
):
    """The block nature of an element is inherited by its descendants iff they are element-only (i.e. are not mixed with significant text)
    and none of the siblings are inline.
    """
    # We need to combine two predicates: parent is annotated as block, and element is not in mixed content
    annotate_matches(
        root,
        annotations,
        lambda e: (
            parent_is_annotated_with(e, annotations, TYPE_ANNOTATION_KEY, BLOCK_TYPE_ANNOTATION)
            and
            (not is_in_mixed_content(e))
            and not any(
                annotations.annotation(sibling, TYPE_ANNOTATION_KEY) == INLINE_TYPE_ANNOTATION
                for sibling in siblings(e)
            )
        ),
        TYPE_ANNOTATION_KEY,
        BLOCK_TYPE_ANNOTATION,
        conflict_mode=AnnotationConflictMode.SKIP,
    )


def annotate_xml_space(
    root: etree._Element,
    annotations: Annotations,
):
    """Annotate elements with xml:space="preserve" with whitespace='preserve'.

    This attribute propagates to descendants unless it is overridden by xml:space="default", though
    in practice we'll consider any value other than "preserve" to be "default" and stop propagation.

    We mark elements affected by xml:space="preserve" with a 'whitespace' annotation with value
    'preserve'.
    """
    annotate_matches(
        root,
        annotations,
        lambda e: (
            e.get("{http://www.w3.org/XML/1998/namespace}space") == XML_SPACE_PRESERVE
            or
            (
                parent_is_annotated_with(e, annotations, WHITESPACE_ANNOTATION_KEY, STRICT_WHITESPACE_ANNOTATION)
                and
                e.get("{http://www.w3.org/XML/1998/namespace}space") != XML_SPACE_DEFAULT
            )
        ),
        WHITESPACE_ANNOTATION_KEY,
        STRICT_WHITESPACE_ANNOTATION,
        conflict_mode=AnnotationConflictMode.OVERWRITE,
    )


def annotate_explicit_whitespace_preserving_elements(
    root: etree._Element,
    annotations: Annotations,
    predicate: ElementPredicate,
):
    annotate_matches(
        root,
        annotations,
        predicate,
        WHITESPACE_ANNOTATION_KEY,
        PRESERVE_WHITESPACE_ANNOTATION,
        conflict_mode=AnnotationConflictMode.OVERWRITE
    )


def annotate_whitespace_preserving_descendants_as_whitespace_preserving(
    root: etree._Element,
    annotations: Annotations,
):
    """The whitespace-preserving nature of an element is inherited by its descendants unless they are already annotated with whitespace."""
    annotate_matches(
        root,
        annotations,
        partial(parent_is_annotated_with, annotations=annotations, annotation_key=WHITESPACE_ANNOTATION_KEY, annotation_value=PRESERVE_WHITESPACE_ANNOTATION),
        WHITESPACE_ANNOTATION_KEY,
        PRESERVE_WHITESPACE_ANNOTATION,
        conflict_mode=AnnotationConflictMode.SKIP,
    )


def annotate_explicit_whitespace_normalizing_elements(
    root: etree._Element,
    annotations: Annotations,
    predicate: ElementPredicate,
):
    annotate_matches(
        root,
        annotations,
        predicate,
        WHITESPACE_ANNOTATION_KEY,
        NORMALIZE_WHITESPACE_ANNOTATION,
        conflict_mode=AnnotationConflictMode.OVERWRITE
    )


def annotate_explicit_stripped_elements(
    root: etree._Element,
    annotations: Annotations,
    predicate: ElementPredicate,
):
    annotate_matches(
        root,
        annotations,
        predicate,
        WHITESPACE_ANNOTATION_KEY,
        STRIP_WHITESPACE_ANNOTATION,
        conflict_mode=AnnotationConflictMode.OVERWRITE
    )


def annotate_untyped_elements_as_default(
    root: etree._Element,
    annotations: Annotations,
    default_type: str,
):
    if default_type not in BLOCK_TYPES:
        raise ValueError(f"default_type must be one of {BLOCK_TYPES}")
    annotate_matches(
        root,
        annotations,
        lambda e: annotations.annotation(e, TYPE_ANNOTATION_KEY) is None,
        TYPE_ANNOTATION_KEY,
        default_type,
        conflict_mode=AnnotationConflictMode.SKIP,
    )


def annotate_logical_level(
    root: etree._Element,
    annotations: Annotations,
):
    annotations.annotate(root, LOGICAL_LEVEL_ANNOTATION_KEY, 0)
    for elem in root.iter():
        parent = elem.getparent()
        if parent is not None:
            parent_level = annotations.annotation(parent, LOGICAL_LEVEL_ANNOTATION_KEY)
            if parent_level is not None:
                annotations.annotate(elem, LOGICAL_LEVEL_ANNOTATION_KEY, parent_level + 1)


def annotate_physical_level(
    root: etree._Element,
    annotations: Annotations,
):
    annotations.annotate(root, PHYSICAL_LEVEL_ANNOTATION_KEY, 0)
    for elem in root.iter():
        parent = elem.getparent()
        if parent is not None:
            parent_level = annotations.annotation(parent, PHYSICAL_LEVEL_ANNOTATION_KEY)
            if parent_level is not None:
                parent_type = annotations.annotation(parent, TYPE_ANNOTATION_KEY)
                if parent_type == INLINE_TYPE_ANNOTATION:
                    physical_level = parent_level
                elif parent_type == BLOCK_TYPE_ANNOTATION:
                    physical_level = parent_level + 1
                else:
                    assert parent_type is None
                    physical_level = parent_level  # Preserve existing structure
                annotations.annotate(elem, PHYSICAL_LEVEL_ANNOTATION_KEY, physical_level)


def annotate_text_transforms(
    root: etree._Element,
    annotations: Annotations,
    one_indent: str,
):
    # The text of an element comes between the element's start tag and the start tag of its first
    # child (or its end tag if it has no children). This function will emplace an attribute which
    # describes how this text should be transformed based on existing annotations on the element and
    # its first child (if any).

    for elem in root.iter():
        text_transforms: list[Callable[[str], str]] = []
        whitespace = annotations.annotation(elem, WHITESPACE_ANNOTATION_KEY)
        first_child = next(iter(elem), None)
        first_child_type = (
            annotations.annotation(first_child, TYPE_ANNOTATION_KEY)
            if (first_child is not None) else
            None
        )

        if whitespace not in {PRESERVE_WHITESPACE_ANNOTATION, STRICT_WHITESPACE_ANNOTATION}:
            if whitespace in {NORMALIZE_WHITESPACE_ANNOTATION, STRIP_WHITESPACE_ANNOTATION}:
                text_transforms.append(normalize_ws)
                if whitespace == STRIP_WHITESPACE_ANNOTATION:
                    text_transforms.append(str.lstrip)
            if first_child_type == BLOCK_TYPE_ANNOTATION:
                child_physical_level = annotations.annotation(
                    first_child, PHYSICAL_LEVEL_ANNOTATION_KEY, 0
                )
                text_transform = partial(
                    transform_text_preceding_block, physical_level=child_physical_level,
                    one_indent=one_indent
                )
                text_transforms.append(text_transform)

            if first_child is None:
                if whitespace == STRIP_WHITESPACE_ANNOTATION:
                    text_transforms.append(str.rstrip)

        annotations.annotate(elem, "text_transforms", text_transforms)


def annotate_tail_transforms(root, annotations, one_indent):
    # The tail text of an element comes between the element's end tag and the start tag of its
    # next sibling (or its parent's end tag if it has no next sibling). This function will emplace
    # an attribute which describes how this tail text should be transformed based on existing
    # annotations on the element and its next sibling (if any).

    for elem in root.iter():
        tail_transforms: list[Callable[[str], str]] = []

        # Tail text exists within the parent element, so we consider the parent's whitespace annotation
        # when determining how to transform the tail text.
        parent = elem.getparent()
        parent_whitespace = (
            annotations.annotation(parent, WHITESPACE_ANNOTATION_KEY)
            if (parent is not None) else
            None
        )

        parent_physical_level = (
            annotations.annotation(parent, PHYSICAL_LEVEL_ANNOTATION_KEY, 0)
            if (parent is not None) else
            0
        )

        next_sibling = elem.getnext()
        next_sibling_type = (
            annotations.annotation(next_sibling, TYPE_ANNOTATION_KEY)
            if (next_sibling is not None) else
            None
        )

        # We also don't need to consider the element's own whitespace annotation, since that only
        # affects the element's text, not its tail. However, we do consider the element's
        # type, since that can affect how we treat the tail text. Tail text can also precede a block
        # element, so we need to consider any following sibling elements as well.
        elem_type = annotations.annotation(elem, TYPE_ANNOTATION_KEY)
        if parent_whitespace not in {PRESERVE_WHITESPACE_ANNOTATION, STRICT_WHITESPACE_ANNOTATION}:
            if parent_whitespace in {NORMALIZE_WHITESPACE_ANNOTATION, STRIP_WHITESPACE_ANNOTATION}:
                tail_transforms.append(normalize_ws)
                if next_sibling is None:
                    if parent_whitespace == STRIP_WHITESPACE_ANNOTATION:
                        tail_transforms.append(str.rstrip)
            if elem_type == BLOCK_TYPE_ANNOTATION:
                if next_sibling_type in {BLOCK_TYPE_ANNOTATION}:
                    text_transform = partial(
                        transform_text_following_block, physical_level=parent_physical_level,
                        one_indent=one_indent
                    )
                    tail_transforms.append(text_transform)
                elif next_sibling_type == INLINE_TYPE_ANNOTATION:
                    text_transform = partial(
                        transform_text_following_block_preceding_inline, physical_level=parent_physical_level,
                    )
                    tail_transforms.append(text_transform)  # Just add a newline before the text
                else:
                    if parent is not None:
                        text_transform = partial(
                            transform_text_following_block, physical_level=parent_physical_level,
                            one_indent=one_indent
                        )
                        tail_transforms.append(text_transform)
                    else:
                        assert parent is None
                        # If the element is at logical level 0, it is the root element, so we
                        # are not allowed to have any tail text at all.
                        tail_transforms.append(lambda s: "")

            if next_sibling is not None:
                if next_sibling_type == BLOCK_TYPE_ANNOTATION:
                    sibling_physical_level = annotations.annotation(
                        next_sibling, PHYSICAL_LEVEL_ANNOTATION_KEY, 0
                    )
                    text_transform = partial(
                        transform_text_preceding_block, physical_level=sibling_physical_level,
                        one_indent=one_indent
                    )
                    tail_transforms.append(text_transform)

        annotations.annotate(elem, "tail_transforms", tail_transforms)



def transform_text_preceding_block(text: str, physical_level: int, one_indent: str) -> str:
    # 1. Strip trailing whitespace
    text = text.rstrip()
    # 2. Add newline and indentation after the text to separate it from the block child
    indent = one_indent * physical_level
    text = text + "\n" + indent
    return text


def transform_text_following_block(text: str, physical_level: int, one_indent: str) -> str:
    # 1. Strip leading whitespace
    text = text.lstrip()
    # 2. Add newline and indentation before the text to separate it from the block element
    indent = one_indent * physical_level
    text = "\n" + indent + text
    return text


def transform_text_following_block_preceding_inline(text: str, physical_level: int) -> str:
    # If the leading run of whitespace does not contain a newline, we add one
    leading_ws = len(text) - len(text.lstrip())
    if leading_ws > 0:
        if "\n" not in text[:leading_ws]:
            text = "\n" + text
    return text


def annotate_matches(
    tree: etree._Element,
    annotations: Annotations,
    predicate: ElementPredicate,
    annotation_key: str,
    annotation_value: str,
    *,
    conflict_mode: AnnotationConflictMode = AnnotationConflictMode.RAISE,
):
    """Annotate elements in the tree that match the predicate with the given annotation.

    Args:
        tree: The XML tree to annotate.
        annotations: The Annotations object to store annotations.
        predicate: A function that takes an element and returns True if it should be annotated.
        annotation_key: The key for the annotation.
        annotation_value: The value for the annotation.
        conflict_mode: Determines how to handle conflicts with existing annotations.
    """
    for elem in tree.iter():
        if predicate(elem):
            existing_type = annotations.annotation(elem, annotation_key)
            if existing_type is not None:
                if conflict_mode == AnnotationConflictMode.RAISE:
                    raise AnnotationConflictError(
                        f"Element <{elem.tag}> was previously marked as {existing_type}, cannot also mark as {annotation_value}"
                    )
                elif conflict_mode == AnnotationConflictMode.SKIP:
                    continue
                elif conflict_mode == AnnotationConflictMode.OVERWRITE:
                    pass  # Overwrite annotation
            annotations.annotate(elem, annotation_key, annotation_value)

