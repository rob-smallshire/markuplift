"""Tests for html_attribute_order() reorderer function."""

from markuplift import Html5Formatter, html_attribute_order
from markuplift.predicates import any_element


def test_html_attribute_order_img_tag():
    """Test ordering for img tags: src before alt, both after class."""
    html = '<img alt="Logo" style="border:0" src="/logo.png" class="logo" id="main-logo">'

    formatter = Html5Formatter(
        reorder_attributes_when={any_element(): html_attribute_order()}
    )

    result = formatter.format_str(html)

    # Check priority order: id, class, src, alt, style
    assert result.index('id="main-logo"') < result.index('class="logo"')
    assert result.index('class="logo"') < result.index('src="/logo.png"')
    assert result.index('src="/logo.png"') < result.index('alt="Logo"')
    assert result.index('alt="Logo"') < result.index('style="border:0"')


def test_html_attribute_order_link_tag():
    """Test ordering for anchor tags: href comes after class."""
    html = '<a title="Home" href="/" class="nav-link" id="home-link">Home</a>'

    formatter = Html5Formatter(
        reorder_attributes_when={any_element(): html_attribute_order()}
    )

    result = formatter.format_str(html)

    # Check priority order: id, class, href, title
    assert result.index('id="home-link"') < result.index('class="nav-link"')
    assert result.index('class="nav-link"') < result.index('href="/"')
    assert result.index('href="/"') < result.index('title="Home"')


def test_html_attribute_order_form_tag():
    """Test ordering for form tags: action comes after class."""
    html = '<form method="post" action="/submit" class="contact-form" id="contact">'

    formatter = Html5Formatter(
        reorder_attributes_when={any_element(): html_attribute_order()}
    )

    result = formatter.format_str(html)

    # Check priority order: id, class, action, method (other)
    assert result.index('id="contact"') < result.index('class="contact-form"')
    assert result.index('class="contact-form"') < result.index('action="/submit"')
    assert result.index('action="/submit"') < result.index('method="post"')


def test_html_attribute_order_input_tag():
    """Test ordering for input tags: name after id, before type."""
    html = '<input type="text" value="test" name="username" class="form-control" id="user">'

    formatter = Html5Formatter(
        reorder_attributes_when={any_element(): html_attribute_order()}
    )

    result = formatter.format_str(html)

    # Check priority order: id, name, class, other (type, value)
    assert result.index('id="user"') < result.index('name="username"')
    assert result.index('name="username"') < result.index('class="form-control"')


def test_html_attribute_order_button_with_events():
    """Test ordering for buttons with event handlers: on* comes after resources."""
    html = '<button onclick="submit()" class="btn" id="submit-btn" type="submit">Submit</button>'

    formatter = Html5Formatter(
        reorder_attributes_when={any_element(): html_attribute_order()}
    )

    result = formatter.format_str(html)

    # Check priority order: id, class, onclick, type (other)
    assert result.index('id="submit-btn"') < result.index('class="btn"')
    assert result.index('class="btn"') < result.index('onclick="submit()"')


def test_html_attribute_order_aria_attributes():
    """Test ordering for ARIA attributes: come after resources, before data-*."""
    html = '<div data-config="test" aria-label="Navigation" class="nav" id="main-nav" role="navigation">'

    formatter = Html5Formatter(
        reorder_attributes_when={any_element(): html_attribute_order()}
    )

    result = formatter.format_str(html)

    # Check priority order: id, class, aria-* and role (both category 5, original order), data-*
    assert result.index('id="main-nav"') < result.index('class="nav"')
    assert result.index('class="nav"') < result.index('aria-label="Navigation"')
    # aria-label and role are both in same category - original order preserved
    assert result.index('aria-label="Navigation"') < result.index('role="navigation"')
    assert result.index('role="navigation"') < result.index('data-config="test"')


def test_html_attribute_order_data_attributes():
    """Test ordering for data-* attributes: come before style."""
    html = '<div style="color:red" data-value="123" data-id="abc" class="widget" id="main">'

    formatter = Html5Formatter(
        reorder_attributes_when={any_element(): html_attribute_order()}
    )

    result = formatter.format_str(html)

    # Check priority order: id, class, data-* (in original order), style
    assert result.index('id="main"') < result.index('class="widget"')
    assert result.index('class="widget"') < result.index('data-value="123"')
    assert result.index('data-value="123"') < result.index('data-id="abc"')
    assert result.index('data-id="abc"') < result.index('style="color:red"')


def test_html_attribute_order_style_always_last():
    """Test that style attribute always comes last."""
    html = '<div onclick="alert()" style="color:red" data-foo="bar" href="#" class="box" id="main">'

    formatter = Html5Formatter(
        reorder_attributes_when={any_element(): html_attribute_order()}
    )

    result = formatter.format_str(html)

    # Style should be last - verify all other attributes come before style
    style_pos = result.index('style="color:red"')
    assert result.index('id="main"') < style_pos
    assert result.index('class="box"') < style_pos
    assert result.index('href="#"') < style_pos
    assert result.index('onclick="alert()"') < style_pos
    assert result.index('data-foo="bar"') < style_pos


def test_html_attribute_order_preserves_order_within_category():
    """Test that original order is preserved within each category."""
    # Multiple data-* attributes should maintain their original order
    html = '<div data-z="last" data-a="first" data-m="middle" class="test" id="main">'

    formatter = Html5Formatter(
        reorder_attributes_when={any_element(): html_attribute_order()}
    )

    result = formatter.format_str(html)

    # Within data-* category, original order should be preserved
    assert result.index('data-z="last"') < result.index('data-a="first"')
    assert result.index('data-a="first"') < result.index('data-m="middle"')


def test_html_attribute_order_multiple_event_handlers():
    """Test ordering with multiple event handlers."""
    html = '<button onmouseover="hover()" onclick="click()" onmouseout="unhover()" class="btn" id="btn">'

    formatter = Html5Formatter(
        reorder_attributes_when={any_element(): html_attribute_order()}
    )

    result = formatter.format_str(html)

    # id and class first, then all on* events in original order
    assert result.index('id="btn"') < result.index('class="btn"')
    assert result.index('class="btn"') < result.index('onmouseover="hover()"')
    # Events should preserve original order
    assert result.index('onmouseover="hover()"') < result.index('onclick="click()"')
    assert result.index('onclick="click()"') < result.index('onmouseout="unhover()"')


def test_html_attribute_order_mixed_aria_attributes():
    """Test ordering with multiple ARIA attributes."""
    html = '<nav aria-labelledby="nav-title" aria-expanded="true" role="navigation" title="Main Nav" class="navbar" id="main-nav">'

    formatter = Html5Formatter(
        reorder_attributes_when={any_element(): html_attribute_order()}
    )

    result = formatter.format_str(html)

    # id, class, then all semantic/accessibility (all same category, original order preserved)
    assert result.index('id="main-nav"') < result.index('class="navbar"')
    assert result.index('class="navbar"') < result.index('aria-labelledby="nav-title"')
    # All semantic/accessibility attributes preserve original order within category
    assert result.index('aria-labelledby="nav-title"') < result.index('aria-expanded="true"')
    assert result.index('aria-expanded="true"') < result.index('role="navigation"')
    assert result.index('role="navigation"') < result.index('title="Main Nav"')


def test_html_attribute_order_case_insensitive():
    """Test that attribute ordering is case-insensitive."""
    html = '<div STYLE="color:red" ID="main" CLASS="box" DATA-value="test">'

    formatter = Html5Formatter(
        reorder_attributes_when={any_element(): html_attribute_order()}
    )

    result = formatter.format_str(html)

    # HTML5 normalizes attributes to lowercase, but ordering should still work
    assert result.index('id="main"') < result.index('class="box"')
    assert result.index('class="box"') < result.index('data-value="test"')
    assert result.index('data-value="test"') < result.index('style="color:red"')


def test_html_attribute_order_video_tag():
    """Test ordering for video tags with multiple resource attributes."""
    html = '<video controls autoplay poster="/poster.jpg" src="/video.mp4" class="video-player" id="main-video">'

    formatter = Html5Formatter(
        reorder_attributes_when={any_element(): html_attribute_order()}
    )

    result = formatter.format_str(html)

    # id, class, src, then other attributes
    assert result.index('id="main-video"') < result.index('class="video-player"')
    assert result.index('class="video-player"') < result.index('src="/video.mp4"')
    # poster is not in the special list, so it goes in "other" category
    assert result.index('src="/video.mp4"') < result.index('poster="/poster.jpg"')


def test_html_attribute_order_complex_real_world_example():
    """Test with a complex real-world example combining many attribute types."""
    html = (
        '<button '
        'style="background:blue" '
        'data-track="click-submit" '
        'aria-label="Submit form" '
        'onclick="handleSubmit()" '
        'type="submit" '
        'disabled '
        'form="contact-form" '
        'name="submit-btn" '
        'class="btn btn-primary" '
        'id="submit" '
        'title="Click to submit"'
        '>Submit</button>'
    )

    formatter = Html5Formatter(
        reorder_attributes_when={any_element(): html_attribute_order()}
    )

    result = formatter.format_str(html)

    # Expected order:
    # 0: id
    # 1: name
    # 2: class
    # 4: onclick (event handler)
    # 5: aria-label, title (semantic/accessibility)
    # 6: data-track, type, disabled, form (other/unknown)
    # 7: style

    assert result.index('id="submit"') < result.index('name="submit-btn"')
    assert result.index('name="submit-btn"') < result.index('class="btn btn-primary"')
    assert result.index('class="btn btn-primary"') < result.index('onclick="handleSubmit()"')
    assert result.index('onclick="handleSubmit()"') < result.index('aria-label="Submit form"')
    assert result.index('aria-label="Submit form"') < result.index('title="Click to submit"')
    assert result.index('title="Click to submit"') < result.index('data-track="click-submit"')
    assert result.index('data-track="click-submit"') < result.index('style="background:blue"')


def test_html_attribute_order_helper_function():
    """Test the reorderer function directly."""
    orderer = html_attribute_order()

    attrs = ["style", "alt", "class", "onclick", "src", "data-foo", "id", "name"]
    result = orderer(attrs)

    # Expected order: id, name, class, src, onclick, alt, data-foo, style
    assert list(result) == ["id", "name", "class", "src", "onclick", "alt", "data-foo", "style"]


def test_html_attribute_order_empty_attributes():
    """Test with element that has no attributes."""
    html = '<div></div>'

    formatter = Html5Formatter(
        reorder_attributes_when={any_element(): html_attribute_order()}
    )

    result = formatter.format_str(html)
    # Html5Formatter adds DOCTYPE and uses explicit tags for non-void elements
    assert '<div></div>' in result  # div is not a void element, needs both tags


def test_html_attribute_order_single_attribute():
    """Test with element that has only one attribute."""
    html = '<div id="main"></div>'

    formatter = Html5Formatter(
        reorder_attributes_when={any_element(): html_attribute_order()}
    )

    result = formatter.format_str(html)
    # Just verify the attribute is present - Html5Formatter adds DOCTYPE
    assert 'id="main"' in result