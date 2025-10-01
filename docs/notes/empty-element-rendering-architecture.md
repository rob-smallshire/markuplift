# Empty Element Rendering Architecture: Design Exploration

**Date:** 2025-10-01
**Context:** Post-implementation analysis of `EmptyElementStrategy` pattern
**Purpose:** Document architectural exploration for future XHTML support and extensibility decisions

## Table of Contents

1. [Current Implementation](#current-implementation)
2. [The Architectural Concern](#the-architectural-concern)
3. [Design Space Exploration](#design-space-exploration)
4. [The Visitor/Renderer Pattern (Deep Dive)](#the-visitorrenderer-pattern-deep-dive)
5. [Trade-off Analysis](#trade-off-analysis)
6. [XHTML Considerations](#xhtml-considerations)
7. [Recommendations](#recommendations)

---

## Current Implementation

### Overview

The current implementation uses an **enum-based strategy pattern** where `DocumentFormatter` asks the strategy about element state and then decides what to do.

### Code Structure

```python
# empty_element.py
class EmptyElementTagStyle(Enum):
    EXPLICIT_TAGS = "explicit"      # <tag></tag>
    SELF_CLOSING_TAG = "self_closing"  # <tag />
    VOID_TAG = "void"                # <tag>

class EmptyElementStrategy(ABC):
    @abstractmethod
    def tag_style(self, element: Element) -> EmptyElementTagStyle:
        """Determine how to render this empty element."""
        pass

class XmlEmptyElementStrategy(EmptyElementStrategy):
    def tag_style(self, element: Element) -> EmptyElementTagStyle:
        return EmptyElementTagStyle.SELF_CLOSING_TAG

class Html5EmptyElementStrategy(EmptyElementStrategy):
    _HTML5_VOID_ELEMENTS = frozenset({'br', 'img', 'hr', ...})

    def tag_style(self, element: Element) -> EmptyElementTagStyle:
        if element.tag in self._HTML5_VOID_ELEMENTS:
            return EmptyElementTagStyle.VOID_TAG
        return EmptyElementTagStyle.EXPLICIT_TAGS
```

### Usage in DocumentFormatter

```python
# document_formatter.py (simplified)
def _format_element(self, annotations, element, parts):
    for event, node in etree.iterwalk(element):
        if event == "start":
            parts.append(f"<{node.tag}")

            # ... render attributes ...

            # Determine tag closing
            is_empty = self._is_empty_element(annotations, node)
            tag_style = self._empty_element_strategy.tag_style(node) if is_empty else None

            # DocumentFormatter interprets the enum and decides what to do
            if is_empty and tag_style in (EmptyElementTagStyle.SELF_CLOSING_TAG,
                                         EmptyElementTagStyle.VOID_TAG):
                if tag_style == EmptyElementTagStyle.SELF_CLOSING_TAG:
                    if not must_wrap_attributes:
                        parts.append(" ")
                    parts.append("/")
                # VOID_TAG: just close with >

            parts.append(">")

            # Content - complex predicate
            if not (is_empty and tag_style in (EmptyElementTagStyle.SELF_CLOSING_TAG,
                                              EmptyElementTagStyle.VOID_TAG)):
                if text := self._text_content(annotations, node):
                    parts.append(escaped_text)

        elif event == "end":
            # Similar complex logic for closing tags
            is_empty = self._is_empty_element(annotations, node)
            tag_style = self._empty_element_strategy.tag_style(node) if is_empty else None

            if not (is_empty and tag_style in (EmptyElementTagStyle.SELF_CLOSING_TAG,
                                              EmptyElementTagStyle.VOID_TAG)):
                parts.append(f"</{node.tag}>")
```

### Strengths

1. **Simple strategy interface** - Single method returning an enum
2. **Clear enum semantics** - Three distinct rendering modes
3. **Works correctly** - All 616 tests pass
4. **Easy to understand** - Straightforward mapping from element to style

### Weaknesses

1. **"Ask, Don't Tell"** - DocumentFormatter asks for state, then decides actions
2. **Knowledge in wrong place** - DocumentFormatter knows how to interpret each enum value
3. **Complex predicates** - Lines like `if not (is_empty and tag_style in (...))` are hard to parse
4. **Tight coupling** - Adding new tag styles requires changes to both strategy and formatter
5. **Violates Single Responsibility** - DocumentFormatter handles both formatting logic AND tag style interpretation

---

## The Architectural Concern

### The "Tell, Don't Ask" Principle

**Problem:** DocumentFormatter is asking the strategy "what should I do?" and then deciding the behavior itself.

```python
# Current: Ask
tag_style = strategy.tag_style(element)
if tag_style == SELF_CLOSING_TAG:
    parts.append(" /")
elif tag_style == VOID_TAG:
    # do nothing special
elif tag_style == EXPLICIT_TAGS:
    # will add closing tag later
```

**Ideal:** DocumentFormatter should tell the strategy "do your job" and let it handle the details.

```python
# Better: Tell
renderer = strategy.get_renderer(element, is_empty)
parts.append(renderer.render_opening_tag(tag_name, attributes_str))
```

### Where Knowledge Should Live

**Current state:**
- **Strategy knows:** Which elements are void, which should self-close
- **DocumentFormatter knows:** What each tag style means, how to render it

**Desired state:**
- **Strategy knows:** Which elements are void, which should self-close, AND how to render them
- **DocumentFormatter knows:** Only formatting/whitespace concerns, delegates all tag rendering

### The Complex Predicates Problem

These predicates are difficult to understand at a glance:

```python
# Add content?
if not (is_empty and tag_style in (SELF_CLOSING_TAG, VOID_TAG)):

# Add closing tag?
if not (is_empty and tag_style in (SELF_CLOSING_TAG, VOID_TAG)):
```

They're doing double-duty:
1. Checking if element is empty
2. Checking if the style needs single-tag rendering

This could be simpler if the strategy just told us: "yes, render content" or "no closing tag needed".

---

## Design Space Exploration

We explored four main alternative approaches:

### Option 1: Strategy Renders Complete Tags

**Idea:** Strategy returns fully-formed tag strings.

```python
class EmptyElementStrategy(ABC):
    @abstractmethod
    def render_opening(self, element: Element, attributes_str: str,
                       is_empty: bool, must_wrap_attrs: bool) -> str:
        """Return complete opening tag with closing syntax."""
        pass

    @abstractmethod
    def needs_closing_tag(self, element: Element, is_empty: bool) -> bool:
        """Return True if closing tag is needed."""
        pass
```

**Pros:**
- Clean delegation - strategy owns rendering
- DocumentFormatter just calls methods

**Cons:**
- Strategy needs to know about attribute wrapping indentation
- Mixing concerns - strategy handles both policy and formatting details
- Hard to test - needs full formatting context

**Verdict:** Too much responsibility in strategy.

---

### Option 2: Two-Phase Strategy

**Idea:** Strategy provides answers to specific questions DocumentFormatter asks.

```python
class EmptyElementStrategy(ABC):
    @abstractmethod
    def opening_suffix(self, element: Element, is_empty: bool,
                       attrs_wrapped: bool) -> str:
        """Complete suffix for opening tag including spacing."""
        pass

    @abstractmethod
    def needs_closing_tag(self, element: Element, is_empty: bool) -> bool:
        """Whether closing tag is needed."""
        pass
```

**Implementation:**
```python
class XmlEmptyElementStrategy:
    def opening_suffix(self, element, is_empty, attrs_wrapped):
        if is_empty:
            return " />" if not attrs_wrapped else "/>"
        return ">"

    def needs_closing_tag(self, element, is_empty):
        return not is_empty

class Html5EmptyElementStrategy:
    def opening_suffix(self, element, is_empty, attrs_wrapped):
        return ">"  # Always just >, never with /

    def needs_closing_tag(self, element, is_empty):
        if is_empty and element.tag in self._HTML5_VOID_ELEMENTS:
            return False
        return True
```

**Usage:**
```python
# Opening tag close
parts.append(
    self._empty_element_strategy.opening_suffix(node, is_empty, must_wrap_attributes)
)

# Content (only if not empty)
if not is_empty:
    if text := self._text_content(annotations, node):
        parts.append(escaped_text)

# Closing tag
if self._empty_element_strategy.needs_closing_tag(node, is_empty):
    parts.append(f"</{node.tag}>")
```

**Pros:**
- Simpler predicates in DocumentFormatter
- Strategy encapsulates tag rendering decisions
- Clear separation of concerns
- Still relatively simple API

**Cons:**
- Still passing context (`is_empty`, `attrs_wrapped`) to strategy
- Two method calls per element (opening, closing)
- String manipulation split between formatter and strategy

**Verdict:** Cleaner than current, but not ideal.

---

### Option 3: Strategy Owns Empty Check

**Idea:** Let strategy define what "empty" means for its format.

```python
class EmptyElementStrategy(ABC):
    @abstractmethod
    def opening_suffix(self, element: Element, has_content: bool,
                       must_wrap_attrs: bool) -> str:
        pass

    @abstractmethod
    def needs_closing_tag(self, element: Element, has_content: bool) -> bool:
        pass
```

**Analysis:**
This doesn't really help - we just renamed `is_empty` to `has_content`. The formatter must still determine emptiness because only it knows about text transformations, whitespace stripping, etc.

**Verdict:** No real benefit, adds confusion about responsibility.

---

### Option 4: Visitor Pattern with Tag Renderers

**Idea:** Strategy returns a renderer object that knows how to render tags.

See [next section](#the-visitorrenderer-pattern-deep-dive) for detailed exploration.

---

## The Visitor/Renderer Pattern (Deep Dive)

### Core Concept

**Insight:** DocumentFormatter has already done all the work of rendering attributes. It has a complete attribute string ready. Why not hand that whole thing to a specialized renderer?

### Architecture

```python
# Three-layer architecture:
# 1. TagRenderer - knows HOW to render specific tag types
# 2. EmptyElementStrategy - knows WHICH renderer to use
# 3. DocumentFormatter - coordinates everything

class TagRenderer(ABC):
    """Renders opening and closing tags for an element.

    Responsibilities:
    - Know how to format opening tag with attributes
    - Know whether closing tag is needed
    - Handle spacing/formatting for its style
    """

    @abstractmethod
    def render_opening_tag(self, tag_name: str, attributes_str: str,
                          closing_indent: str = "") -> str:
        """Render complete opening tag.

        Args:
            tag_name: Element tag name (e.g., 'div', 'br')
            attributes_str: Complete rendered attributes including spacing
                          (e.g., ' class="foo" id="bar"')
            closing_indent: Indentation for closing '/>' in wrapped case

        Returns:
            Complete opening tag
        """
        pass

    @abstractmethod
    def render_closing_tag(self, tag_name: str) -> str:
        """Render closing tag if needed.

        Returns:
            Closing tag (e.g., '</div>') or empty string if not needed
        """
        pass
```

### Renderer Implementations

```python
class ExplicitTagsRenderer(TagRenderer):
    """Both opening and closing tags, always.

    Used for:
    - All non-empty elements
    - HTML5 non-void empty elements (script, div, etc.)
    """

    def render_opening_tag(self, tag_name: str, attributes_str: str,
                          closing_indent: str = "") -> str:
        return f"<{tag_name}{attributes_str}>"

    def render_closing_tag(self, tag_name: str) -> str:
        return f"</{tag_name}>"


class SelfClosingTagRenderer(TagRenderer):
    """XML-style self-closing with slash.

    Used for:
    - XML empty elements

    Handles two cases:
    - Inline attributes: <tag attr="x" />
    - Wrapped attributes: <tag\n  attr="x"\n/>
    """

    def render_opening_tag(self, tag_name: str, attributes_str: str,
                          closing_indent: str = "") -> str:
        if closing_indent:
            # Wrapped attributes: slash on its own line
            return f"<{tag_name}{attributes_str}\n{closing_indent}/>"
        else:
            # Inline attributes: space before slash
            return f"<{tag_name}{attributes_str} />"

    def render_closing_tag(self, tag_name: str) -> str:
        return ""  # No closing tag for self-closing


class VoidTagRenderer(TagRenderer):
    """HTML5 void elements - single tag, no slash.

    Used for:
    - HTML5 void elements (br, img, hr, input, etc.)

    Just closes with '>', no special handling.
    """

    def render_opening_tag(self, tag_name: str, attributes_str: str,
                          closing_indent: str = "") -> str:
        return f"<{tag_name}{attributes_str}>"

    def render_closing_tag(self, tag_name: str) -> str:
        return ""  # No closing tag for void elements
```

### Strategy Implementation

```python
class EmptyElementStrategy(ABC):
    """Strategy that provides appropriate renderer for elements."""

    @abstractmethod
    def get_renderer(self, element: Element, is_empty: bool) -> TagRenderer:
        """Get the appropriate tag renderer for this element/state.

        Args:
            element: The element being rendered
            is_empty: Whether element has no content/children

        Returns:
            TagRenderer instance appropriate for this element
        """
        pass


class XmlEmptyElementStrategy(EmptyElementStrategy):
    """XML strategy: empty elements self-close, others use explicit tags."""

    def __init__(self):
        self._explicit = ExplicitTagsRenderer()
        self._self_closing = SelfClosingTagRenderer()

    def get_renderer(self, element: Element, is_empty: bool) -> TagRenderer:
        return self._self_closing if is_empty else self._explicit


class Html5EmptyElementStrategy(EmptyElementStrategy):
    """HTML5 strategy: void elements use void syntax, others explicit."""

    _HTML5_VOID_ELEMENTS = frozenset({
        'area', 'base', 'br', 'col', 'embed', 'hr', 'img',
        'input', 'link', 'meta', 'source', 'track', 'wbr'
    })

    def __init__(self):
        self._explicit = ExplicitTagsRenderer()
        self._void = VoidTagRenderer()

    def get_renderer(self, element: Element, is_empty: bool) -> TagRenderer:
        if is_empty and element.tag in self._HTML5_VOID_ELEMENTS:
            return self._void
        return self._explicit
```

### Usage in DocumentFormatter

```python
def _format_element(self, annotations, element, parts):
    for event, node in etree.iterwalk(element, events=("start", "end", ...)):
        if event == "start":
            # Build complete attribute string
            attr_parts = []
            must_wrap = self._must_wrap_attributes(node)
            physical_level = annotations.annotation(node, "physical_level", 0)

            if must_wrap:
                spacer = "\n" + self._one_indent * (physical_level + 1)
            else:
                spacer = " "

            for k in attribute_names:
                # ... format attribute k ...
                attr_parts.append(f"{spacer}{k}={escaped_value}")

            attributes_str = "".join(attr_parts)
            closing_indent = self._one_indent * physical_level if must_wrap else ""

            # Get renderer and render opening tag
            is_empty = self._is_empty_element(annotations, node)
            renderer = self._empty_element_strategy.get_renderer(node, is_empty)

            opening_tag = renderer.render_opening_tag(
                node.tag, attributes_str, closing_indent
            )
            parts.append(opening_tag)

            # Content (only if not empty - simple check!)
            if not is_empty:
                if text := self._text_content(annotations, node):
                    parts.append(self._escape_text_content(text))

        elif event == "end":
            # Get renderer and render closing tag
            is_empty = self._is_empty_element(annotations, node)
            renderer = self._empty_element_strategy.get_renderer(node, is_empty)

            closing_tag = renderer.render_closing_tag(node.tag)
            if closing_tag:
                parts.append(closing_tag)
```

### Benefits of Visitor/Renderer Pattern

1. **Single Responsibility**
   - `TagRenderer`: Knows how to format tags
   - `EmptyElementStrategy`: Knows which renderer to use
   - `DocumentFormatter`: Coordinates, handles content/whitespace

2. **Open/Closed Principle**
   - Add new tag styles by creating new `TagRenderer` classes
   - No changes to `DocumentFormatter` needed

3. **Tell, Don't Ask**
   - DocumentFormatter tells renderer: "render this"
   - Doesn't ask: "what should I do?"

4. **Simple Predicates**
   - `if not is_empty:` - clear and simple
   - No complex enum checks

5. **Easy Testing**
   - Test renderers with simple strings
   - Test strategies with mock elements
   - No need for full formatter context

6. **Extensibility**
   - XHTML? New `XhtmlVoidTagRenderer` with ` />`
   - Custom format? Implement `TagRenderer` interface

### Challenges

1. **Attribute String Complexity**
   - Need to decide: does `attributes_str` include trailing whitespace?
   - Current solution: pass `closing_indent` separately

2. **More Classes**
   - Current: 2 strategies, 1 enum (3 components)
   - Visitor: 2 strategies, 3 renderers (5 components)

3. **Indirect Behavior**
   - Current: see all logic in DocumentFormatter
   - Visitor: must look in renderer to see what happens

4. **Renderer Reuse**
   - Strategies share renderer instances (flyweight pattern)
   - Need to ensure renderers are stateless

---

## Trade-off Analysis

### Complexity

| Aspect | Current (Enum) | Visitor/Renderer |
|--------|---------------|------------------|
| **Lines of code** | ~150 | ~200 |
| **Number of classes** | 3 (1 enum, 2 strategies) | 5 (3 renderers, 2 strategies) |
| **Conceptual complexity** | Medium (enum interpretation) | Medium (indirection through renderer) |
| **Logic location** | Spread between formatter and strategy | Concentrated in renderers |

### Maintainability

| Aspect | Current (Enum) | Visitor/Renderer |
|--------|---------------|------------------|
| **Adding new style** | Modify enum, strategy, AND formatter | Add new renderer, update strategy |
| **Finding tag logic** | Split between formatter and strategy | All in renderer class |
| **Predicate clarity** | Complex boolean expressions | Simple boolean expressions |
| **Coupling** | Tight (formatter knows enum values) | Loose (formatter knows interface) |

### Testability

| Aspect | Current (Enum) | Visitor/Renderer |
|--------|---------------|------------------|
| **Unit test strategy** | Easy (return enum value) | Easy (return renderer) |
| **Unit test formatter** | Complex (need full setup) | Easy (mock renderer) |
| **Unit test renderers** | N/A (logic in formatter) | Easy (pass strings) |
| **Integration tests** | Required for correctness | Nice to have |

### Extensibility

| Aspect | Current (Enum) | Visitor/Renderer |
|--------|---------------|------------------|
| **XHTML support** | Add enum value, update formatter | Add XhtmlVoidTagRenderer |
| **Custom formats** | Hard (tied to enum) | Easy (implement TagRenderer) |
| **Per-element rendering** | Hard (strategy sees element) | Medium (renderer doesn't see element) |
| **Format variations** | Hard (need new enum values) | Easy (new renderer classes) |

### Performance

Both approaches have similar performance:
- Current: enum comparison in Python
- Visitor: virtual method dispatch in Python

Negligible difference in practice.

---

## XHTML Considerations

### XHTML Requirements

XHTML is XML-compliant HTML that requires:
- All empty void elements must use self-closing syntax: `<br />`
- Non-void empty elements still use explicit tags: `<script></script>`

### With Current Implementation

Would need to add:
1. New enum value: `EmptyElementTagStyle.XHTML_VOID_TAG`
2. New strategy: `XhtmlEmptyElementStrategy`
3. Update DocumentFormatter to handle new enum value

```python
# document_formatter.py additions
if tag_style == EmptyElementTagStyle.XHTML_VOID_TAG:
    parts.append(" />")  # Different from VOID_TAG (no slash) and SELF_CLOSING_TAG (context)
```

**Problem:** DocumentFormatter now knows about 4 different tag styles and their specific formatting rules.

### With Visitor/Renderer Pattern

Would need to add:
1. New renderer: `XhtmlVoidTagRenderer`
2. New strategy: `XhtmlEmptyElementStrategy`
3. No changes to DocumentFormatter

```python
class XhtmlVoidTagRenderer(TagRenderer):
    """XHTML void elements - self-closing with space and slash."""

    def render_opening_tag(self, tag_name: str, attributes_str: str,
                          closing_indent: str = "") -> str:
        if closing_indent:
            return f"<{tag_name}{attributes_str}\n{closing_indent}/>"
        else:
            return f"<{tag_name}{attributes_str} />"

    def render_closing_tag(self, tag_name: str) -> str:
        return ""

class XhtmlEmptyElementStrategy(EmptyElementStrategy):
    _XHTML_VOID_ELEMENTS = Html5EmptyElementStrategy._HTML5_VOID_ELEMENTS

    def __init__(self):
        self._explicit = ExplicitTagsRenderer()
        self._xhtml_void = XhtmlVoidTagRenderer()

    def get_renderer(self, element: Element, is_empty: bool) -> TagRenderer:
        if is_empty and element.tag in self._XHTML_VOID_ELEMENTS:
            return self._xhtml_void
        return self._explicit
```

**Advantage:** DocumentFormatter unchanged. All XHTML knowledge in renderer and strategy.

---

## Recommendations

### When to Keep Current Implementation

**Keep the current enum-based approach if:**

1. ✅ Only need 2-3 tag rendering styles
2. ✅ No plans for format variations (XHTML, custom formats)
3. ✅ Team prefers simpler mental model
4. ✅ Test coverage is comprehensive (catching changes to formatter logic)
5. ✅ Performance is not a concern (both approaches similar)

**Current state:** This describes the project now. **Keep current implementation.**

### When to Refactor to Visitor/Renderer

**Refactor to visitor pattern when:**

1. ❌ Adding XHTML support (4th tag style)
2. ❌ Adding custom format support
3. ❌ Finding bugs related to complex predicates
4. ❌ Team grows and needs better separation of concerns
5. ❌ Need to unit test tag rendering in isolation

**Trigger points for refactoring:**
- When adding XHTML formatter
- When adding 3rd party format extensions
- When onboarding new contributors who struggle with current logic

### Incremental Refactoring Path

If/when refactoring to visitor pattern:

**Phase 1: Extract renderers (current behavior)**
1. Create `TagRenderer` interface
2. Create `ExplicitTagsRenderer`, `SelfClosingTagRenderer`, `VoidTagRenderer`
3. Keep enum-based strategy
4. Update DocumentFormatter to use renderers based on enum
5. **All tests still pass, behavior unchanged**

**Phase 2: Move decision to strategy**
1. Update `EmptyElementStrategy` to return `TagRenderer`
2. Update strategies to instantiate and return appropriate renderer
3. Remove enum from public API
4. **All tests still pass, behavior unchanged**

**Phase 3: Simplify DocumentFormatter**
1. Remove complex enum-based predicates
2. Use simple `if not is_empty:` checks
3. **All tests still pass, simpler code**

### Code Quality Improvements (Current Implementation)

Even without refactoring, improve current implementation:

**1. Add assertions for invariants:**
```python
# After line 444
if is_empty:
    assert tag_style is not None, "tag_style must be set for empty elements"
    assert isinstance(tag_style, EmptyElementTagStyle), \
           f"tag_style must be EmptyElementTagStyle, got {type(tag_style)}"
```

**2. Extract predicates to named functions:**
```python
def _should_include_content(self, is_empty: bool, tag_style: EmptyElementTagStyle | None) -> bool:
    """Determine if element content should be included in output."""
    return not is_empty or tag_style == EmptyElementTagStyle.EXPLICIT_TAGS

def _needs_closing_tag(self, is_empty: bool, tag_style: EmptyElementTagStyle | None) -> bool:
    """Determine if closing tag is needed."""
    return not (is_empty and tag_style in (EmptyElementTagStyle.SELF_CLOSING_TAG,
                                          EmptyElementTagStyle.VOID_TAG))
```

**3. Add comprehensive documentation:**
```python
# At line 442
# Determine tag rendering strategy
# - Empty elements: consult strategy for appropriate style
# - Non-empty elements: always use explicit tags
# Strategy returns:
#   - SELF_CLOSING_TAG: XML empty elements (add space and /)
#   - VOID_TAG: HTML5 void elements (just >)
#   - EXPLICIT_TAGS: HTML5 non-void empty elements (need </tag>)
```

---

## Conclusion

The current enum-based implementation is **appropriate for the current requirements** (XML and HTML5 support). It works correctly, has full test coverage, and is understood by the current maintainer.

However, the visitor/renderer pattern represents a **more extensible and maintainable** architecture that would better support:
- XHTML implementation
- Custom format extensions
- Team growth and onboarding
- Isolated unit testing

**Recommendation:** Keep current implementation, but **revisit this document when adding XHTML support**. At that point, the benefits of refactoring will outweigh the costs.

### Next Steps

1. ✅ Keep current implementation for now
2. 📝 Document code quality improvements (assertions, named predicates)
3. 🎯 Trigger point: Implement visitor pattern when adding XHTML support
4. 📚 Use this document as reference for that refactoring

---

## Appendix: Full Example Comparison

### Current Implementation (Enum-Based)

```python
# Strategy returns enum
tag_style = self._empty_element_strategy.tag_style(node) if is_empty else None

# DocumentFormatter interprets enum
if is_empty and tag_style in (EmptyElementTagStyle.SELF_CLOSING_TAG,
                             EmptyElementTagStyle.VOID_TAG):
    if tag_style == EmptyElementTagStyle.SELF_CLOSING_TAG:
        if not must_wrap_attributes:
            parts.append(" ")
        parts.append("/")

parts.append(">")

if not (is_empty and tag_style in (EmptyElementTagStyle.SELF_CLOSING_TAG,
                                  EmptyElementTagStyle.VOID_TAG)):
    if text := self._text_content(annotations, node):
        parts.append(escaped_text)
```

### Visitor/Renderer Pattern

```python
# Strategy returns renderer
renderer = self._empty_element_strategy.get_renderer(node, is_empty)

# Renderer handles all tag details
opening_tag = renderer.render_opening_tag(node.tag, attributes_str, closing_indent)
parts.append(opening_tag)

# Simple check
if not is_empty:
    if text := self._text_content(annotations, node):
        parts.append(escaped_text)
```

---

**Document Version:** 1.0
**Author:** Architecture discussion with AI assistant
**Status:** Reference document for future decisions
