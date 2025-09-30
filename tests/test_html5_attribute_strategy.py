"""Tests for HTML5 attribute formatting strategy."""

from inspect import cleandoc

from markuplift import Html5Formatter
from markuplift.attribute_formatting import Html5AttributeStrategy


def test_html5_boolean_attributes_are_minimized():
    """Test that HTML5 boolean attributes are minimized to empty strings."""
    # Test various boolean attributes with different values
    example = cleandoc("""
        <div>
            <input checked="checked" disabled="true" readonly="" required="false">
            <video autoplay="autoplay" controls="controls" loop muted="muted"></video>
            <details open="open">
                <summary>Details</summary>
                Content
            </details>
        </div>
    """)

    formatter = Html5Formatter()
    actual = formatter.format_str(example)

    expected = (
        cleandoc("""
        <!DOCTYPE html>
        <div>
          <input checked disabled readonly required />
          <video autoplay controls loop muted />
          <details open><summary>Details</summary> Content</details>
        </div>
    """)
        + "\n"
    )

    assert actual == expected


def test_non_boolean_attributes_are_preserved():
    """Test that non-boolean attributes retain their values."""
    example = cleandoc("""
        <div>
            <input type="text" value="test" id="input1" class="form-control">
            <a href="https://example.com" title="Example Link">Link</a>
        </div>
    """)

    formatter = Html5Formatter(reorder_attributes_when={})  # Disable default ordering for this test
    actual = formatter.format_str(example)

    expected = (
        cleandoc("""
        <!DOCTYPE html>
        <div>
          <input type="text" value="test" id="input1" class="form-control" />
         <a href="https://example.com" title="Example Link">Link</a></div>
    """)
        + "\n"
    )

    assert actual == expected


def test_mixed_boolean_and_regular_attributes():
    """Test elements with both boolean and regular attributes."""
    example = cleandoc("""
        <form>
            <input type="email" required="required" placeholder="Enter email" disabled="disabled">
            <button type="submit" formnovalidate="formnovalidate">Submit</button>
        </form>
    """)

    formatter = Html5Formatter()
    actual = formatter.format_str(example)

    expected = (
        cleandoc("""
        <!DOCTYPE html>
        <form>
          <input type="email" required placeholder="Enter email" disabled />
          <button type="submit" formnovalidate>Submit</button>
        </form>
    """)
        + "\n"
    )

    assert actual == expected


def test_all_html5_boolean_attributes():
    """Test all defined HTML5 boolean attributes."""
    example = cleandoc("""
        <div>
            <input async="async" autofocus="autofocus" checked="checked"
                   default="default" defer="defer" disabled="disabled"
                   formnovalidate="formnovalidate" hidden="hidden"
                   multiple="multiple" readonly="readonly" required="required"
                   reversed="reversed" selected="selected">
            <video autoplay="autoplay" controls="controls" loop="loop" muted="muted"></video>
            <script nomodule="nomodule"></script>
            <map name="map1">
                <area ismap="ismap">
            </map>
            <option novalidate="novalidate"></option>
            <details open="open" itemscope="itemscope"></details>
        </div>
    """)

    formatter = Html5Formatter()
    actual = formatter.format_str(example)

    expected = (
        cleandoc("""
        <!DOCTYPE html>
        <div>
          <input async autofocus checked default defer disabled formnovalidate hidden multiple readonly required reversed selected />
          <video autoplay controls loop muted />
          <script nomodule />
          <map name="map1">
            <area ismap />
          </map>
          <option novalidate />
          <details open itemscope />
        </div>
    """)
        + "\n"
    )

    assert actual == expected


def test_attribute_strategy_composition_with_user_formatters():
    """Test that user-provided attribute formatters work with HTML5 strategy."""
    from markuplift.predicates import attribute_matches

    # Custom formatter that uppercases style attributes
    def uppercase_style(value, formatter, level):
        return value.upper()

    example = cleandoc("""
        <div style="color: red; font-size: 14px;">
            <input checked="checked" style="border: 1px solid black;">
        </div>
    """)

    formatter = Html5Formatter(reformat_attribute_when={attribute_matches("style", lambda v: True): uppercase_style})
    actual = formatter.format_str(example)

    expected = (
        cleandoc("""
        <!DOCTYPE html>
        <div style="COLOR: RED; FONT-SIZE: 14PX;">
          <input checked style="BORDER: 1PX SOLID BLACK;" />
        </div>
    """)
        + "\n"
    )

    assert actual == expected


def test_html5_strategy_boolean_attribute_list():
    """Test that the Html5AttributeStrategy has the correct boolean attributes."""
    strategy = Html5AttributeStrategy()

    # These are the HTML5 boolean attributes as defined in the spec
    expected_boolean_attrs = {
        "async",
        "autofocus",
        "autoplay",
        "checked",
        "controls",
        "default",
        "defer",
        "disabled",
        "formnovalidate",
        "hidden",
        "ismap",
        "itemscope",
        "loop",
        "multiple",
        "muted",
        "nomodule",
        "novalidate",
        "open",
        "readonly",
        "required",
        "reversed",
        "selected",
    }

    assert strategy.BOOLEAN_ATTRIBUTES == expected_boolean_attrs


def test_boolean_attribute_formatting_logic():
    """Test the boolean attribute formatting logic directly."""
    strategy = Html5AttributeStrategy()

    # All boolean attributes should be minimized to empty string
    assert strategy._format_boolean_attribute("checked") == ""
    assert strategy._format_boolean_attribute("true") == ""
    assert strategy._format_boolean_attribute("false") == ""
    assert strategy._format_boolean_attribute("") == ""
    assert strategy._format_boolean_attribute("any-value") == ""


def test_case_sensitivity_of_boolean_attributes():
    """Test that boolean attribute detection is case-sensitive."""
    # Test with actual boolean attributes vs similar non-boolean attributes
    example = cleandoc("""
        <div>
            <input checked="checked" data-custom="custom" required="required">
        </div>
    """)

    formatter = Html5Formatter()
    actual = formatter.format_str(example)

    # Boolean attributes 'checked' and 'required' should be minimized
    # data-* attributes are not boolean attributes so they keep their values
    expected = (
        cleandoc("""
        <!DOCTYPE html>
        <div>
          <input checked data-custom="custom" required />
        </div>
    """)
        + "\n"
    )

    assert actual == expected


def test_empty_boolean_attributes_remain_empty():
    """Test that boolean attributes that are already empty remain empty."""
    example = cleandoc("""
        <div>
            <input checked="" disabled="" hidden="">
        </div>
    """)

    formatter = Html5Formatter()
    actual = formatter.format_str(example)

    expected = (
        cleandoc("""
        <!DOCTYPE html>
        <div>
          <input checked disabled hidden />
        </div>
    """)
        + "\n"
    )

    assert actual == expected
