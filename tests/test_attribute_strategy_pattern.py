"""Tests for the attribute formatting strategy pattern."""

from inspect import cleandoc


from markuplift import Formatter, Html5Formatter, XmlFormatter
from markuplift.attribute_formatting import (
    AttributeFormattingStrategy,
    Html5AttributeStrategy,
    XmlAttributeStrategy,
    NullAttributeStrategy,
)
from markuplift.predicates import attribute_matches


class MockAttributeStrategy(AttributeFormattingStrategy):
    """Mock strategy for testing."""

    def format_attribute(self, element, attr_name, attr_value, user_formatters, formatter, level):
        # Add prefix to all attribute values
        return f"mock-{attr_value}", False


def test_formatter_uses_null_strategy_by_default():
    """Test that Formatter uses NullAttributeStrategy by default."""
    formatter = Formatter()
    assert isinstance(formatter._attribute_strategy, NullAttributeStrategy)


def test_formatter_accepts_custom_strategy():
    """Test that Formatter accepts a custom attribute strategy."""
    custom_strategy = MockAttributeStrategy()
    formatter = Formatter(attribute_strategy=custom_strategy)
    assert formatter._attribute_strategy is custom_strategy


def test_html5_formatter_uses_html5_strategy():
    """Test that Html5Formatter configures Html5AttributeStrategy."""
    formatter = Html5Formatter()
    assert isinstance(formatter._formatter._attribute_strategy, Html5AttributeStrategy)


def test_xml_formatter_uses_xml_strategy():
    """Test that XmlFormatter configures XmlAttributeStrategy."""
    formatter = XmlFormatter()
    assert isinstance(formatter._formatter._attribute_strategy, XmlAttributeStrategy)


def test_null_strategy_only_applies_user_formatters():
    """Test that NullAttributeStrategy only applies user formatters."""

    def uppercase_formatter(value, formatter, level):
        return value.upper()

    example = cleandoc("""
        <root>
            <element class="test" id="example">Content</element>
        </root>
    """)

    formatter = Formatter(reformat_attribute_when={attribute_matches("class", "test"): uppercase_formatter})
    actual = formatter.format_str(example)

    expected = cleandoc("""
        <root>
          <element class="TEST" id="example">Content</element>
        </root>
    """)

    assert actual == expected


def test_xml_strategy_applies_user_formatters():
    """Test that XmlAttributeStrategy applies user formatters (no built-in XML rules yet)."""

    def prefix_formatter(value, formatter, level):
        return f"xml-{value}"

    example = cleandoc("""
        <root>
            <element class="test" id="example">Content</element>
        </root>
    """)

    formatter = XmlFormatter(reformat_attribute_when={attribute_matches("class", "test"): prefix_formatter})
    actual = formatter.format_str(example)

    expected = cleandoc("""
        <root>
          <element class="xml-test" id="example">Content</element>
        </root>
    """)

    assert actual == expected


def test_html5_strategy_applies_boolean_rules_then_user_formatters():
    """Test that Html5AttributeStrategy applies HTML5 rules first, then user formatters."""

    # This formatter should not be called for boolean attributes since they're already minimized
    def should_not_be_called(value, formatter, level):
        return f"SHOULD_NOT_APPEAR-{value}"

    # This formatter should be called for non-boolean attributes
    def uppercase_formatter(value, formatter, level):
        return value.upper()

    example = cleandoc("""
        <div>
            <input checked="checked" class="form-input" disabled="disabled">
        </div>
    """)

    formatter = Html5Formatter(
        reformat_attribute_when={
            attribute_matches("checked", "any-value"): should_not_be_called,  # Won't be called - different value
            attribute_matches("class", "form-input"): uppercase_formatter,  # Will be called - regular attr
        }
    )
    actual = formatter.format_str(example)

    expected = (
        cleandoc("""
        <!DOCTYPE html>
        <div>
          <input checked class="FORM-INPUT" disabled />
        </div>
    """)
        + "\n"
    )

    assert actual == expected


def test_strategy_receives_correct_parameters():
    """Test that the strategy receives the correct parameters."""

    class TestStrategy(AttributeFormattingStrategy):
        def __init__(self):
            self.calls = []

        def format_attribute(self, element, attr_name, attr_value, user_formatters, formatter, level):
            self.calls.append(
                {
                    "element_tag": element.tag,
                    "attr_name": attr_name,
                    "attr_value": attr_value,
                    "user_formatters_count": len(user_formatters),
                    "level": level,
                }
            )
            return attr_value, False

    strategy = TestStrategy()
    example = cleandoc("""
        <root>
            <child attr1="value1" attr2="value2">Content</child>
        </root>
    """)

    formatter = Formatter(attribute_strategy=strategy)
    formatter.format_str(example)

    # Should have been called for both attributes
    assert len(strategy.calls) == 2

    # Check first call
    call1 = strategy.calls[0]
    assert call1["element_tag"] == "child"
    assert call1["attr_name"] in ["attr1", "attr2"]
    assert call1["attr_value"] in ["value1", "value2"]
    assert call1["user_formatters_count"] == 0
    assert call1["level"] == 1


def test_strategy_with_attribute_wrapping():
    """Test that strategy works correctly with attribute wrapping."""

    example = cleandoc("""
        <root>
            <input checked="checked" class="form-control" disabled="disabled" id="test-input">
        </root>
    """)

    formatter = Html5Formatter(wrap_attributes_when=lambda root: lambda element: element.tag == "input")
    actual = formatter.format_str(example)

    expected = (
        cleandoc("""
        <!DOCTYPE html>
        <root>
          <input
            checked
            class="form-control"
            disabled
            id="test-input"
          />
        </root>
    """)
        + "\n"
    )

    assert actual == expected


def test_custom_strategy_integration():
    """Test integration of a completely custom strategy."""

    class PrefixStrategy(AttributeFormattingStrategy):
        def format_attribute(self, element, attr_name, attr_value, user_formatters, formatter, level):
            # Apply built-in rule: prefix all attribute values
            value = f"prefix-{attr_value}"

            # Then apply user formatters
            for predicate, formatter_func in user_formatters.items():
                if predicate(element, attr_name, value):
                    value = formatter_func(value, formatter, level)
                    break

            return value, False

    def suffix_formatter(value, formatter, level):
        return f"{value}-suffix"

    example = cleandoc("""
        <root>
            <element class="test" id="example">Content</element>
        </root>
    """)

    formatter = Formatter(
        attribute_strategy=PrefixStrategy(),
        reformat_attribute_when={attribute_matches("class", "prefix-test"): suffix_formatter},
    )
    actual = formatter.format_str(example)

    expected = cleandoc("""
        <root>
          <element class="prefix-test-suffix" id="prefix-example">Content</element>
        </root>
    """)

    assert actual == expected


def test_backward_compatibility_with_existing_code():
    """Test that existing code without strategies continues to work."""

    def uppercase_formatter(value, formatter, level):
        return value.upper()

    example = cleandoc("""
        <root>
            <element class="test" id="example">Content</element>
        </root>
    """)

    # This should work exactly as before
    formatter = Formatter(reformat_attribute_when={attribute_matches("class", "test"): uppercase_formatter})
    actual = formatter.format_str(example)

    expected = cleandoc("""
        <root>
          <element class="TEST" id="example">Content</element>
        </root>
    """)

    assert actual == expected
