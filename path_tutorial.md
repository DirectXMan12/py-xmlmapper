Path Modeler Tutoial
====================

In this example, we will use the `xmlmapper` library's `path_mapper` module to
create the same model as demonstrated in `core_tutorial.md`.

To start, we'll reproduce our XML document from before:

    >>> xml = """
    ... <meal type='dinner'>
    ...     <appetizers>
    ...         <cheese crackers='triscuits'>cheddar</cheese>
    ...         <appetizer name='dogs in a blanket'>cocktail hot dogs in flaky pastry</appetizer>
    ...     </appetizers>
    ...     <dessert>
    ...         <food>carrot cake</food>
    ...         <drink name='shirely temple' alcoholic='False'/>
    ...     </dessert>
    ...     <side_dishes>
    ...         <side name='mashed potatoes'/>
    ...         <side name='green beans'/>
    ...     </side_dishes>
    ...     <main_course category='meat'>roast beef</main_course>
    ...     <drinks>
    ...         <category name='wines' price='10'>
    ...             <drink alcoholic='True' name='blanc'/>
    ...             <drink alcoholic='False' name='kiddy wine'/>
    ...             <drink alcoholic='True' name='pinot noir'/>
    ...         </category>
    ...     </drinks>
    ... </meal>
    ... """
    >>>

Creating the model
------------------

First, we need to create our model, just like before, setting a root tag
of "meal":

    >>> from xmlmapper import path_modeler as pm
    >>> class Meal(pm.Model):
    ...     ROOT_ELEM = "meal"
    ...
    >>>

Note that the `Model` class here is the same exact model class from the core
modeler in `xmlmapper` or `xmlmapper.core_modeler`; `Model` is simply imported
into the root `path_modeler` module for convinience.

Next, we'll add in the first part of the model: the name of the meal.

    >>> Meal.name = pm.ROOT['name']
    >>>

This sytax is significantly different from the core modeler, but is designed
to feel more natural and be more readable.  The `ROOT` object refers to the
root tag of the current model.  Python's item access syntax can be used to
refer to attributes.  XMLMapper determines the type of mapping from the last
value in the specified path.  Here, the last value is the attribute "name" on
the root element, so XMLMapper maps the `name` property of the `Meal` class
to the value of the `name` attribute on the root tag.

Now we'll model our appetizers:

    >>> Meal.cheese = pm.ROOT.appetizers.cheese
    >>> Meal.crackers = pm .ROOT.appetizers.cheese['crackers']
    >>> class Appetizer(pm.Model):
    ...     ROOT_ELEM = 'appetizer'
    ...     name = pm.ROOT['name']
    ...     description = pm.ROOT
    ...
    >>> Meal.appetizer = pm.ROOT.appetizers.appetizer % Appetizer
    >>>

There are two new features here.  First, we see that to map to the text of a
tag, we simply specify the path to the tag (as demonstrated by `Meal.cheese`
and `Appetizer.description`.

Secondly, we see the way to create a property that maps a tag to a model:
we simply use the modulo/format operator, `%`, with the path on the left-hand
side and the model class on the right.  Think about this like we're
"formatting" the tag with the model class, just like we format strings with
`dict` or `tuple` objects.  We will see later on that this same mnemonic
applies when we use the `%` operator to set the `loads` and `dumps` methods
as well.

Continuing on, we'll model the side dishes.  The side dishes are a uniform
list:

    >>> from xmlmapper import xml_helpers as xh
    >>> Meal.sides = pm.ROOT.side_dishes[...] % (xh.attr_loader('name'), xh.attr_dumper('name', 'side'))

Once again, we see our basic XML manipulation helpers.  Additionally, there
are two new pieces of syntax.  First, we have the syntax for mapping to lists:
passing the `...` (ellipsis) object to the item acessor.  Additionally, we
see the syntax for specifying `loads` and `dumps` (or `elem_loads` and
`elem_dumps`, as the case may be).  Just like mapping to a model, we use the
`%` operator to "format" the path with a loader and dumper.

Continuing on, we'll model the main course:

    >>> Meal.main_course = pm.ROOT.main_course

Then, we'll model our drinks.  As before, we want to have two separate
attributes for alcoholic wines and non-alcoholic wine-like beverages that
kids can drink.  Additionally, we'll want to list all the categories of drinks.

    >>> Meal.drink_types = pm.ROOT.drinks[...] % (xh.attr_loader('name'), xh.attr_dumper('name', 'category', alcoholic=True))
    >>> Meal.wines = pm.ROOT.drinks.category['name': 'wines'][...].drink['alcoholic': True] % (xh.attr_loader('name'), xh.attr_dumper('name'))
    >>> Meal.kid_wines = pm.ROOT.drinks.category['name': 'wines'][...].drink['alcoholic': False] % (xh.attr_loader('name'), xh.attr_dumper('name'))

While the syntax for specifying the uniform list used to define
`Meal.drink_types` is familar, the specifications to `Meal.wines` and
`Meal.kid_wines` present new syntax, as well a twist on the uniform list
syntax.

When additional path elements are specified after a `[...]`, they are as the
selector to create a list view which maps to a subset of the elements in a
list.  Additionally, we see here the syntax for filtering on the value of
an attribute, instead of just its presence.  To do so, we use Python's slice
syntax in a manner that looks similar to its `dict` creation syntax, specifying
`attribute: value` in the item accessor instead of just the attribute name.

Lastly, we'll model the desert element.  We will assume that not all meals
have desserts:

    >>> def load_drink(elem):
    ...     name = elem.get('name')
    ...     if xh.str_to_bool(elem.get('alcoholic')):
    ...         return "[adult-only] " + name
    ...     else:
    ...         return name
    ...
    >>> def dump_drink(val):
    ...     if val.startswith("[adult-only] "):
    ...         name = val[13:]
    ...         alcoholic = "True"
    ...     else:
    ...         name = val
    ...         alcoholic = "False"
    ...     return xh.create_element('drink', name=name, alcoholic=alcoholic)
    ...
    >>> class Dessert(pm.Model):
    ...     ROOT_ELEM = 'dessert'
    ...     name = pm.ROOT.food
    ...     drink = pm.ROOT.drink % pm.Custom(load_drink, dump_drink)
    ...
    >>> Meal.dessert = pm.ROOT.dessert % Dessert % {'always_present': False}
    >>>

Here, we introduce the syntax for specifying additional properties, as well as
`loads` and `dumps` via "formatting" the path with  a `dict`.  We also show how
formatting can be chained, so that we may first "format" the path with a model,
and then "format" the result of that to set the property as not always present.

Additionally, we see that we may create a mapping that maps to a tag itself,
instead of its text, by "formatting" the path with a with either the `Custom`
class, or by an instance of a subclass of the `Custom` class.  Subclasses of
the `Custom` class need only have `loads` and `dumps` callable properties or
methods.  In the case where only the `Custom` class itself is used, `loads`
and `dumps` methods may be set using the `%` operator in the standard ways
discussed above.


Using the model
---------------

Now that we have our model, we can work with it.  We will create two instances
of the model: one empty one, and one based on the XML above.

    >>> meal1 = Meal(xml)
    >>> meal2 = Meal()

Now, we can manipulate both.  As before, since `appetizer` was set as always
present, we can do the following:

    >>> meal2.appetizer.name = 'corn dogs'
    >>> meal2.appetizer.description = 'hot dogs wrapped in corn meal and deep-fried'
    >>> str(meal2)
    '<meal><appetizers><appetizer name="corn dogs">hot dogs wrapped in corn meal and deep-fried</appetizer></appetizers></meal>'
    >>>

However, since we set set `dessert` as not always present, we must do the
following:

    >>> meal2 = Meal()
    >>> meal2.dessert is None
    True
    >>> meal2.dessert = Dessert()
    >>> meal2.dessert.name = 'chocolate'
    >>> str(meal2)
    '<meal><dessert><food>chocolate</food></dessert></meal>'
    >>>

One of the neat things is that when you use selectors in XPath expressions,
XMLMapper will create the elements with those attributes.  So, for instance,
had we specified the selector for `dessert` as 'dessert[@sugary="True"]', the
'dessert' element would have been created as such
'<dessert sugary="True">...</dessert>'.

Now, we'll take a quick peek at the lists.  For the uniform lists, we can see
that the nth element of the list directly corresponds to the nth subelement:

    >>> list(meal1.sides)
    [u'mashed potatoes', u'green beans']
    >>> [se.get('name') for se in meal1._etree.find('side_dishes')]
    ['mashed potatoes', 'green beans']
    >>>

For the list views, the nth element of the list corresponds to the nth
subelement which matches the selector.  Changing the list does not affect
elements not matching the selector:

    >>> [se.get('name') for se in meal1._etree.find('drinks/category[@name="wines"]')]
    ['blanc', 'kiddy wine', 'pinot noir']
    >>> list(meal1.wines)
    [u'blanc', u'pinot noir']
    >>> list(meal1.kid_wines)
    [u'kiddy wine']
    >>> del meal1.wines[1]
    >>> list(meal1.wines)
    [u'blanc']
    >>> [se.get('name') for se in meal1._etree.find('drinks/category[@name="wines"]')]
    ['blanc', 'kiddy wine']

As demonstrated above, the `str` method can be used to get XML from the model.
However, if you wish to pass extra information to the `etree.tostring` method,
you can use the `to_xml` method of any model.  For instance:

    >>> print meal2.to_xml(pretty_print=True)
    <meal>
      <dessert>
        <food>chocolate</food>
      </dessert>
    </meal>
    <BLANKLINE>
    >>>

Finally, the actuall `lxml.etree` document can be accessed via the `_etree`
property of the model.  This can be useful if we want to use a model to
manipulate an existing element tree:

    >>> from lxml import etree
    >>> elem = etree.Element('elem')
    >>> m = pm.Model(elem)
    >>> m._etree is elem
    True
    >>>

Since all manipulation is done in place and lazily, any structure present
in the element tree which is not present in the model will be left untouched.

Note that although we directly use the `xmlmapper.path_modeler` namespace
the root `xmlmodeler` namespace contains the `ROOT` object as well as the
`Custom` class, the two components needed to make use of the path modeling
functionality.
