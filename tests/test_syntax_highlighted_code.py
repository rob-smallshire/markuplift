"""Tests for formatting syntax-highlighted code blocks with preserved whitespace."""

from approvaltests import verify  # type: ignore
from markuplift import Html5Formatter


def test_syntax_highlighted_code_preserves_whitespace():
    """Test that syntax-highlighted code in <pre> preserves its whitespace structure."""
    html = """<body><article><section><pre class="code contain" id="code"><span></span><span id="line-1"><span class="k">def</span><span class="w"> </span><span class="nf">nth_root</span><span class="p">(</span><span class="n">radicand</span><span class="p">,</span> <span class="n">n</span><span class="p">):</span>
</span>    <span class="fragment initial-highlighted-initial" data-fragment-group-id="single-return" id="line-2"><span class="k">return</span> <span class="n">radicand</span> <span class="o">**</span> <span class="p">(</span><span class="mi">1</span><span class="o">/</span><span class="n">n</span><span class="p">)</span>
</span><span id="line-3">
</span><span id="line-4">
</span><span id="line-5"><span class="k">def</span><span class="w"> </span><span class="nf">ordinal_suffix</span><span class="p">(</span><span class="n">value</span><span class="p">):</span>
</span>    <span id="line-6"><span class="n">s</span> <span class="o">=</span> <span class="nb">str</span><span class="p">(</span><span class="n">value</span><span class="p">)</span>
</span>    <span id="line-7"><span class="k">if</span> <span class="n">s</span><span class="o">.</span><span class="n">endswith</span><span class="p">(</span><span class="s1">'11'</span><span class="p">):</span>
</span>        <span class="fragment initial-highlighted-initial" data-fragment-group-id="multiple-return" id="line-8"><span class="k">return</span> <span class="s1">'th'</span>
</span>    <span id="line-9"><span class="k">elif</span> <span class="n">s</span><span class="o">.</span><span class="n">endswith</span><span class="p">(</span><span class="s1">'12'</span><span class="p">):</span>
</span>        <span class="fragment initial-highlighted-initial" data-fragment-group-id="multiple-return" id="line-10"><span class="k">return</span> <span class="s1">'th'</span>
</span>    <span id="line-11"><span class="k">elif</span> <span class="n">s</span><span class="o">.</span><span class="n">endswith</span><span class="p">(</span><span class="s1">'13'</span><span class="p">):</span>
</span>        <span class="fragment initial-highlighted-initial" data-fragment-group-id="multiple-return" id="line-12"><span class="k">return</span> <span class="s1">'th'</span>
</span></pre></section></article></body>"""

    # Html5Formatter now uses html_normalize_whitespace() by default which automatically
    # excludes whitespace-significant elements (<pre>, <style>, etc.) and their descendants
    formatter = Html5Formatter()

    result = formatter.format_str(html)
    verify(result)


def test_syntax_highlighted_code_with_attribute_reordering():
    """Test that syntax-highlighted code preserves whitespace while reordering attributes."""
    html = """<body><article><section><pre id="code" class="code contain"><span></span><span id="line-1"><span class="k">def</span><span class="w"> </span><span class="nf">nth_root</span><span class="p">(</span><span class="n">radicand</span><span class="p">):</span>
</span>    <span id="line-2" data-fragment-group-id="single-return" class="fragment initial-highlighted-initial"><span class="k">return</span> <span class="n">radicand</span>
</span></pre></section></article></body>"""

    # Html5Formatter now uses html_normalize_whitespace() by default which automatically
    # excludes whitespace-significant elements (<pre>, <style>, etc.) and their descendants
    formatter = Html5Formatter()

    result = formatter.format_str(html)
    verify(result)