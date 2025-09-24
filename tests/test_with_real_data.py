import jsbeautifier

from markuplift import DocumentFormatter
from markuplift.annotation import INLINE_TYPE_ANNOTATION


def test_generated_html():
    original = (
"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"/>
    <link rel="stylesheet" href="clock.css"/>
    <link rel="stylesheet" href="colors.css"/>
    <link rel="stylesheet" href="effects.css"/>
    <link rel="stylesheet" href="font-families.css"/>
    <link rel="stylesheet" href="font-variables.css"/>
    <link rel="stylesheet" href="pygments.css"/>
    <link rel="stylesheet" href="slides.css"/>
    <link rel="stylesheet" href="terminal.css"/>




    <script type="module" src="animation.mjs"></script>
    <script type="module" src="annotations.mjs"></script>
    <script type="module" src="balancetext.mjs"></script>
    <script type="module" src="case.mjs"></script>
    <script type="module" src="clapperboards.mjs"></script>
    <script type="module" src="clock.mjs"></script>
    <script type="module" src="effects.mjs"></script>
    <script type="module" src="extract-css.mjs"></script>
    <script type="module" src="key-value-store.mjs"></script>
    <script type="module" src="keypress.mjs"></script>
    <script type="module" src="logging.mjs"></script>
    <script type="module" src="onload.mjs"></script>
    <script type="module" src="optional-background.mjs"></script>
    <script type="module" src="scrolling.mjs"></script>
    <script type="module" src="sizing.mjs"></script>
    <script type="module" src="three-state-animation.mjs"></script>
    <script type="module" src="visning.mjs"></script>
    <script type="module" src="wait.mjs"></script>


    <link rel="icon" href="data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2016%2016'%3E%3Ctext%20x='0'%20y='14'%3E🦄%3C/text%3E%3C/svg%3E" type="image/svg+xml" />
    <title>
    Title goes here
</title>
</head>
<body class="visning-optional-background">
    <div id="clapperboard"></div>
    <article class="icon-on-left-container" style="--flair-color: #238bbf;">

        <header class="title">
            <h1>Title goes here</h1>

        </header>

        <div class="icon-on-left-icon-section">
            <img src="x-ray-primary-regular-alpha-512x512.png" alt="pizza"/>
        </div>
        <div class="icon-on-left-content-section" id="wait-for-this-element">
            <section style="">
                <p>This XHTML document must have a section root element without attributes.</p>
    <p>The contents of the root section can be arbitrary XHTML elements, with a strong preference for:</p>
    <ul>
        <li>Semantic HTML elements such as this list</li>
        <li>Or <code>strong</code> and <code>em</code> tags <mark>inline tags</mark> for example.</li>
    </ul>
            </section>
        </div>
    </article>




    <div id="clock"></div>

    <script id="page-data-script">
        window.pageData = {
    "fragmentGroupIdBuildOrder": [],
    "showHtmlTimecode": false,
    "skipLastFragmentOutEvent": false
}
    </script>

</body>
</html>"""
    )

    def is_block(e):
        return (
            (e.tag in {"html", "head", "meta", "link", "body", "div", "article", "section", "header", "p", "ul", "li", "script", "h1", "h2", "h3", "title"})
            or
            (e.tag in {"img"} and (e.getparent() is not None) and is_block(e.getparent()))
        )

    formatter = DocumentFormatter(
        block_predicate=is_block,
        strip_whitespace_predicate=lambda e: e.tag in {"title", "h1", "h2", "h3", "p", "li"},
        preserve_whitespace_predicate=lambda e: e.tag in {"style", "pre"},
        wrap_attributes_predicate=lambda e: e.tag in {"link"} and sum(1 for k in e.attrib if not k.startswith("_")) >= 3,
        text_content_formatters={
            lambda e: e.tag == "title": lambda text, formatter, level: (text or "").strip(),
            lambda e: e.tag == "script": beautify_js
        }
    )
    actual = formatter.format_str(original)

    expected = ("""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="stylesheet" href="clock.css" />
    <link rel="stylesheet" href="colors.css" />
    <link rel="stylesheet" href="effects.css" />
    <link rel="stylesheet" href="font-families.css" />
    <link rel="stylesheet" href="font-variables.css" />
    <link rel="stylesheet" href="pygments.css" />
    <link rel="stylesheet" href="slides.css" />
    <link rel="stylesheet" href="terminal.css" />
    <script type="module" src="animation.mjs" />
    <script type="module" src="annotations.mjs" />
    <script type="module" src="balancetext.mjs" />
    <script type="module" src="case.mjs" />
    <script type="module" src="clapperboards.mjs" />
    <script type="module" src="clock.mjs" />
    <script type="module" src="effects.mjs" />
    <script type="module" src="extract-css.mjs" />
    <script type="module" src="key-value-store.mjs" />
    <script type="module" src="keypress.mjs" />
    <script type="module" src="logging.mjs" />
    <script type="module" src="onload.mjs" />
    <script type="module" src="optional-background.mjs" />
    <script type="module" src="scrolling.mjs" />
    <script type="module" src="sizing.mjs" />
    <script type="module" src="three-state-animation.mjs" />
    <script type="module" src="visning.mjs" />
    <script type="module" src="wait.mjs" />
    <link
      rel="icon"
      href="data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2016%2016'%3E%3Ctext%20x='0'%20y='14'%3E🦄%3C/text%3E%3C/svg%3E"
      type="image/svg+xml"
    />
    <title>Title goes here</title>
  </head>
  <body class="visning-optional-background">
    <div id="clapperboard" />
    <article class="icon-on-left-container" style="--flair-color: #238bbf;">
      <header class="title">
        <h1>Title goes here</h1>
      </header>
      <div class="icon-on-left-icon-section">
        <img src="x-ray-primary-regular-alpha-512x512.png" alt="pizza" />
      </div>
      <div class="icon-on-left-content-section" id="wait-for-this-element">
        <section style="">
          <p>This XHTML document must have a section root element without attributes.</p>
          <p>The contents of the root section can be arbitrary XHTML elements, with a strong preference for:</p>
          <ul>
            <li>Semantic HTML elements such as this list</li>
            <li>Or <code>strong</code> and <code>em</code> tags <mark>inline tags</mark> for example.</li>
          </ul>
        </section>
      </div>
    </article>
    <div id="clock" />
    <script id="page-data-script">
      window.pageData = {
        "fragmentGroupIdBuildOrder": [],
        "showHtmlTimecode": false,
        "skipLastFragmentOutEvent": false
      }
    </script>
  </body>
</html>""")
    assert actual == expected



def test_xml_doc():
    original = (
"""<?xml version='1.0' encoding='utf-8'?>
<?xml-model href="urn:demon-schemas:chunked-content.rng" type="application/relax-ng+xml" schematypens="http://relaxng.org/ns/structure/1.0"?>
<chunked-content>
    <titles><title>Title goes here</title>
    </titles><chunks><chunk class="hidden-visible-visible fragment" data-fragment-group-id="echo">
        <heading>Talking point one</heading>
        <paragraphs><p>Be concise and keep the text to four lines or fewer.</p>
    </paragraphs></chunk>
    <chunk class="hidden-visible-visible fragment" data-fragment-group-id="foxtrot">
        <heading>Talking point two</heading>
        <paragraphs><p>Be concise and keep the text to four lines or fewer.</p>
    </paragraphs></chunk>
    <chunk class="hidden-visible-visible fragment" data-fragment-group-id="delta">
        <heading><em>Talking point</em> three</heading>
        <paragraphs><p>Be <mark>concise</mark> and keep the text to <mark><strong>four</strong> lines</mark> or fewer.</p>
    </paragraphs></chunk>
</chunks></chunked-content>
"""
    )

    formatter = DocumentFormatter(
        block_predicate=lambda e: e.tag in {"chunked-content", "titles", "title", "chunks", "chunk", "heading", "paragraphs", "p"},
        strip_whitespace_predicate=lambda e: e.tag in {"supertitle", "title", "subtitle"},
        preserve_whitespace_predicate=lambda e: e.tag in {"style", "pre"},
        wrap_attributes_predicate=lambda e: len(e.attrib) >= 2,
        default_type=INLINE_TYPE_ANNOTATION,
    )
    actual = formatter.format_str(original)

    expected = ("""<?xml-model href="urn:demon-schemas:chunked-content.rng" type="application/relax-ng+xml" schematypens="http://relaxng.org/ns/structure/1.0"?>
<chunked-content>
  <titles>
    <title>Title goes here</title>
  </titles>
  <chunks>
    <chunk
      class="hidden-visible-visible fragment"
      data-fragment-group-id="echo"
    >
      <heading>Talking point one</heading>
      <paragraphs>
        <p>Be concise and keep the text to four lines or fewer.</p>
      </paragraphs>
    </chunk>
    <chunk
      class="hidden-visible-visible fragment"
      data-fragment-group-id="foxtrot"
    >
      <heading>Talking point two</heading>
      <paragraphs>
        <p>Be concise and keep the text to four lines or fewer.</p>
      </paragraphs>
    </chunk>
    <chunk
      class="hidden-visible-visible fragment"
      data-fragment-group-id="delta"
    >
      <heading><em>Talking point</em> three</heading>
      <paragraphs>
        <p>Be <mark>concise</mark> and keep the text to <mark><strong>four</strong> lines</mark> or fewer.</p>
      </paragraphs>
    </chunk>
  </chunks>
</chunked-content>""")
    assert actual == expected



def beautify_js(text: str, formatter: DocumentFormatter, physical_indent_level: int) -> str:

    text = text or ""
    if text.strip() == "":
        return ""

    options = jsbeautifier.BeautifierOptions(
        dict(
            indent_size=formatter.indent_size,
            indent_char=formatter.indent_char,
            preserve_newlines=True,
            max_preserve_newlines=2,
            space_in_empty_paren=False,
        )
    )

    pretty_text = jsbeautifier.beautify(text, options)
    lines = pretty_text.splitlines()
    indent = formatter.one_indent * (physical_indent_level + 1)
    indented_lines = [indent + line if line.strip() != "" else line for line in lines]
    indented_text = "\n".join(indented_lines)
    return "\n" + indented_text + "\n" + formatter.one_indent * physical_indent_level


if __name__ == "__main__":
    test_generated_html()