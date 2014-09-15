import unittest

from lxml import etree
import should_be.all  # noqa

import xmlmapper as mp
from xmlmapper import xml_helpers as xh


class SampleModel(mp.Model):
    ROOT_ELEM = 'some_elem'

    name = mp.ROOT.name


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
        self.desc = mp.ROOT.name['lang': 'english'] % mp.Custom(xh.load_text,
                                                                xh.dump_text)

    def test_loads(self):
        self.model._etree.append(self.elem)
        self.desc._loads = lambda e: str(e.text) + '-hi'
        self.desc.__get__(self.model).should_be(self.target_value + '-hi')

    def test_dumps(self):
        def set_text(e, v):
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
        self.desc = mp.ROOT.name

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
        self.desc = mp.ROOT.cheese['type']


class TestNodeModelValue(_TestDescBase, unittest.TestCase):
    def setUp(self):
        class OtherModel(mp.Model):
            ROOT_ELEM = 'food'
            crackers = mp.ROOT.crackers

        self.model = SampleModel()
        self.target_value = OtherModel()
        self.target_value.crackers = 'ritz'
        self.alternate_value = OtherModel()
        self.alternate_value.crackers = 'whole-grain'
        self.desc = mp.ROOT.food % OtherModel % {'always_present': False}
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
        self.desc = mp.ROOT.food[...].cracker % (xh.attr_loader('name'),
                                                 xh.attr_dumper('name'))
        self.elem = etree.Element('food')
        self.item_elem_name = 'cracker'
        self.item_path = 'food/cracker'
        self.elem.append(etree.Element('cheese', name='cheddar'))
        self.elem.append(etree.Element('cheese', name='swiss'))

    def test_partial_set(self):
        self.make_present()
        self.make_item_present(self.alternate_value[1])
        dumper = lambda e, v: e.set('like', v)
        other_desc = mp.ROOT.food[...].cracker % {'loads': xh.load_text,
                                                  'dumps': dumper,
                                                  'full_replace': False}
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
        self.desc = mp.ROOT.food[...] % (xh.attr_loader('name'),
                                         xh.attr_dumper('name', 'cheese'))
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
