"""Unit tests for empty element rendering strategies.

This module tests the EmptyElementStrategy pattern and its concrete implementations
for XML and HTML5 document formats.
"""

from lxml import etree
import pytest

from markuplift.empty_element import (
    EmptyElementStrategy,
    EmptyElementTagStyle,
    XmlEmptyElementStrategy,
    Html5EmptyElementStrategy,
)


class TestEmptyElementTagStyleEnum:
    """Tests for the EmptyElementTagStyle enum."""

    def test_enum_has_three_values(self):
        """Verify the enum has exactly three distinct values."""
        values = list(EmptyElementTagStyle)
        assert len(values) == 3

    def test_enum_value_names(self):
        """Verify all three enum values exist with correct names."""
        assert hasattr(EmptyElementTagStyle, "EXPLICIT_TAGS")
        assert hasattr(EmptyElementTagStyle, "SELF_CLOSING_TAG")
        assert hasattr(EmptyElementTagStyle, "VOID_TAG")

    def test_enum_values_are_distinct(self):
        """Verify enum values are distinct."""
        explicit = EmptyElementTagStyle.EXPLICIT_TAGS
        self_closing = EmptyElementTagStyle.SELF_CLOSING_TAG
        void = EmptyElementTagStyle.VOID_TAG

        assert explicit != self_closing
        assert explicit != void
        assert self_closing != void


class TestXmlEmptyElementStrategy:
    """Tests for XML empty element strategy."""

    def test_returns_self_closing_tag_for_any_element(self):
        """XML strategy returns SELF_CLOSING_TAG for all elements."""
        strategy = XmlEmptyElementStrategy()

        # Test various tag names
        for tag_name in ["div", "span", "custom", "foo", "bar", "root"]:
            elem = etree.Element(tag_name)
            assert strategy.tag_style(elem) == EmptyElementTagStyle.SELF_CLOSING_TAG

    def test_works_with_namespaced_elements(self):
        """XML strategy handles namespaced elements correctly."""
        strategy = XmlEmptyElementStrategy()

        # Create namespaced element
        ns_elem = etree.Element("{http://example.com}custom")
        assert strategy.tag_style(ns_elem) == EmptyElementTagStyle.SELF_CLOSING_TAG

    def test_works_with_elements_with_attributes(self):
        """XML strategy works regardless of attributes (only checks tag)."""
        strategy = XmlEmptyElementStrategy()

        elem = etree.Element("div")
        elem.set("class", "test")
        elem.set("id", "foo")

        assert strategy.tag_style(elem) == EmptyElementTagStyle.SELF_CLOSING_TAG


class TestHtml5EmptyElementStrategy:
    """Tests for HTML5 empty element strategy."""

    # All 13 HTML5 void elements as per WHATWG spec
    HTML5_VOID_ELEMENTS = [
        "area", "base", "br", "col", "embed", "hr", "img",
        "input", "link", "meta", "source", "track", "wbr"
    ]

    # Common non-void elements that might be empty
    NON_VOID_ELEMENTS = [
        "script", "style", "div", "span", "p", "title",
        "textarea", "iframe", "section", "article", "main"
    ]

    def test_void_elements_return_void_tag(self):
        """All 13 HTML5 void elements return VOID_TAG."""
        strategy = Html5EmptyElementStrategy()

        for tag_name in self.HTML5_VOID_ELEMENTS:
            elem = etree.Element(tag_name)
            result = strategy.tag_style(elem)
            assert result == EmptyElementTagStyle.VOID_TAG, \
                f"Expected VOID_TAG for <{tag_name}>, got {result}"

    def test_non_void_elements_return_explicit_tags(self):
        """Common non-void elements return EXPLICIT_TAGS."""
        strategy = Html5EmptyElementStrategy()

        for tag_name in self.NON_VOID_ELEMENTS:
            elem = etree.Element(tag_name)
            result = strategy.tag_style(elem)
            assert result == EmptyElementTagStyle.EXPLICIT_TAGS, \
                f"Expected EXPLICIT_TAGS for <{tag_name}>, got {result}"

    def test_custom_elements_return_explicit_tags(self):
        """Custom/web component elements return EXPLICIT_TAGS."""
        strategy = Html5EmptyElementStrategy()

        custom_tags = ["my-component", "custom-widget", "x-button"]
        for tag_name in custom_tags:
            elem = etree.Element(tag_name)
            assert strategy.tag_style(elem) == EmptyElementTagStyle.EXPLICIT_TAGS

    def test_void_elements_with_attributes(self):
        """Void elements with attributes still return VOID_TAG."""
        strategy = Html5EmptyElementStrategy()

        img = etree.Element("img")
        img.set("src", "test.jpg")
        img.set("alt", "Test image")
        assert strategy.tag_style(img) == EmptyElementTagStyle.VOID_TAG

        br = etree.Element("br")
        br.set("class", "clearfix")
        assert strategy.tag_style(br) == EmptyElementTagStyle.VOID_TAG

    def test_case_sensitivity(self):
        """HTML5 tags should be lowercase (case-sensitive check)."""
        strategy = Html5EmptyElementStrategy()

        # Lowercase should be void
        br_lower = etree.Element("br")
        assert strategy.tag_style(br_lower) == EmptyElementTagStyle.VOID_TAG

        # Uppercase BR is not in the void set (HTML is case-sensitive in lxml)
        br_upper = etree.Element("BR")
        assert strategy.tag_style(br_upper) == EmptyElementTagStyle.EXPLICIT_TAGS

    def test_void_element_count(self):
        """Verify exactly 13 void elements in HTML5."""
        assert len(self.HTML5_VOID_ELEMENTS) == 13

    def test_param_not_in_void_elements(self):
        """Verify obsolete 'param' element is not in void elements."""
        strategy = Html5EmptyElementStrategy()

        param = etree.Element("param")
        # param is obsolete and should not be treated as void
        assert strategy.tag_style(param) == EmptyElementTagStyle.EXPLICIT_TAGS

    def test_all_void_elements_defined(self):
        """Verify all WHATWG-specified void elements are present."""
        expected_void = {
            "area", "base", "br", "col", "embed", "hr", "img",
            "input", "link", "meta", "source", "track", "wbr"
        }
        assert set(self.HTML5_VOID_ELEMENTS) == expected_void


class TestStrategyAbstractBase:
    """Tests for EmptyElementStrategy abstract base class."""

    def test_cannot_instantiate_abstract_strategy(self):
        """Cannot instantiate the abstract base class directly."""
        with pytest.raises(TypeError):
            EmptyElementStrategy()

    def test_concrete_strategies_implement_tag_style(self):
        """Verify concrete strategies implement tag_style method."""
        xml_strategy = XmlEmptyElementStrategy()
        html5_strategy = Html5EmptyElementStrategy()

        assert hasattr(xml_strategy, "tag_style")
        assert callable(xml_strategy.tag_style)

        assert hasattr(html5_strategy, "tag_style")
        assert callable(html5_strategy.tag_style)
