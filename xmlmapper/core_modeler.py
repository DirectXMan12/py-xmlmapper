import collections
import weakref

from lxml import etree
import six


def split_elem_def(path):
    """Get the element name and attribute selectors from an XPath path."""
    path_parts = path.rpartition('/')
    elem_spec_parts = path_parts[2].rsplit('[')
    # chop off the other ']' before we return
    return (elem_spec_parts[0], [part[:-1] for part in elem_spec_parts[1:]])


def set_elem_attrs(attr_parts, elem):
    """Sets the attributes on an element based on XPath attribute selectors."""
    for attr_part in attr_parts:
        attr_part = attr_part[1:]  # chop off '@'
        nv_parts = attr_part.split('=')
        attr_name = nv_parts[0]
        if len(nv_parts) == 1:
            attr_val = ''
        else:
            attr_val = nv_parts[1]
            if attr_val[0] in ("'", '"'):
                attr_val = attr_val[1:-1]  # remove quotes

        elem.set(attr_name, attr_val)


def make_elem(desc_str):
    """Makes an element based on a XPath description."""
    if '@' not in desc_str:
        # we have a normal name
        return etree.Element(desc_str)
    else:
        # we have a name with an attribute
        elem_name, attr_parts = split_elem_def(desc_str)
        elem = etree.Element(elem_name)

        set_elem_attrs(attr_parts, elem)

        return elem


# TODO(sross): make this work in when we have
#              an attribute selector with a '/'
#              in the value portion
def make_path(path, root, to_parent=False):
    """Like mkdir -p, but for XML."""
    parent_node = None
    parts = path.rsplit('/', 1)
    missing_parts = []
    while parent_node is None:
        if len(parts) > 1:
            missing_parts.append(parts[1])
            parent_node = root.find(parts[0])
        elif parts[0] == '':
            parent_node = root
        else:
            parent_node = root.find(parts[0])
            if parent_node is None:
                parent_node = root
                missing_parts.append(parts[0])

        parts = parts[0].rsplit('/', 1)

    if to_parent:
        stop_at = 1
    else:
        stop_at = 0

    while len(missing_parts) > stop_at:
        tag_name = missing_parts.pop()
        elem = make_elem(tag_name)
        parent_node.append(elem)
        parent_node = elem

    return parent_node


class CustomNodeValue(object):
    def __init__(self, node_path, loads, dumps):
        self._node_path = node_path
        self._loads = loads
        self._dumps = dumps

        self._cached_vals = weakref.WeakKeyDictionary()
        self._nodes = weakref.WeakKeyDictionary()

    def __get__(self, inst, type=None):
        if inst is None:
            return self

        node = self._nodes.get(inst, None)

        if node is None:
            node = self._nodes[inst] = inst._etree.find(self._node_path)

        if inst._cache and self._cached_vals.get(inst, None) is not None:
            return self._cached_vals[inst]

        if node is not None:
            res = self._loads(node)
        else:
            res = None

        if inst._cache:
            self._cached_vals[inst] = res

        return res

    def __set__(self, inst, value):
        node = self._nodes.get(inst, None)

        if node is None:
            node = self._nodes[inst] = inst._etree.find(self._node_path)

        if inst._cache:
            self._cached_vals[inst] = value

        if node is None:
            parent_node = make_path(self._node_path, inst._etree,
                                    to_parent=True)

            elem_name, attrs = split_elem_def(self._node_path)
            elem = etree.Element(elem_name)
            set_elem_attrs(attrs, elem)

            elem = self._dumps(elem, value)

            parent_node.append(elem)
            node = self._nodes[inst] = elem
        else:
            new_node = self._dumps(node, value)
            if new_node is None:
                node_parent = node.getparent()
                node_parent.remove(node)
            elif new_node is not node:
                node_parent = node.getparent()
                ind = node_parent.index(node)
                node_parent.remove(node)

                node_parent.insert(ind, node)
                self._nodes[inst] = node

    def __delete__(self, inst):
        node = self._nodes.get(inst, None)

        if node is None:
            node = inst._etree.find(self._node_path)

        if inst._cache:
            self._cached_vals[inst] = None

        if node is None:
            raise AttributeError('No such node {0}'.format(self._node_path))
        else:
            node.getparent().remove(node)
            self._nodes.pop(inst, None)

    def __repr__(self):
        return ("<XML mapping[{type}] "
                "({path})>").format(type=type(self).__name__,
                                    path=self._node_path)


class NodeValue(CustomNodeValue):
    def __init__(self, node_path, loads=six.text_type, dumps=six.text_type):
        self._node_path = node_path

        self._raw_loads = loads
        self._loads = lambda e: self._raw_loads(e.text)
        self._dumps = dumps

        self._cached_vals = weakref.WeakKeyDictionary()
        self._nodes = weakref.WeakKeyDictionary()

    def __set__(self, inst, value):
        node = self._nodes.get(inst, None)

        if node is None:
            node = self._nodes[inst] = inst._etree.find(self._node_path)

        if inst._cache:
            self._cached_vals[inst] = value

        if node is None:
            node = self._nodes[inst] = make_path(self._node_path, inst._etree)

        text_val = self._dumps(value)
        node.text = text_val

    def __repr__(self):
        return ("<XML mapping[{type}] "
                "(text of {path})>").format(type=type(self).__name__,
                                            path=self._node_path)


class ModelNodeValue(object):
    def __init__(self, node_path, model_cls, always_present=True):
        self._node_path = node_path
        self._model = model_cls
        self._nodes = weakref.WeakKeyDictionary()
        self._always_present = always_present

    def __get__(self, inst, type=None):
        if inst is None:
            return self

        node = self._nodes.get(inst, None)

        if node is None:
            node = self._nodes[inst] = inst._etree.find(self._node_path)

        if node is not None:
            return self._model(node, cache=inst._cache)
        elif self._always_present:
            node = make_path(self._node_path, inst._etree)
            obj = self._model(node, cache=inst._cache)
            self._nodes[inst] = node
            return obj
        else:
            return None

    def __set__(self, inst, value):
        node = self._nodes.get(inst, None)

        if node is None:
            node = self._nodes[inst] = inst._etree.find(self._node_path)

        if node is None:
            parent_node = make_path(self._node_path, inst._etree,
                                    to_parent=True)
            set_elem_attrs(split_elem_def(self._node_path)[1], value._etree)
            parent_node.append(value._etree)
            node = self._nodes[inst] = value._etree
        else:
            node_parent = node.getparent()
            ind = node_parent.index(node)
            node_parent.remove(node)
            set_elem_attrs(split_elem_def(self._node_path)[1], inst._etree)
            node_parent.insert(ind, value._etree)
            self._nodes[inst] = value._etree

    def __delete__(self, inst):
        node = self._nodes.get(inst, None)

        if node is None:
            node = inst._etree.find(self._node_path)

        if node is None:
            raise AttributeError('No such node {0}'.format(self._node_path))
        else:
            node.getparent().remove(node)
            self._nodes.pop(inst, None)

    def __repr__(self):
        return ("<XML mapping[{type}] ({path}) --> "
                "{model}>").format(type=type(self).__name__,
                                   path=self._node_path,
                                   model=self._model.__name__)


class AttributeValue(object):
    def __init__(self, node_path, attr_name,
                 loads=six.text_type, dumps=six.text_type):
        self._node_path = node_path
        self._attr_name = attr_name
        self._loads = loads
        self._dumps = dumps

        self._cached_vals = weakref.WeakKeyDictionary()
        self._nodes = weakref.WeakKeyDictionary()

    def __get__(self, inst, type=None):
        if inst is None:
            return self

        node = self._nodes.get(inst, None)

        if node is None:
            node = self._nodes[inst] = inst._etree.find(self._node_path)

        if inst._cache and self._cached_vals.get(inst, None) is not None:
            return self._cached_vals[inst]

        if node is not None:
            attr_val = node.get(self._attr_name, None)
            if attr_val is not None:
                res = self._loads(attr_val)
            else:
                res = None
        else:
            res = None

        if inst._cache and res is not None:
            self._cached_vals[inst] = res

        return res

    def __set__(self, inst, value):
        node = self._nodes.get(inst, None)

        if node is None:
            node = self._nodes[inst] = inst._etree.find(self._node_path)

        if inst._cache:
            self._cached_vals[inst] = value

        if node is None:
            node = self._nodes[inst] = make_path(self._node_path, inst._etree)

        text_val = self._dumps(value)
        node.set(self._attr_name, text_val)

    def __delete__(self, inst):
        node = self._nodes.get(inst, None)

        if node is None:
            node = inst._etree.find(self._node_path)

        if inst._cache:
            self._cached_vals.pop(inst, None)

        if node is None:
            raise AttributeError('No such node {0}'.format(self._node_path))
        else:
            node.attrib.pop(self._attr_name)
            self._nodes.pop(inst, None)

    def __repr__(self):
        return ('<XML mapping[{type}] '
                '("{attr}" of {path})>').format(type=type(self).__name__,
                                                path=self._node_path,
                                                attr=self._attr_name)


class NodeValueListView(object):
    def __init__(self, node_path, selector, elem_loads, elem_dumps,
                 always_present=False, full_replace=True,
                 delete_pred=lambda e: True):
        self._node_path = node_path
        self._selector = selector
        self._elem_loads = elem_loads
        self._full_replace = full_replace

        self._raw_dumps = elem_dumps

        self._elem_dumps = self._create_and_dump

        self._nodes = weakref.WeakKeyDictionary()
        self._always_present = always_present
        self._delete_pred = delete_pred

    def _create_and_dump(self, v, existing=None):
        if existing is not None and not self._full_replace:
            elem = existing
        else:
            elem = make_elem(self._selector)
        self._raw_dumps(elem, v)
        return elem

    def _child_nodes(self, node):
        return node.findall(self._selector)

    def __get__(self, inst, type=None):
        if inst is None:
            return self

        node = self._nodes.get(inst, None)

        if node is None:
            node = self._nodes[inst] = inst._etree.find(self._node_path)

            if node is None:
                if self._always_present:
                    node = self._nodes[inst] = make_path(self._node_path,
                                                         inst._etree)
                else:
                    return None

        return NodeValueListViewInst(inst, self)

    def __set__(self, inst, values):
        node = self._nodes.get(inst, None)

        if node is None:
            node = self._nodes[inst] = inst._etree.find(self._node_path)

            if node is None:
                node = self._nodes[inst] = make_path(self._node_path,
                                                     inst._etree)

        for cnode in self._child_nodes(node):
            node.remove(cnode)

        view = NodeValueListViewInst(inst, self)
        for val in values:
            view.append(val)

    def __delete__(self, inst):
        node = self._nodes.get(inst, None)

        if node is None:
            node = self._nodes[inst] = inst._etree.find(self._node_path)

        if node is None:
            raise AttributeError('No such node {0}'.format(self._node_path))
        else:
            for cnode in self._child_nodes(node):
                # TODO(sross): use delete_pred here?
                node.remove(cnode)

    def _actual_index(self, ind, node):
        child_nodes = self._child_nodes(node)
        if len(child_nodes) == 0:
            return len(node)
        if len(child_nodes) <= ind:
            return node.index(child_nodes[-1]) + 1
        else:
            return node.index(child_nodes[ind])

    def __repr__(self):
        return ("<XML mapping[{type}] ({selector} under "
                "{path})>").format(type=type(self).__name__,
                                   path=self._node_path,
                                   selector=self._selector)


class NodeValueListViewInst(collections.MutableSequence):
    def __init__(self, inst, parent):
        # TODO(sross): should this be a weak ref
        self.inst = inst
        self.parent = parent

    def __str__(self):
        return str(list(self))

    def __repr__(self):
        return ("<NodeValueListViewInst({path} / {selector}) "
                "{elems}>").format(path=self.parent._node_path,
                                   selector=self.parent._selector,
                                   elems=list(self))

    def __getitem__(self, ind):
        node = self.parent._nodes.get(self.inst, None)
        if isinstance(ind, slice):
            return [self.parent._elem_loads(e) for e
                    in self.parent._child_nodes(node)[ind]]
        else:
            return self.parent._elem_loads(self.parent._child_nodes(node)[ind])

    def __setitem__(self, ind, value):
        node = self.parent._nodes.get(self.inst, None)

        child_nodes = self.parent._child_nodes(node)

        if not isinstance(ind, slice):
            ind = slice(ind, ind + 1)
            value = [value]

        for vind, cind in enumerate(six.moves.range(ind.start,
                                                    ind.stop,
                                                    ind.step or 1)):
            act_ind = self.parent._actual_index(cind, node)
            if len(child_nodes) > cind:
                existing = child_nodes[cind]
                child_nodes[cind].getparent().remove(child_nodes[cind])
            else:
                existing = None

            node.insert(act_ind, self.parent._elem_dumps(value[vind],
                                                         existing))
            child_nodes = self.parent._child_nodes(node)

    def __delitem__(self, ind):
        node = self.parent._nodes.get(self.inst, None)

        child_nodes = self.parent._child_nodes(node)
        if isinstance(ind, slice):
            for cnode in child_nodes[ind]:
                if self.parent._delete_pred(cnode):
                    cnode.getparent().remove(cnode)
        else:
            if self.parent._delete_pred(child_nodes[ind]):
                child_nodes[ind].getparent().remove(child_nodes[ind])

    def __len__(self):
        node = self.parent._nodes.get(self.inst, None)
        return len(self.parent._child_nodes(node))

    def insert(self, ind, value):
        node = self.parent._nodes.get(self.inst, None)

        if node is None:
            raise AttributeError('No such node {0}'.format(
                self.parent._node_path))
        else:
            act_ind = self.parent._actual_index(ind, node)
            node.insert(act_ind, self.parent._elem_dumps(value))


class NodeValueList(NodeValueListView):
    def __init__(self, node_path, elem_loads, elem_dumps,
                 always_present=False):
        self._node_path = node_path
        self._elem_loads = elem_loads
        self._elem_dumps = lambda v, existing=None: elem_dumps(v)
        self._nodes = weakref.WeakKeyDictionary()
        self._always_present = always_present
        self._full_replace = True
        self._selector = '*'  # for repr
        self._delete_pred = lambda e: True

    def __delete__(self, inst):
        node = self._nodes.get(inst, None)

        if node is None:
            node = self._nodes[inst] = inst._etree.find(self._node_path)

        if node is None:
            raise AttributeError('No such node {0}'.format(self._node_path))
        else:
            node.getparent().remove(node)
            self._nodes.pop(inst, None)

    def _child_nodes(self, node):
        return node

    def _actual_index(self, ind, node):
        return ind

    def __repr__(self):
        return "<XML mapping[{type}] (* under {path})".format(
            type=type(self).__name__, path=self._node_path)


class Model(object):
    ROOT_ELEM = 'elem'

    def __init__(self, content=None, cache=False):
        if content is None:
            self._etree = etree.Element(self.ROOT_ELEM)
        elif isinstance(content, six.string_types):
            self._etree = etree.fromstring(content)
        else:
            self._etree = content

        if self._etree.tag != self.ROOT_ELEM:
            raise ValueError('This model should have a root tag of {root}, '
                             'but the input had a root tag of {actual}'.format(
                                 root=self.ROOT_ELEM,
                                 actual=self._etree.tag))

        self._cache = cache

    def __str__(self):
        if six.PY2:
            return self.to_xml()
        else:
            return self.to_xml(encoding=str)

    def __bytes__(self):
        return self.to_xml()

    def __unicode__(self):
        return self.to_xml(encoding=six.text_type)

    def to_xml(self, *args, **kwargs):
        return etree.tostring(self._etree, *args, **kwargs)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        return self._etree == other._etree

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return ("<XML Mapping Model[{type}] "
                "caching={cache}>").format(type=type(self).__name__,
                                           cache=self._cache)

    def __hash__(self):
        return hash(self._etree)
