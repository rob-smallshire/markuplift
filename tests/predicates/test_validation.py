import pytest

from markuplift.predicates import (
    PredicateError,
    tag_equals,
    tag_in,
    has_attribute,
    attribute_equals,
    attribute_count_min,
    attribute_count_max,
    attribute_count_between,
    is_processing_instruction,
)


class TestTagValidation:
    """Test validation of tag names."""

    def test_tag_equals_empty_tag(self):
        """Test that empty tag names are rejected."""
        with pytest.raises(PredicateError, match="Tag name cannot be empty"):
            tag_equals("")

    def test_tag_equals_invalid_tag(self):
        """Test that invalid tag names are rejected."""
        with pytest.raises(PredicateError, match="Invalid tag name"):
            tag_equals("123invalid")  # Tags can't start with numbers

    def test_tag_equals_valid_tag(self):
        """Test that valid tag names are accepted."""
        factory = tag_equals("div")  # Should not raise
        assert factory is not None

    def test_tag_in_no_tags(self):
        """Test that tag_in requires at least one tag."""
        with pytest.raises(PredicateError, match="At least one tag name must be provided"):
            tag_in()

    def test_tag_in_empty_tag(self):
        """Test that empty tag names in tag_in are rejected."""
        with pytest.raises(PredicateError, match="Tag name cannot be empty"):
            tag_in("div", "", "span")

    def test_tag_in_invalid_tag(self):
        """Test that invalid tag names in tag_in are rejected."""
        with pytest.raises(PredicateError, match="Invalid tag name"):
            tag_in("div", "123invalid", "span")

    def test_tag_in_valid_tags(self):
        """Test that valid tag names are accepted."""
        factory = tag_in("div", "span", "p")  # Should not raise
        assert factory is not None


class TestAttributeValidation:
    """Test validation of attribute names."""

    def test_has_attribute_empty_name(self):
        """Test that empty attribute names are rejected."""
        with pytest.raises(PredicateError, match="Attribute name cannot be empty"):
            has_attribute("")

    def test_has_attribute_invalid_name(self):
        """Test that invalid attribute names are rejected."""
        with pytest.raises(PredicateError, match="Invalid attribute name"):
            has_attribute("123invalid")  # Attributes can't start with numbers

    def test_has_attribute_valid_name(self):
        """Test that valid attribute names are accepted."""
        factory = has_attribute("class")  # Should not raise
        assert factory is not None

    def test_attribute_equals_empty_name(self):
        """Test that empty attribute names are rejected."""
        with pytest.raises(PredicateError, match="Attribute name cannot be empty"):
            attribute_equals("", "value")

    def test_attribute_equals_invalid_name(self):
        """Test that invalid attribute names are rejected."""
        with pytest.raises(PredicateError, match="Invalid attribute name"):
            attribute_equals("123invalid", "value")

    def test_attribute_equals_valid_name(self):
        """Test that valid attribute names are accepted."""
        factory = attribute_equals("class", "button")  # Should not raise
        assert factory is not None


class TestCountValidation:
    """Test validation of count parameters."""

    def test_attribute_count_min_negative(self):
        """Test that negative minimum counts are rejected."""
        with pytest.raises(PredicateError, match="Minimum count must be non-negative, got -1"):
            attribute_count_min(-1)

    def test_attribute_count_min_zero(self):
        """Test that zero minimum count is accepted."""
        factory = attribute_count_min(0)  # Should not raise
        assert factory is not None

    def test_attribute_count_min_positive(self):
        """Test that positive minimum counts are accepted."""
        factory = attribute_count_min(5)  # Should not raise
        assert factory is not None

    def test_attribute_count_max_negative(self):
        """Test that negative maximum counts are rejected."""
        with pytest.raises(PredicateError, match="Maximum count must be non-negative, got -1"):
            attribute_count_max(-1)

    def test_attribute_count_max_zero(self):
        """Test that zero maximum count is accepted."""
        factory = attribute_count_max(0)  # Should not raise
        assert factory is not None

    def test_attribute_count_max_positive(self):
        """Test that positive maximum counts are accepted."""
        factory = attribute_count_max(5)  # Should not raise
        assert factory is not None


class TestRangeValidation:
    """Test validation of range parameters."""

    def test_attribute_count_between_negative_min(self):
        """Test that negative minimum counts are rejected."""
        with pytest.raises(PredicateError, match="Minimum count must be non-negative, got -1"):
            attribute_count_between(-1, 5)

    def test_attribute_count_between_negative_max(self):
        """Test that negative maximum counts are rejected."""
        with pytest.raises(PredicateError, match="Maximum count must be non-negative, got -1"):
            attribute_count_between(0, -1)

    def test_attribute_count_between_min_greater_than_max(self):
        """Test that min > max is rejected."""
        with pytest.raises(PredicateError, match="Minimum count \\(5\\) cannot be greater than maximum count \\(3\\)"):
            attribute_count_between(5, 3)

    def test_attribute_count_between_equal_min_max(self):
        """Test that min == max is accepted."""
        factory = attribute_count_between(5, 5)  # Should not raise
        assert factory is not None

    def test_attribute_count_between_valid_range(self):
        """Test that valid ranges are accepted."""
        factory = attribute_count_between(0, 5)  # Should not raise
        assert factory is not None


class TestProcessingInstructionValidation:
    """Test validation of processing instruction parameters."""

    def test_processing_instruction_empty_target(self):
        """Test that empty string targets are rejected."""
        with pytest.raises(PredicateError, match="Processing instruction target cannot be empty"):
            is_processing_instruction("")

    def test_processing_instruction_none_target(self):
        """Test that None target is accepted."""
        factory = is_processing_instruction(None)  # Should not raise
        assert factory is not None

    def test_processing_instruction_valid_target(self):
        """Test that valid targets are accepted."""
        factory = is_processing_instruction("xml-stylesheet")  # Should not raise
        assert factory is not None

    def test_processing_instruction_no_target(self):
        """Test that no target parameter is accepted."""
        factory = is_processing_instruction()  # Should not raise
        assert factory is not None