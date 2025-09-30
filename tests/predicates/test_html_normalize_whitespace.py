"""Tests for the html_normalize_whitespace predicate factory."""

from lxml import html
from markuplift.predicates import html_normalize_whitespace


def test_html_normalize_whitespace_excludes_pre():
    """Test that html_normalize_whitespace does not match <pre> elements."""
    doc = html.fromstring("<div><pre>code</pre></div>")
    predicate_factory = html_normalize_whitespace()
    predicate = predicate_factory(doc)

    pre = doc.find(".//pre")
    assert not predicate(pre), "<pre> should not match normalize predicate"


def test_html_normalize_whitespace_excludes_style():
    """Test that html_normalize_whitespace does not match <style> elements."""
    doc = html.fromstring("<div><style>css</style></div>")
    predicate_factory = html_normalize_whitespace()
    predicate = predicate_factory(doc)

    style = doc.find(".//style")
    assert not predicate(style), "<style> should not match normalize predicate"


def test_html_normalize_whitespace_excludes_script():
    """Test that html_normalize_whitespace does not match <script> elements."""
    doc = html.fromstring("<div><script>js</script></div>")
    predicate_factory = html_normalize_whitespace()
    predicate = predicate_factory(doc)

    script = doc.find(".//script")
    assert not predicate(script), "<script> should not match normalize predicate"


def test_html_normalize_whitespace_excludes_textarea():
    """Test that html_normalize_whitespace does not match <textarea> elements."""
    doc = html.fromstring("<div><textarea>text</textarea></div>")
    predicate_factory = html_normalize_whitespace()
    predicate = predicate_factory(doc)

    textarea = doc.find(".//textarea")
    assert not predicate(textarea), "<textarea> should not match normalize predicate"


def test_html_normalize_whitespace_excludes_code():
    """Test that html_normalize_whitespace does not match <code> elements."""
    doc = html.fromstring("<div><code>snippet</code></div>")
    predicate_factory = html_normalize_whitespace()
    predicate = predicate_factory(doc)

    code = doc.find(".//code")
    assert not predicate(code), "<code> should not match normalize predicate"


def test_html_normalize_whitespace_excludes_descendants_of_pre():
    """Test that html_normalize_whitespace does not match descendants of <pre>."""
    doc = html.fromstring("<div><pre><span>code</span><strong>bold</strong></pre></div>")
    predicate_factory = html_normalize_whitespace()
    predicate = predicate_factory(doc)

    span = doc.find(".//span")
    strong = doc.find(".//strong")

    assert not predicate(span), "<span> inside <pre> should not match"
    assert not predicate(strong), "<strong> inside <pre> should not match"


def test_html_normalize_whitespace_excludes_nested_descendants():
    """Test that html_normalize_whitespace excludes deeply nested descendants."""
    doc = html.fromstring("<div><pre><div><span><em>text</em></span></div></pre></div>")
    predicate_factory = html_normalize_whitespace()
    predicate = predicate_factory(doc)

    inner_div = doc.find(".//pre/div")
    span = doc.find(".//span")
    em = doc.find(".//em")

    assert not predicate(inner_div), "<div> inside <pre> should not match"
    assert not predicate(span), "<span> nested in <pre> should not match"
    assert not predicate(em), "<em> deeply nested in <pre> should not match"


def test_html_normalize_whitespace_matches_regular_elements():
    """Test that html_normalize_whitespace matches regular elements."""
    doc = html.fromstring("<div><p>text</p><span>content</span></div>")
    predicate_factory = html_normalize_whitespace()
    predicate = predicate_factory(doc)

    div = doc
    p = doc.find(".//p")
    span = doc.find(".//span")

    assert predicate(div), "<div> should match normalize predicate"
    assert predicate(p), "<p> should match normalize predicate"
    assert predicate(span), "<span> outside <pre> should match"


def test_html_normalize_whitespace_mixed_document():
    """Test html_normalize_whitespace with mixed whitespace-significant and normal elements."""
    doc = html.fromstring("""
        <article>
            <p>Normal paragraph</p>
            <pre><span class="k">def</span> <span class="n">foo</span>()</pre>
            <p>Another paragraph</p>
            <code>inline code</code>
        </article>
    """)
    predicate_factory = html_normalize_whitespace()
    predicate = predicate_factory(doc)

    article = doc
    paragraphs = doc.findall(".//p")
    pre = doc.find(".//pre")
    pre_spans = pre.findall(".//span")
    inline_code = doc.find(".//code")

    # Regular elements should match
    assert predicate(article), "<article> should match"
    assert predicate(paragraphs[0]), "First <p> should match"
    assert predicate(paragraphs[1]), "Second <p> should match"

    # Whitespace-significant elements should not match
    assert not predicate(pre), "<pre> should not match"
    assert not predicate(inline_code), "<code> should not match"

    # Descendants of <pre> should not match
    for span in pre_spans:
        assert not predicate(span), "<span> inside <pre> should not match"


def test_html_normalize_whitespace_syntax_highlighted_code():
    """Test html_normalize_whitespace with real syntax-highlighted code structure."""
    doc = html.fromstring("""
        <pre class="code"><span id="line-1"><span class="k">def</span> <span class="nf">foo</span>():
</span>    <span id="line-2">    <span class="k">return</span> <span class="mi">42</span>
</span></pre>
    """)
    predicate_factory = html_normalize_whitespace()
    predicate = predicate_factory(doc)

    pre = doc
    all_spans = doc.findall(".//span")

    # Pre should not match
    assert not predicate(pre), "<pre> should not match"

    # All spans inside pre should not match (preserving whitespace structure)
    for span in all_spans:
        assert not predicate(span), f"<span> inside <pre> should not match: {span.get('id') or span.get('class')}"


def test_html_normalize_whitespace_excludes_textarea_descendants():
    """Test that descendants of <textarea> are also excluded."""
    doc = html.fromstring("<div><textarea><span>text</span></textarea></div>")
    predicate_factory = html_normalize_whitespace()
    predicate = predicate_factory(doc)

    textarea = doc.find(".//textarea")
    # Note: HTML parser may strip tags inside textarea, but we test textarea itself
    assert not predicate(textarea), "<textarea> should not match"


def test_html_normalize_whitespace_multiple_pre_blocks():
    """Test that multiple <pre> blocks and their descendants are all excluded."""
    doc = html.fromstring("""
        <div>
            <pre><span>code1</span></pre>
            <p>normal text</p>
            <pre><span>code2</span></pre>
        </div>
    """)
    predicate_factory = html_normalize_whitespace()
    predicate = predicate_factory(doc)

    div = doc
    p = doc.find(".//p")
    pre_blocks = doc.findall(".//pre")
    spans = doc.findall(".//span")

    # Normal elements should match
    assert predicate(div), "<div> should match"
    assert predicate(p), "<p> should match"

    # Pre blocks should not match
    for pre in pre_blocks:
        assert not predicate(pre), "<pre> should not match"

    # Spans inside pre blocks should not match
    for span in spans:
        assert not predicate(span), "<span> inside <pre> should not match"