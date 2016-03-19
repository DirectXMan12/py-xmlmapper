from lxml import etree
import six


def load_text(elem):
    return elem.text


def dump_text(val, elem):
    elem.text = six.text_type(val)
    return elem


def text_dumper(elem_name=None, processor=six.text_type, **extra_attributes):
    def process_and_dump_text(val, elem):
        elem = dump_text(elem, processor(val))
        for attr, val in extra_attributes.items():
            elem.set(attr, val)

        return elem

    def create_and_dump_text(val):
        elem = etree.Element(elem_name)
        return process_and_dump_text(val, elem)

    if elem_name is not None:
        return create_and_dump_text
    else:
        return process_and_dump_text


def text_loader(processor=six.text_type):
    def load_and_process_text(elem):
        return processor(elem.text)

    return load_and_process_text


def attr_dumper(attr_name, elem_name=None,
                processor=six.text_type, **extra_attributes):
    def dump_attr(val, elem):
        elem.set(attr_name, processor(val))
        for attr, val in extra_attributes.items():
            elem.set(attr, val)
        return elem

    if elem_name is None:
        return dump_attr
    else:
        def create_and_dump_attr(val):
            return dump_attr(val, etree.Element(elem_name))

        return create_and_dump_attr


def attr_loader(attr_name, processor=six.text_type):
    def load_attr(elem):
        return processor(elem.get(attr_name))

    return load_attr


def load_presence(elem):
    return elem is not None


def dump_presence(val, elem):
    return elem if val else None


def str_to_bool(s):
    return s.lower() == 'true' or s == '1'


def create_element(*args, **kwargs):
    return etree.Element(*args, **kwargs)
