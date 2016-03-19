import six

if six.PY2:
    import mock
else:
    from unittest import mock

import unittest

from lxml import etree
import should_be.all  # noqa

import xmlmapper as mp
from xmlmapper import xml_helpers as xh


class SampleModel(mp.Model):
    ROOT_ELEM = 'some_elem'

    name = mp.NodeValue('name')


class TestModel(unittest.TestCase):
    def test_load_from_etree(self):
        xml = etree.Element('some_elem')
        name_elem = etree.Element('name')
        name_elem.text = 'hi'
        xml.append(name_elem)
        model = SampleModel(xml)

        model._etree.shouldnt_be_none()
        model.name.should_be('hi')

    def test_load_from_string(self):
        xml = "<some_elem><name>hi</name></some_elem>"
        model = SampleModel(xml)

        model._etree.shouldnt_be_none()
        model.name.should_be('hi')

    def test_load_from_none(self):
        model = SampleModel()

        model._etree.shouldnt_be_none()
        model._etree.tag.should_be('some_elem')

    def test_raises_when_root_elem_doesnt_match(self):
        xml = "<some_other_elem><name>hi</name></some_other_elem>"

        def make_sample_model(xml):
            return SampleModel(xml)

        make_sample_model.should_raise(ValueError, xml)

    def test_to_string(self):
        model = SampleModel()
        model.name = 'some name'

        xml_str = str(model)
        if six.PY2:
            xml_str2 = model.to_xml()
            xml_str3 = unicode(model)
            xml_str3.should_be(xml_str2.decode('ascii'))
        else:
            xml_str2 = model.to_xml(encoding=str)

        xml_str.should_be(xml_str2)

        xml = etree.fromstring(xml_str)

        name_elem = xml.find('name')
        name_elem.shouldnt_be_none()
        name_elem.text.should_be('some name')

    def test_to_bytes(self):
        model = SampleModel()
        model.name = 'some name'

        xml_str = bytes(model)
        xml_str2 = model.to_xml()

        xml_str.should_be(xml_str2)

        xml = etree.fromstring(xml_str)

        name_elem = xml.find('name')
        name_elem.shouldnt_be_none()
        name_elem.text.should_be('some name')


class TestElemUtils(unittest.TestCase):
    def test_make_elem_plain(self):
        elem = mp.make_elem('some_elem')

        elem.tag.should_be('some_elem')

    def test_make_elem_with_attr_name(self):
        elem = mp.make_elem('some_elem[@some_attr]')

        elem.tag.should_be('some_elem')
        elem.get('some_attr').should_be_empty()

    def test_make_elem_with_attr_full(self):
        elem = mp.make_elem('some_elem[@some_attr="some val"]')

        elem.tag.should_be('some_elem')
        elem.get('some_attr').should_be('some val')

    def test_make_elem_multiple_attrs(self):
        elem = mp.make_elem('some_elem[@some_attr="some val"][@other_attr]')

        elem.tag.should_be('some_elem')
        elem.get('some_attr').should_be('some val')
        elem.get('other_attr').should_be_empty()

    def test_make_path_already_exists(self):
        root = etree.Element('root')
        t1 = etree.Element('tag1')
        t2 = etree.Element('tag2')
        t3 = etree.Element('tag3')
        root.append(t1)
        t1.append(t2)
        t2.append(t3)

        with mock.patch.object(mp, 'make_elem') as make_patch:
            res = mp.make_path('tag1/tag2/tag3', root)

            make_patch.called.should_be_false()
            res.tag.should_be('tag3')

    def test_make_path_parent_exists(self):
        root = etree.Element('root')
        t1 = etree.Element('tag1')
        t2 = etree.Element('tag2')
        root.append(t1)
        t1.append(t2)

        res = mp.make_path('tag1/tag2/tag3', root)

        res.tag.should_be('tag3')
        t2.find('tag3').shouldnt_be_none()

    def test_make_path_nothing_exists(self):
        root = etree.Element('root')

        res = mp.make_path('tag1/tag2/tag3', root)

        res.shouldnt_be_none()
        res.tag.should_be('tag3')
        root.find('tag1/tag2/tag3').shouldnt_be_none()

    def test_make_path_with_attribs(self):
        root = etree.Element('root')

        res = mp.make_path('tag1/tag2/tag3[@name="val"]', root)

        res.shouldnt_be_none()
        res.tag.should_be('tag3')
        res.get('name').should_be('val')
        root.find('tag1/tag2/tag3').shouldnt_be_none()

    def test_make_path_to_parent_some_exists(self):
        root = etree.Element('root')
        t1 = etree.Element('tag1')
        root.append(t1)

        res = mp.make_path('tag1/tag2/tag3', root, to_parent=True)

        res.tag.should_be('tag2')
        t1.find('tag2').shouldnt_be_none()

    def test_make_path_to_parent_all_exists(self):
        root = etree.Element('root')
        t1 = etree.Element('tag1')
        t2 = etree.Element('tag2')
        root.append(t1)
        t1.append(t2)

        res = mp.make_path('tag1/tag2/tag3', root, to_parent=True)

        res.tag.should_be('tag2')
        t1.find('tag2').shouldnt_be_none()


class _TestDescBase(object):
    def make_present(self):
        self.model._etree.append(self.elem)

    def test_get_exists(self):
        self.make_present()
        self.desc.__get__(self.model).should_be(self.target_value)

    def test_get_not_exists(self):
        self.desc.__get__(self.model).should_be_none()

    def test_del_exists(self):
        self.make_present()
        self.desc.__delete__(self.model)

    def test_del_not_exists(self):
        self.desc.__delete__.should_raise(AttributeError, self.model)

    def test_set_exists(self):
        self.make_present()
        self.desc.__get__(self.model).should_be(self.target_value)
        self.desc.__set__(self.model, self.alternate_value)
        self.desc.__get__(self.model).should_be(self.alternate_value)

    def test_set_not_exists(self):
        self.desc.__set__(self.model, self.alternate_value)
        self.desc.__get__(self.model).should_be(self.alternate_value)


class TestCustomNodeValue(_TestDescBase, unittest.TestCase):
    def setUp(self):
        self.model = SampleModel()
        self.elem = etree.Element('name', lang='english')
        self.target_value = 'some name'
        self.alternate_value = 'some other name'
        self.elem.text = self.target_value
        self.desc = mp.CustomNodeValue('name[@lang="english"]',
                                       xh.load_text, xh.dump_text)

    def test_loads(self):
        self.model._etree.append(self.elem)
        self.desc._loads = lambda e: str(e.text) + '-hi'
        self.desc.__get__(self.model).should_be(self.target_value + '-hi')

    def test_dumps(self):
        def set_text(v, e):
            e.text = v[:-3]
            return e

        self.desc._dumps = set_text
        self.desc.__set__(self.model, self.target_value + '-hi')
        elem = self.model._etree.find('name')
        elem.shouldnt_be_none()
        elem.text.should_be(self.target_value)

    def test_set_invalidates_cache(self):
        self.model._cache = True
        self.desc._cached_vals[self.model] = 'cheese'
        self.desc.__set__(self.model, 'crackers')
        self.desc.__get__(self.model).should_be('crackers')
        self.desc._cached_vals[self.model].should_be('crackers')

    def test_get_cache_disabled(self):
        self.model._cache = False
        self.desc.__set__(self.model, 'cheese')
        self.desc.__get__(self.model).should_be('cheese')
        self.model._etree.find('name').text = 'crackers'
        self.desc.__get__(self.model).should_be('crackers')

    def test_get_cache_enabled(self):
        self.model._cache = True
        self.desc._cached_vals[self.model] = 'cheese'
        self.desc.__get__(self.model).should_be('cheese')


class TestNodeValue(TestCustomNodeValue):
    def setUp(self):
        self.model = SampleModel()
        self.elem = etree.Element('name')
        self.target_value = 'some value'
        self.alternate_value = 'some other value'
        self.elem.text = self.target_value
        self.desc = mp.NodeValue('name')

    def test_loads(self):
        self.model._etree.append(self.elem)
        self.desc._raw_loads = lambda v: str(v) + '-hi'
        self.desc.__get__(self.model).should_be(self.target_value + '-hi')

    def test_dumps(self):
        self.desc._dumps = lambda v: v[:-3]
        self.desc.__set__(self.model, self.target_value + '-hi')
        elem = self.model._etree.find('name')
        elem.shouldnt_be_none()
        elem.text.should_be(self.target_value)


class TestAttributeValue(_TestDescBase, unittest.TestCase):
    def setUp(self):
        self.model = SampleModel()
        self.elem = etree.Element('cheese')
        self.target_value = 'cheddar'
        self.alternate_value = 'swiss'
        self.elem.set('type', 'cheddar')
        self.desc = mp.AttributeValue('cheese', 'type')


class TestNodeModelValue(_TestDescBase, unittest.TestCase):
    def setUp(self):
        class OtherModel(mp.Model):
            ROOT_ELEM = 'food'
            crackers = mp.NodeValue('crackers')

        self.model = SampleModel()
        self.target_value = OtherModel()
        self.target_value.crackers = 'ritz'
        self.alternate_value = OtherModel()
        self.alternate_value.crackers = 'whole-grain'
        self.desc = mp.ModelNodeValue('food', OtherModel, always_present=False)
        self.elem = self.target_value._etree

    def test_always_present(self):
        self.desc._always_present = True
        self.desc.__get__(self.model).shouldnt_be_none()


class _TestNodeValueListViewBase(_TestDescBase):
    @property
    def init_desc(self):
        return self.desc.__get__(self.model)

    def make_item_present(self, content='', ind=1):
        item_elem = etree.Element(self.item_elem_name, name=content)
        self.elem.insert(ind, item_elem)

    def test_get_item_exists(self):
        self.make_present()
        self.make_item_present(self.alternate_value[0])
        self.init_desc[0].shouldnt_be_none()
        self.init_desc[0].should_be(self.alternate_value[0])

    def test_get_item_not_exists(self):
        self.make_present()
        self.init_desc.__getitem__.should_raise(IndexError, 0)

    def test_set_item_exists(self):
        self.make_present()
        self.make_item_present(self.alternate_value[0])
        self.init_desc[0] = self.alternate_value[2]
        self.model._etree.findall(self.item_path).should_have_length(1)
        self.model._etree.find(self.item_path).get('name').should_be(
            self.alternate_value[2])

    def test_set_item_not_exists(self):
        self.make_present()
        self.init_desc[0] = self.alternate_value[2]
        self.model._etree.findall(self.item_path).should_have_length(1)
        self.model._etree.find(self.item_path).get('name').should_be(
            self.alternate_value[2])

    def test_del_item_exists(self):
        self.make_present()
        self.make_item_present(self.alternate_value[0])
        del self.init_desc[0]
        self.model._etree.find(self.item_path).should_be_none()

    def test_del_item_not_exists(self):
        self.make_present()
        self.init_desc.pop.should_raise(IndexError, 0)
        self.model._etree.find(self.item_path).should_be_none()

    def test_always_present(self):
        self.desc._always_present = True
        self.init_desc.should_be([])

    def test_len(self):
        self.make_present()
        self.make_item_present(self.alternate_value[0])
        self.make_item_present(self.alternate_value[1])
        len(self.desc.__get__(self.model)).should_be(2)


class TestNodeValueListView(_TestNodeValueListViewBase, unittest.TestCase):
    def setUp(self):
        self.model = SampleModel()
        self.target_value = []
        self.alternate_value = ['ritz', 'triscuit', 'wheat thins']
        self.desc = mp.NodeValueListView('food', 'cracker',
                                         lambda e: e.get('name'),
                                         lambda v, e: e.set('name', v))
        self.elem = etree.Element('food')
        self.item_elem_name = 'cracker'
        self.item_path = 'food/cracker'
        self.elem.append(etree.Element('cheese', name='cheddar'))
        self.elem.append(etree.Element('cheese', name='swiss'))

    def test_partial_set(self):
        self.make_present()
        self.make_item_present(self.alternate_value[1])
        dumper = lambda v, e: e.set('like', v)
        other_desc = mp.NodeValueListView('food', 'cracker', lambda e: e.text,
                                          full_replace=False,
                                          elem_dumps=dumper)
        other_init_desc = other_desc.__get__(self.model)
        other_init_desc[0] = 'shredded wheat'
        self.model._etree.findall(self.item_path).should_have_length(1)
        elem = self.model._etree.find(self.item_path)
        elem.get('like').should_be('shredded wheat')
        elem.get('name').should_be(self.alternate_value[1])

    def test_set_leaves_other_elems_behind(self):
        self.make_present()
        self.make_item_present(self.alternate_value[0])
        self.make_item_present(self.alternate_value[1])

        food_elem = self.model._etree.find('food')
        len(food_elem).should_be(4)
        self.desc.__set__(self.model, ['wheat thins'])
        len(food_elem).should_be(3)
        food_elem[0].tag.should_be('cheese')
        food_elem[1].tag.should_be('cheese')
        food_elem[2].tag.should_be('cracker')
        food_elem[2].get('name').should_be('wheat thins')

    def test_delete_leaves_other_elems_behind(self):
        self.make_present()
        self.make_item_present(self.alternate_value[0])
        self.make_item_present(self.alternate_value[1])

        food_elem = self.model._etree.find('food')
        len(food_elem).should_be(4)
        self.desc.__delete__(self.model)
        len(food_elem).should_be(2)
        food_elem[0].tag.should_be('cheese')
        food_elem[1].tag.should_be('cheese')

    def test_set_item_exists(self):
        super(TestNodeValueListView, self).test_set_item_exists()
        self.model._etree.findall('food/cheese').shouldnt_be_empty()

    def test_set_item_not_exists(self):
        super(TestNodeValueListView, self).test_set_item_not_exists()
        self.model._etree.findall('food/cheese').shouldnt_be_empty()

    def test_del_item_exists(self):
        super(TestNodeValueListView, self).test_del_item_exists()
        self.model._etree.findall('food/cheese').shouldnt_be_empty()

    def test_del_item_not_exists(self):
        super(TestNodeValueListView, self).test_del_item_not_exists()
        self.model._etree.findall('food/cheese').shouldnt_be_empty()

    def test_insert(self):
        self.make_present()
        self.make_item_present(self.alternate_value[0])
        self.make_item_present(self.alternate_value[1], ind=3)
        self.init_desc.insert(1, self.alternate_value[2])

        self.model._etree.findall(self.item_path).should_have_length(3)
        list(self.init_desc).should_be([self.alternate_value[0],
                                        self.alternate_value[2],
                                        self.alternate_value[1]])
        elem = self.model._etree.find('food')[3]
        elem.tag.should_be('cracker')
        elem.get('name').should_be(self.alternate_value[2])

    def test_delete_pred_true_removes_elem(self):
        self.make_present()
        self.make_item_present(self.alternate_value[0])
        self.make_item_present(self.alternate_value[1])
        self.desc._delete_pred = lambda e: True

        del self.init_desc[0]
        len(self.model._etree.findall(self.item_path)).should_be(1)

    def test_delete_pred_false_keeps_elem(self):
        self.make_present()
        self.make_item_present(self.alternate_value[0])
        self.make_item_present(self.alternate_value[1])

        def del_pred(elem):
            elem.attrib.pop('name')
            return False

        self.desc._delete_pred = del_pred

        del self.init_desc[0]
        len(self.model._etree.findall(self.item_path)).should_be(2)
        self.model._etree.find(self.item_path).get('name',
                                                   None).should_be_none()


class TestNodeValueList(_TestNodeValueListViewBase, unittest.TestCase):
    def setUp(self):
        self.model = SampleModel()
        self.target_value = []
        self.alternate_value = ['american', 'pepperjack', 'cheddar']
        self.desc = mp.NodeValueList('food', lambda e: e.get('name'),
                                     lambda v: etree.Element('cheese', name=v))
        self.elem = etree.Element('food')
        self.item_elem_name = 'cheese'
        self.item_path = 'food/cheese'

    def make_present(self):
        super(TestNodeValueList, self).make_present()

    def test_delete_removes_node(self):
        self.make_present()
        self.model._etree.find('food').shouldnt_be_none()
        self.desc.__delete__(self.model)
        self.model._etree.find('food').should_be_none()

    def test_insert(self):
        self.make_present()
        self.make_item_present(self.alternate_value[0])
        self.make_item_present(self.alternate_value[1], ind=3)
        self.init_desc.insert(1, self.alternate_value[2])

        self.model._etree.findall(self.item_path).should_have_length(3)
        list(self.init_desc).should_be([self.alternate_value[0],
                                        self.alternate_value[2],
                                        self.alternate_value[1]])
