XML Helper Reference
====================

Module: `xmlmapper.xml_helpers`

Note that any of the methods which create a `loads` or `dumps` method
can take an optional `processor` parameter.  this will be used to post- or
pre-process the Python value (respectively).

Text Loader (`Element` --> `str`)
--------------------------------

This method takes in an element and returns its text content.

```python
load_text
```

Text Dumper (`Element`, value --> `Element`)
--------------------------------------------

This method takes an element and a value and returns the element, after having
set its text to the value.

```python
dump_text
```

Create Text Loader (`Element` --> `str`)
----------------------------------------

The return value of this method is essentially the same as `load_text`, but
with the text being passed through the specified processor before it is
returned.

```python
text_loader(processor=six.text_type)
```

Create Text Dumper (`Element`, value --> `Element` or value --> `Element`)
--------------------------------------------------------------------------

This method optionally takes the name of an element, plus any additional
statically set attributes, and creates a `dumps` method.

If an element name is passed in, it will create a `dumps` method
which takes an element and a value and returns the element, having set the
element's text to the value.  If an element name is specified, it will create
a method which takes in a value and returns a new element of the specified
name with its text set to value.

Note that if you do not provide an element name and wish to pass in a
processor, you *must* do so by keyword.

```python
text_dumper(processor=six.text_type, **extra_attributes)
text_dumper(elem_name, processor=six.text_type, **extra_attributes)
```

Create Attribute Dumper (`Element`, value --> `Element` or value --> `Element`)
------------------------------------------------------------------------------

This method takes an attribute name, and optionally an element name,
as well as any additional statically set attributes, and creates a `dumps`
method.

If just an attribute name is passed in, it will create a `dumps` method
which takes an element and a value and returns the element, having set the
attribute to the value.  If both an attribute and element name are specified,
it will create a method which takes in a value and returns a new element of the
specified name with the specified attribute set to the value.

Note that if you do not provide an element name and wish to pass in a
processor, you *must* do so by keyword.

```python
attr_dumper(attr_name, processor=six.text_type, **extra_attributes)
attr_dumper(attr_name, elem_name, processor=six.text_type, **extra_attributes)
```

Create Attribute Loader (`ELement` --> `str`)
---------------------------------------------

This method takes an attribute name, and creates a method which takes an
element and returns the value of the specified attribute on that element.

```python
attr_loader(attr_name, processor=six.text_type)
```

Convert a String to a Boolean
-----------------------------

This method converts a string into a boolean.  Any upper- or lower-case
variation of 'true' as well as '1', will be converted into `True`.  Any other
value will be converted into `False`.

```python
str_to_bool(s)
```

Create an Element
-----------------

This method is essentially a proxy for `etree.Element`.  Any arguments passed
to this method will be passed on to `etree.Element`.  The benefit of using
this method is that it will always use the same implementation of ElementTree
that the rest of XMLMapper is using.  This means that if XMLMapper ever has to
either change ElementTree implementations, or offers multiple ElementTree
backends, you don't have to change your programs.

```python
create_element(*args, **kwargs)
```
