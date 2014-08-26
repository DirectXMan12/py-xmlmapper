import unittest

from lxml import etree
import should_be.all  # noqa

from xmlmapper import xml_helpers as xh


class TestXMLHelpers(unittest.TestCase):
    def setUp(self):
        self.elem_name = 'some_elem'
        self.elem = etree.Element(self.elem_name)

        self.attr_name = 'some_attr'
        self.attr_val = 'some val'
        self.alt_attr_val = 'some other val'
        self.elem.set(self.attr_name, self.attr_val)

        self.text_val = 'some text'
        self.alt_text_val = 'some other text'
        self.elem.text = self.text_val

    def test_load_text(self):
        xh.load_text(self.elem).should_be(self.text_val)

    def test_dump_text(self):
        xh.dump_text(self.elem, self.alt_text_val)
        self.elem.text.should_be(self.alt_text_val)

    def test_text_dumper_create(self):
        dumps = xh.text_dumper(self.elem_name, lambda s: 'hi-' + s,
                               extra='extra val')

        elem = dumps(self.alt_text_val)
        elem.tag.should_be(self.elem_name)
        elem.get('extra').should_be('extra val')
        elem.text.should_be('hi-' + self.alt_text_val)

    def test_text_dumper_no_create(self):
        dumps = xh.text_dumper(processor=lambda s: 'hi-' + s,
                               extra='extra val')

        elem = dumps(self.elem, self.alt_text_val)
        elem.should_be_exactly(self.elem)
        elem.get('extra').should_be('extra val')
        elem.text.should_be('hi-' + self.alt_text_val)

    def test_text_loader(self):
        loads = xh.text_loader(lambda s: 'hi-' + s)
        loads(self.elem).should_be('hi-' + self.text_val)

    def test_attr_dumper_no_create(self):
        dumps = xh.attr_dumper(self.attr_name, processor=lambda s: 'hi-' + s,
                               extra='extra val')
        elem = dumps(self.elem, self.alt_attr_val)
        elem.should_be_exactly(self.elem)
        elem.get(self.attr_name).should_be('hi-' + self.alt_attr_val)
        elem.get('extra').should_be('extra val')

    def test_attr_dumper_create(self):
        dumps = xh.attr_dumper(self.attr_name, self.elem_name,
                               lambda s: 'hi-' + s, extra='extra val')
        elem = dumps(self.alt_attr_val)
        elem.tag.should_be(self.elem_name)
        elem.get(self.attr_name).should_be('hi-' + self.alt_attr_val)
        elem.get('extra').should_be('extra val')

    def test_attr_loader(self):
        loads = xh.attr_loader(self.attr_name, processor=lambda s: 'hi-' + s)
        loads(self.elem).should_be('hi-' + self.attr_val)

    def test_str_to_bool(self):
        xh.str_to_bool('true').should_be(True)
        xh.str_to_bool('TRUE').should_be(True)
        xh.str_to_bool('True').should_be(True)
        xh.str_to_bool('1').should_be(True)
        xh.str_to_bool('false').should_be(False)
