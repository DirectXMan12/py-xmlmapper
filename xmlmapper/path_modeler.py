import collections
import copy

from xmlmapper import core_modeler as core
from xmlmapper.core_modeler import Model
from xmlmapper import path


class DescPathElem(object):
    def __getattr__(self, name):
        return NodeValuePathElem(self._path, name)

    def __getitem__(self, ind):
        if ind is Ellipsis:
            return NodeValueListPathElem(self._path)

        if isinstance(ind, tuple):
            new_ind = ind[0]
        else:
            new_ind = ind

        if isinstance(new_ind, slice):
            new_ind = path._parse_slice(new_ind)

        res = AttributeValuePathElem(self._path, new_ind)

        if isinstance(ind, tuple) and len(ind) > 1:
            return res[ind[1:]]
        else:
            return res

    def __mod__(self, mod_spec):
        new_obj = copy.copy(self)
        if isinstance(mod_spec, type):
            if issubclass(mod_spec, Model):
                return self._with_model(new_obj, mod_spec)
            elif issubclass(mod_spec, Custom):
                return self._with_custom(new_obj, None, None)
        elif isinstance(mod_spec, Custom):
            return self._with_custom(new_obj, mod_spec.loads, mod_spec.dumps)
        elif isinstance(mod_spec, collections.Mapping):
            return self._set_options(new_obj, **mod_spec)
        else:
            return self._with_loads_dumps(new_obj, *mod_spec)

    def _with_model(self, new_obj, model):
        raise AttributeError("'{type}' object cannot be formatted with "
                             "a model.".format(
                                 type=type(self).__name__))

    def _with_loads_dumps(self, new_obj, loads, dumps):
        raise AttributeError("'{type}' object cannot be formatted with "
                             "'loads'and 'dumps' methods".format(
                                 type=type(self).__name__))

    def _set_options(self, new_obj):
        raise AttributeError("'{type}' object has no options"
                             "to set".format(type=type(self).__name__))

    def _with_custom(self, new_obj, loads, dumps):
        raise AttributeError("'{type}' object cannot be formatted with a "
                             "custom mapping.".format(
                                 type=type(self).__name__))


class BasicPathElem(DescPathElem):
    def _with_model(self, new_obj, model):
        return ModelNodeValuePathElem(self._path, model)

    def _with_loads_dumps(self, new_obj, loads, dumps):
        new_obj._loads = loads
        new_obj._dumps = dumps

        return new_obj

    def _set_options(self, new_obj, loads=None, dumps=None):
        return self._with_loads_dumps(new_obj,
                                      loads or self._loads,
                                      dumps or self._dumps)

    def _with_custom(self, new_obj, loads, dumps):
        return CustomNodeValuePathElem(new_obj._path, loads, dumps)


class NodeValuePathElem(BasicPathElem, core.NodeValue, path.TagPathElemBase):
    def __init__(self, parent_path, name):
        path.TagPathElemBase.__init__(self, parent_path, name)
        core.NodeValue.__init__(self, self._path)

    def __copy__(self):
        new_obj = type(self)(self._parent_path, self._name)
        new_obj._raw_loads = self._raw_loads
        new_obj._dumps = self._dumps

        return new_obj

    def _with_loads_dumps(self, new_obj, loads, dumps):
        new_obj._raw_loads = loads
        new_obj._dumps = dumps

        return new_obj


class CustomNodeValuePathElem(DescPathElem, core.CustomNodeValue):
    def __init__(self, node_path, loads, dumps):
        core.CustomNodeValue.__init__(self, node_path, loads, dumps)

    def __copy__(self):
        new_obj = type(self)(self._node_path)
        new_obj._loads = self._loads
        new_obj._dumps = self._dumps

        return new_obj

    def _with_loads_dumps(self, new_obj, loads, dumps):
        new_obj._loads = loads
        new_obj._dumps = dumps

        return new_obj

    def _set_options(self, new_obj, loads=None, dumps=None):
        return self._with_loads_dumps(new_obj,
                                      loads or self._loads,
                                      dumps or self._dumps)


class AttributeValuePathElem(BasicPathElem, core.AttributeValue,
                             path.AttrSelectorPathElemBase):
    def __init__(self, tag_path, attribute):
        path.AttrSelectorPathElemBase.__init__(self, tag_path, attribute)
        core.AttributeValue.__init__(self, tag_path, attribute)

    def __copy__(self):
        new_obj = type(self)(self._tag_path, self._attribute)
        new_obj._loads = self._loads
        new_obj._dumps = self._dumps

        return new_obj


class NodeValueListPathElem(DescPathElem, core.NodeValueList):
    def __init__(self, path):
        self._path = path
        core.NodeValueList.__init__(self, path, None, None)

    def _with_model(self, new_obj, model):
        new_obj._elem_loads = lambda e: model(e)
        new_obj._elem_dumps = lambda m: m._etree

    def _with_loads_dumps(self, new_obj, loads, dumps):
        new_obj._elem_loads = loads
        new_obj._elem_dumps = lambda v, existing=None: dumps(v)

        return new_obj

    def _set_options(self, new_obj, loads=None, dumps=None,
                     elem_loads=None, elem_dumps=None,
                     always_present=None):
        loads = loads or elem_loads or self._elem_loads
        dumps = dumps or elem_dumps or self._raw_dumps

        if always_present is not None:
            new_obj._always_present = always_present

        return self._with_loads_dumps(new_obj, loads, dumps)

    def __getattr__(self, name):
        return NodeValueListViewTagPathElem(self._path, name)

    def __getitem__(self, ind):
        raise TypeError("'{0}' object as no attribute "
                        "'__getitem__'".format(type(self)))

    def __copy__(self):
        new_obj = type(self)(self._node_path)
        new_obj._elem_loads = self._elem_loads
        new_obj._elem_dumps = self._elem_dumps
        new_obj._always_present = self._always_present

        return new_obj


class NodeValueListViewTagPathElem(DescPathElem, core.NodeValueListView):
    def __init__(self, parent_path, name):
        core.NodeValueListView.__init__(self, parent_path, name,
                                        None, None)

    def _with_model(self, new_obj, model):
        new_obj._elem_loads = lambda e: model(e)
        new_obj._elem_dumps = lambda m, e: m._etree
        new_obj._full_replace = True

        return new_obj

    def _with_loads_dumps(self, new_obj, loads, dumps, delete_pred=None):
        new_obj._elem_loads = loads
        new_obj._raw_dumps = dumps

        if delete_pred is not None:
            new_obj._delete_pred = delete_pred

        return new_obj

    def _set_options(self, new_obj, loads=None, dumps=None,
                     elem_loads=None, elem_dumps=None,
                     full_replace=None, always_present=None):
        loads = loads or elem_loads or self._elem_loads
        dumps = dumps or elem_dumps or self._raw_dumps

        if full_replace is not None:
            new_obj._full_replace = full_replace

        if always_present is not None:
            new_obj._always_present = always_present

        return self._with_loads_dumps(new_obj, loads, dumps)

    def __getitem__(self, ind):
        if isinstance(ind, slice):
            new_ind = path._parse_slice(ind)
        elif isinstance(ind, tuple):
            new_ind = ind[0]
        else:
            new_ind = ind

        selector = self._selector + '[@' + new_ind + ']'
        res = NodeValueListViewAttributePathElem(self._node_path,
                                                 selector)

        if isinstance(ind, tuple) and len(ind) > 1:
            return res[ind[1:]]
        else:
            return res

    def __getattr__(self, name):
        raise AttributeError("'{type}' object has "
                             "no attribute '{attr}'".format(type=type(self),
                                                            attr=name))

    def __copy__(self):
        new_obj = type(self)(self._node_path, self._selector)
        new_obj._elem_loads = self._elem_loads,
        new_obj._raw_dumps = self._raw_dumps
        new_obj._full_replace = self._full_replace
        new_obj._always_present = self._always_present

        return new_obj


class NodeValueListViewAttributePathElem(NodeValueListViewTagPathElem):
    def __init__(self, node_path, selector):
        core.NodeValueListView.__init__(self, node_path, selector,
                                        None, None)

    def __copy__(self):
        new_obj = type(self)(self._node_path, self._selector)
        new_obj._elem_loads = self._elem_loads,
        new_obj._raw_dumps = self._raw_dumps
        new_obj._full_replace = self._full_replace
        new_obj._always_present = self._always_present

        return new_obj


class ModelNodeValuePathElem(core.ModelNodeValue):
    def __mod__(self, mod_spec):
        if isinstance(mod_spec, collections.Mapping):
            new_obj = copy.copy(self)
            return self._set_options(new_obj, **mod_spec)
        else:
            raise ValueError('Cannot format a ModelNodeValuePathElem '
                             'with anything but a mapping')

    def _set_options(self, new_obj, always_present=None):
        if always_present is not None:
            new_obj._always_present = always_present

        return new_obj

    def __copy__(self):
        return type(self)(self._node_path, self._model, self._always_present)


def tag(name):
    return NodeValuePathElem(None, name)


def root_tag(name):
    return NodeValuePathElem('/', name)


ROOT = NodeValuePathElem(None, '.')


class Custom(object):
    def __init__(self, loads, dumps):
        self.loads = loads
        self.dumps = dumps
