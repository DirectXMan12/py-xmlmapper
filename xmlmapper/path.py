def _parse_slice(ind):
    return "{attr}='{val}'".format(attr=ind.start, val=ind.stop)


class PathElem(object):
    def __getitem__(self, ind):
        if isinstance(ind, tuple):
            new_ind = ind[0]
        else:
            new_ind = ind

        if isinstance(new_ind, slice):
            new_ind = _parse_slice(new_ind)

        res = AttrSelectorPathElem(self._path, new_ind)

        if isinstance(ind, tuple) and len(ind) > 1:
            return res[ind[1:]]
        else:
            return res

    def __getattr__(self, name):
        return TagPathElem(self._path, name)

    def __repr__(self):
        return "<{name}({path})>".format(name=type(self).__name__,
                                         path=self._path)

    def __str__(self):
        return self._path

    def __eq__(self, other):
        if not isinstance(other, PathElem):
            return False
        else:
            return self._path == other._path

    def __ne__(self, other):
        return not self.__eq__(other)


class TagPathElemBase(object):
    def __init__(self, parent_path, name):
        self._parent_path = parent_path
        self._name = name

    @property
    def _path(self):
        if self._parent_path is None:
            return self._name
        elif self._parent_path[-1] == '/':
            return self._parent_path + self._name
        else:
            return self._parent_path + '/' + self._name

    def __str__(self):
        return self._path

    def __radd__(self, previous):
        # TODO(sross): handle strings?
        if self._path[0] == '/':
            return TagPathElem(self._parent_path, self._name)
        else:
            return PathElem(previous._path + '/' + self._parent_path,
                            self._name)


class TagPathElem(PathElem, TagPathElemBase):
    pass


class AttrSelectorPathElemBase(object):
    def __init__(self, tag_path, attribute):
        self._tag_path = tag_path
        self._attribute = attribute

    @property
    def _path(self):
        if self._tag_path is None:
            return '*[@' + self._attribute + ']'
        else:
            return self._tag_path + '[@' + self._attribute + ']'

    def __radd__(self, previous):
        return AttrSelectorPathElem(previous._path, self._attribute)


class AttrSelectorPathElem(PathElem, AttrSelectorPathElemBase):
    pass


def tag(name):
    return TagPathElem(None, name)


def root_tag(name):
    return TagPathElem('/', name)


ROOT = TagPathElem(None, '.')
