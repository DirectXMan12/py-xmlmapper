Path Modeler Reference
======================

Actual Module: `xmlmapper.path_modeler`

*Note*: if there are any additional options besides `loads` and `dumps`, they
will be presented with an additional `dict`, without `loads` and `dumps`
elements, although as long as `loads` and `dumps` are appropriate, they
may be passed via a `dict` as well.

Text Node
---------

Maps to the text of a particular node, using `loads` and `dumps`
to convert the text to and from Python values (respectively).

```python
parent.child % (loads, dumps)
```

Custom Node
-----------

Maps directly to a particular node, making no assumptions about
its contents.  `loads` is expected to take an element and convert
it into a Python value, while `dumps` is expected to take an
element an a value, and return an element.

```python
parent.child % Custom(loads, dumps)
parent.child % Custom % (loads, dumps)
```

Node Attribute
--------------

Maps to the value of an attribute on a particular node. `loads`
and `dumps` convert the attribute value to and from Python values
(respectively).

```python
parent.child['attr'] % (loads, dumps)
```

Model Node
----------

Maps a node to a `Model`.  When the `always_present` parameter is set to
`True`, the root node of the model will get automatically created if it
does not exist when it is retrieved.  If set to `False`, then if the node
does not exist, retrieving the value will return `None`.

```python
parent.child % ModelClass % {'always_present': True}
```

Node List
---------

Maps the children of a node to a list of values.  `elem_loads`
takes one of the subelements and returns a Python value,
while `elem_dumps` takes a Python value and returns an element.
`NodeValueList` also has an `always_present` parameter that functions
identically to that of `ModelNodeValue`, except with respect to the
parent node.

```python
parent.child[...] % (elem_loads, elem_dumps) % {'always_present': False}
```

Node List View
--------------

Maps the a subset of the chilren of a node to a list of values. `elem_loads`
takes one of the subelements and returns a Python value.  `elem_dumps` takes
an element and a value and returns an element.  `NodeValueListView` has an
`always_present` parameter which functions identically to `NodeValueList`.
Additionally `NodeValueListView` has a parameter `full_replace`.  If
`full_replace` is `True`, then each time an element is set, a brand new
node is passed to `elem_dumps`.  However, if `full_replace` is set to `False`,
the existing element is passed to `elem_dumps`.  This allows you to have two
separate list views that modify the same set of elements, but functions on
different attributes, for instance.  Finally, there is a parameter
`delete_pred`, which takes in an element and returns a boolean.  If the
return value is `True`, the actual element will be deleted.  If the return
value is `False`, the the element will not be deleted, and `delete_pred`
is expected to modify the element accordingly to "delete" the appropriate
part (this is particularly useful when `full_delete` is `False`).

```python
parent.child[...].item % (elem_loads, elem_dumps) % {'always_present': False,
                                                     'full_replace': True}
parent.child[...].item % (elem_loads, elem_dumps, delete_pred) % {
    'always_present': False, 'full_replace': True}
```

Model
-----

The `Model` class is the lynchpin of XMLMapper, tying all the various mappings
together.  To manipulate an existing element tree, simply pass the root
`Element` to the  constructor.  Note that the element tree will be manipulated
in place; no copy is made.  To manipulate a XML document that's in a string,
you can simply pass that in as well.  To start from scratch, simply do not pass
any argument to the constructor of `Model`.

Additionally, the `Model` constructor takes a `cache` argument (and has a
corresponding `_cache` property).  When set to `True`, some of the mapping
descriptors above will cache their Python values, so they don't have to query
the element tree every time.  Set this to `False` if you will be manipulating
the element tree independently of the model.

Instances of `Model` have two important parts.  The first is the `_etree`,
property, which contains the root `Element` for the model.  The second is the
`to_xml()` method, and by extension the response of `Model` to `str`.  Calling
`str` on an instance of model will convert it to an XML string.  Calling
`to_xml` does the same thing, except that any arguments passed to `to_xml` will
be passed along to `etree.tostring` (so, for instance, you can pass the
`pretty_print` argument to `to_xml` to get a pretty-printed XML string).

```python
Model(content=None, cache=False)
```

```python
model.to_xml(*args, **kwargs)
```
