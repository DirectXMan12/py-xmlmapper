Basic Core Modeler Tutorial
===========================

In this example, we will use the `xmlmapper` library to create a simple model
for parsing XML descriptions of meals.

To start, suppose that we have an XML document that describes a dinner:

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

Now, suppose we want to model this document, so we can parse and create meal
descriptions.  First, we create a model for the overall meal.  We will start
by creating an empty model with a root tag of "meal".

    >>> import xmlmapper.core_modeler as mp
    >>> class Meal(mp.Model):
    ...     ROOT_ELEM = "meal"
    ...
    >>>

Then, we will add in the first part of the model: the name of the meal.
Note that these attributes can simply be added using
`attribute = Constructor(xyz)` in the class definition -- they do not have
to be added after the fact as shown below.

    >>> Meal.name = mp.AttributeValue('.', 'type')
    >>>

The `AttributeValue` constructor takes, at the very least, a basic XPath
expression to the tag containing the attribute, as well as the name of the
attribute that we want to extract.  It can also take `loads` and `dumps`
arguments to describe how to convert the value of the attribute from raw text
to a python value and vice-versa, respectively.  By default, it just uses the
appropriate string constructors for this purpose.

Next, we will want to model our appetizers:

    >>> Meal.cheese = mp.NodeValue('appetizers/cheese')
    >>> Meal.crackers = mp.AttributeValue('appetizers/cheese', 'crackers')
    >>> class Appetizer(mp.Model):
    ...     ROOT_ELEM = 'appetizer'
    ...     name = mp.AttributeValue('.', 'name')
    ...     description = mp.NodeValue('.')
    ...
    >>> Meal.appetizer = mp.ModelNodeValue('appetizers/appetizer', Appetizer)
    >>>

Here, we introduce two new types: the `NodeValue` type and the `ModelNodeValue` type.
The former takes a basic XPath expression and extracts the text from the tags that it
points to, while the latter maps a tag and all of its contents to another model.

The `NodeValue` constructor can also take `loads` and `dumps` parameters, while the
`ModelNodeValue` constructor can take a boolean value named `always_present`, while
defaults to True.  More on that later.

Now we will tackle the side dishes.  The side dishes are a uniform list, and thus
can be modeled as follows:

    >>> from xmlmapper import xml_helpers as xh
    >>> Meal.sides = mp.NodeValueList('side_dishes', xh.attr_loader('name'), xh.attr_dumper('name', 'side'))
    >>>

The `NodeValueList` constructor takes a basic XPath expression pointing to the
parent element for the list, as well as `elem_loads` and `elem_dumps` arguments
which specify how to convert the elements in the list to and from python values.

Here, we also see a couple of basic helpers from the `xml_helper` module which
assist in creating methods which load attributes, and dump attributes.  Both the
`elem_loads` and `elem_dumps` methods have the same signature as their `loads`
and `dumps` counterparts, except the `elem_dumps` method is expected to create
the corresponding XML element.  This can be done by using the `create_element`
helper, or by manually invoking `lxml.etree.Element`.

We will now quickly model the main course, as it is just simple text:

    >>> Meal.main_course = mp.NodeValue('main_course')

Continuing on, we must model our drinks.  For the drinks, we want to have two
separate attributes for wines and non-alcoholic drinks, and we also want to
be able to list the types of drinks we have to offer.

    >>> Meal.drink_types = mp.NodeValueList('drinks', xh.attr_loader('name'), xh.attr_dumper('name', 'category', alcoholic=True))
    >>> Meal.wines = mp.NodeValueListView('drinks/category[@name="wines"]', 'drink[@alcoholic="True"]', xh.attr_loader('name'), xh.attr_dumper('name'))
    >>> Meal.kid_wines = mp.NodeValueListView('drinks/category[@name="wines"]', 'drink[@alcoholic="False"]', xh.attr_loader('name'), xh.attr_dumper('name'))

While the `NodeValueList` is familiar, the `NodeValueListView` is new here.
`NodeValueListView` is similar to `NodeValueList`, except that it only captures
a subset of the elements under a given parent element.  Its constructor takes
an XPath expression to the parent element, followed by a selector XPath expression
to filter the sub elements.  Note that the selector should consist of an element
name followed by zero or more XPath predicates (such as attribute selectors).

Unlike the `elem_dumps` method of `NodeValueList`, the the `elem_dumps` parameter of
`NodeValueListView` takes two arguments: an existing element, and the python value
to convert.  `elem_dumps` for `NodeValueListView` may then manipulate and return the
existing element instead of having to create the element itself.

Additionally, note the additional keyword parameter of the `attr_dumper` helper in `NodeValueList`.
Any additional keyword arguments passed to `attr_dumper` will be added as properties of the
created element.

Lastly, we will model the desert element.  We will assume that not all meals have desserts:

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
    >>> class Dessert(mp.Model):
    ...     ROOT_ELEM = 'dessert'
    ...     name = mp.NodeValue('food')
    ...     drink = mp.CustomNodeValue('drink', load_drink, dump_drink)
    ...
    >>> Meal.dessert = mp.ModelNodeValue('dessert', Dessert, always_present=False)
    >>>

Here, we introduce the last, and most fundamental type: `CustomNodeValue`.
Like `NodeValue`, `CustomNodeValue` takes an XPath expression, a `loads`,
and a `dumps` parameter.  Unlike the former, however, the `loads` and `dumps`
parameters are mandatory, and work converting values to XML elements, instead
of values to text.

Additionally, we make use of the `always_present` parameter here.  Setting this
to `False` means that it will not get automatically created if we go to fetch it
and the underlying tag is not present.

Using the model
---------------

Now that we have our model, we can work with it.  We will create two instances
of the model: one empty one, and one based on the XML above.

    >>> meal1 = Meal(xml)
    >>> meal2 = Meal()

Now, we can manipulate both.  The first thing to note is that since `appetizer`
was set as always present, we can do the following:

    >>> meal2.appetizer.name = 'corn dogs'
    >>> meal2.appetizer.description = 'hot dogs wrapped in corn meal and deep-fried'
    >>> str(meal2)
    '<meal><appetizers><appetizer name="corn dogs">hot dogs wrapped in corn meal and deep-fried</appetizer></appetizers></meal>'
    >>>

However, since we set set `dessert` as not always present, we must do the following:

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
'dessert' element would have been created as such '<dessert sugary="True">...</dessert>'.

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
    >>> m = mp.Model(elem)
    >>> m._etree is elem
    True
    >>>

Since all manipulation is done in place and lazily, any structure present
in the element tree which is not present in the model will be left untouched.

Note that although we've directly used the the `xmlmapper.core_modeler` module
here, the root `xmlmapper` contains all the classes from the `core_modeler`
module.
