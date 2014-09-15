Python XML Mapper
=================

XML Mapper is a tool for mapping XML to Python objects and vice-versa.
It has no particular relation to any other libraries named 'XMLMapper', except
in general concept.

There are two main ways to use XMLMapper -- you can use the `core_modeler`
module's functionality, which uses a more traditional syntax -- you simply
create descriptors using standard Python class creation.  A tutorial for how
to use this module can be found in the file `core_tutorial.md`.  A reference
for this functionality can be found in `core_reference.md`.

The second way to use XMLMapper is to use the `path_modeler` module's
functionality, which is a DSL.  It uses Python's item and and attribute
selection syntax to specify the path to the XML elements in a "natural" way.
A tutorial for how to use this module can be found in the file
`path_tutorial.md`.  A reference for this functionality can be found in
`path_reference.md`.

Note that both the tutorials are both renderable as Markdown, as well as being
executable using [YALPT](https://github.com/directxman12/yalpt), so you can
experiment around directly in the context of the tutorial.

Basic examples can also be found below.

XMLMapper Core Modeler
----------------------

```python
import xmlmapper as mp
from xmlmapper import xml_helpers as xh

class TestSubModel(mp.Model):
    ROOT_ELEM = 'thirdnode'

    name = mp.AttributeValue('.', 'name')
    desc = mp.NodeValue('.')

class TestModel(mp.Model):
    ROOT_ELEM = 'topnode'

    some_node = mp.NodeValue('subnode/firstnode')
    some_attr = mp.AttributeValue('subnode/secondnode', 'type')
    some_model = mp.ModelNodeValue('subnode/thirdnode[@name="test"]', TestSubModel)
    some_list = mp.NodeValueList('subnode/list',
                                 xh.attr_loader('name'),
                                 xh.attr_dumper('name', 'listelem'))
    some_partial_list = mp.NodeValueListView('subnode/list',
                                             'listitem[@type="first"]',
                                             xh.attr_loader('name'),
                                             xh.attr_dumper('name'))

tm1 = TestModel()
tm1.some_node = 'value 1'
tm1.some_attr = 'value 2'
tm1.some_model.desc = 'some desc'
tm1.some_list = ['a', 'b', 'c']
tm1.some_partial_list = ['d', 'e']
compact = str(tm1)
pretty_printed = tm1.to_xml(pretty_print=True)

tm2 = TestModel(open('somefile.xml').read())
```

XMLMapper Path Modeler
----------------------

```python
import xmlmapper as mp
from xmlmapper import xml_helpers as xh

class TestSubModel(mp.Model):
    ROOT_ELEM = 'thirdnode'

    name = mp.ROOT['name']
    desc = mp.ROOT

class TestModel(mp.Model):
    ROOT_ELEM = 'topnode'

    some_node = mp.ROOT.subnode.firstnode
    some_attr = mp.ROOT.subnode.secondnode['type']
    some_model = mp.ROOT.subnode.thirdnode['name': 'test'] % TestSubModel
    some_list = mp.ROOT.subnode.list[...] % (xh.attr_loader('name'),
                                             xh.attr_dumper('name',
                                                            'listelem'))
    some_partial_list = mp.ROOT.subnode.list[...].listitem['type': 'first'] % (
        xh.attr_loader('name'), xh.attr_dumper('name'))

tm1 = TestModel()
tm1.some_node = 'value 1'
tm1.some_attr = 'value 2'
tm1.some_model.desc = 'some desc'
tm1.some_list = ['a', 'b', 'c']
tm1.some_partial_list = ['d', 'e']
compact = str(tm1)
pretty_printed = tm1.to_xml(pretty_print=True)

tm2 = TestModel(open('somefile.xml').read())
```

XPath Helpers
-------------

In addition to the `path_modeler` module, there exists a `path` module whose
methods are designed to assist in the construction of XPath expression strings.
It functions similarly to `path_modeler` module, except that it generates
strings instead of descriptors.  You can use it to generate the XPath
expressions for the `core_modeler` classes if you wish.
