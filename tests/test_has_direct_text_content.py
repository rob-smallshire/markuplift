from lxml import etree
from markuplift.utilities import has_direct_significant_text

def make_tree(xml: str):
    return etree.fromstring(xml)

def test_element_with_no_text():
    el = make_tree("<root></root>")
    assert not has_direct_significant_text(el)

def test_element_with_whitespace_text():
    el = make_tree("<root>   \n\t  </root>")
    assert not has_direct_significant_text(el)

def test_element_with_significant_text():
    el = make_tree("<root>hello</root>")
    assert has_direct_significant_text(el)

def test_element_with_significant_text_and_children():
    el = make_tree("<root>hello<child/></root>")
    assert has_direct_significant_text(el)

def test_element_with_child_with_significant_tail():
    el = make_tree("<root><child/>world</root>")
    # child.tail is 'world'
    assert has_direct_significant_text(el)

def test_element_with_child_with_whitespace_tail():
    el = make_tree("<root><child/>   \n\t</root>")
    assert not has_direct_significant_text(el)

def test_element_with_multiple_children_and_mixed_tails():
    el = make_tree("<root><a/>foo<b/>   <c/>bar</root>")
    # a.tail = 'foo', b.tail = '   ', c.tail = 'bar'
    assert has_direct_significant_text(el)

def test_element_with_comment_with_significant_tail():
    root = etree.Element("root")
    comment = etree.Comment("This is a comment")
    root.append(comment)
    comment.tail = "important"
    assert has_direct_significant_text(root)

def test_element_with_comment_with_whitespace_tail():
    root = etree.Element("root")
    comment = etree.Comment("This is a comment")
    root.append(comment)
    comment.tail = "   \n"
    assert not has_direct_significant_text(root)

def test_element_with_processing_instruction_with_significant_tail():
    root = etree.Element("root")
    pi = etree.ProcessingInstruction("xml-stylesheet", "type='text/xsl' href='style.xsl'")
    root.append(pi)
    pi.tail = "data"
    assert has_direct_significant_text(root)

def test_element_with_processing_instruction_with_whitespace_tail():
    root = etree.Element("root")
    pi = etree.ProcessingInstruction("xml-stylesheet", "type='text/xsl' href='style.xsl'")
    root.append(pi)
    pi.tail = "  \n\t"
    assert not has_direct_significant_text(root)

def test_element_with_mixed_children_and_tails():
    root = etree.Element("root")
    child1 = etree.Element("child1")
    comment = etree.Comment("comment")
    pi = etree.ProcessingInstruction("foo", "bar")
    root.append(child1)
    root.append(comment)
    root.append(pi)
    child1.tail = "   "
    comment.tail = "baz"
    pi.tail = "   "
    # Only comment.tail is significant
    assert has_direct_significant_text(root)

def test_element_with_significant_text_and_all_children_whitespace_tails():
    root = etree.Element("root")
    child1 = etree.Element("child1")
    comment = etree.Comment("comment")
    pi = etree.ProcessingInstruction("foo", "bar")
    root.append(child1)
    root.append(comment)
    root.append(pi)
    root.text = "hello"
    child1.tail = "   "
    comment.tail = "   "
    pi.tail = "   "
    assert has_direct_significant_text(root)

def test_element_with_all_children_whitespace_tails_and_no_text():
    root = etree.Element("root")
    child1 = etree.Element("child1")
    comment = etree.Comment("comment")
    pi = etree.ProcessingInstruction("foo", "bar")
    root.append(child1)
    root.append(comment)
    root.append(pi)
    child1.tail = "   "
    comment.tail = "   "
    pi.tail = "   "
    assert not has_direct_significant_text(root)
