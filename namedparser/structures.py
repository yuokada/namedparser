# -*- coding: utf-8 -*-
from __future__ import (division, absolute_import, )

from pyparsing import ParseResults

'''
===========================
ノードクラスの命名規則
===========================

original: lower and hyphened
class: UpperCamel
'''


def _camel_to_hyphened(text):
    letters = list(text)
    first_letter = letters.pop(0).lower()
    conv = lambda _s: '-' + _s.lower() if _s.isupper() else _s
    return first_letter + ''.join([conv(v) for v in letters])


class Results(object):
    """ Wrapper of pyparsing.ParseResults
    """

    def __init__(self, parse_result):
        self.values = parse_result

    def __getitem__(self, k):
        return self.values[k]

    def __str__(self):
        return '\n'.join(str(v) for v in self.values)

    def search(self, node_type):
        return [v for v in self.values
                if hasattr(v, 'is_same_nodetype') and v.is_same_nodetype(node_type)]


class ValueDefinitions(object):
    def __str__(self):
        return '{0} {1};'.format(self['node_type'], self['value'])

    def __repr__(self):
        return self.__str__()

    def __add__(self, other):
        return str(self) + str(other)

    def is_same_nodetype(self, nodetype):
        """
        this method cannot detect unknown node
        TODO: unknownもわかったほうがよいかな？
        """
        if isinstance(nodetype, str):
            return _camel_to_hyphened(self.__class__.__name__) == nodetype
        else:
            return type(nodetype) == type(self)

    def asList(self):
        return [self['node_type'], self['value']]


class QuotedValuePossesiable(ValueDefinitions):
    def __str__(self):
        return '{0} "{1}";'.format(self['node_type'], self['value'])


class EasyAcceesser(object):
    def __getattr__(self, name):
        return self[name]


# =================

def _detect_firstvalue(var):
    if isinstance(var, ParseResults):
        return var[0]
    if isinstance(var, str):
        return var
    return var[0]


class UnknowNode(ValueDefinitions, EasyAcceesser, dict):
    def __init__(self, parse_result):
        assert 'node_type' in parse_result and 'value' in parse_result
        super(UnknowNode, self).__init__(
            node_type=parse_result['node_type'],
            value=_detect_firstvalue(parse_result['value'])
        )

    def is_same_nodetype(self, nodetype):
        """ """
        return self.node_type == nodetype


class Include(QuotedValuePossesiable, EasyAcceesser, dict):
    def __init__(self, parse_result):
        super(Include, self).__init__(
            node_type=parse_result['node_type'],
            value=_detect_firstvalue(parse_result['value']),
        )


class Directory(QuotedValuePossesiable, EasyAcceesser, dict):
    def __init__(self, parse_result):
        super(Directory, self).__init__(
            node_type=parse_result['node_type'],
            value=_detect_firstvalue(parse_result['value']),
        )


class Algorithm(ValueDefinitions, EasyAcceesser, dict):
    def __init__(self, parse_result):
        super(Algorithm, self).__init__(
            node_type=parse_result['node_type'],
            value=_detect_firstvalue(parse_result['value']),
        )


class Secret(QuotedValuePossesiable, EasyAcceesser, dict):
    def __init__(self, parse_result):
        super(Secret, self).__init__(
            node_type=parse_result['node_type'],
            value=_detect_firstvalue(parse_result['value']),
        )


class CheckNames(ValueDefinitions, EasyAcceesser, dict):
    def __init__(self, parse_result):
        if isinstance(parse_result, self.__class__):
            super(CheckNames, self).__init__(
                node_type=parse_result['node_type'],
                target=parse_result['target'],
                value=parse_result['value'],
            )
        else:
            super(CheckNames, self).__init__(
                node_type=parse_result['node_type'],
                target=parse_result['value'][0],
                value=parse_result['value'][1],
            )

    def __str__(self):
        return '{0} {1} {2};'.format(self['node_type'], self['target'], self['value'], )

    def asList(self):
        return [self['node_type'], self['target'], self['value']]


class Options(ValueDefinitions, EasyAcceesser, dict):
    def __init__(self, parse_result):
        assert parse_result['node_type'] == 'options'
        super(Options, self).__init__(
            node_type=parse_result['node_type'],
            value=parse_result['value'],
        )

    def __str__(self):
        v = str(self['value'])
        return 'options {\n' + v + '\n};'

    def search(self, node_type):
        return self.value.search(node_type)


class Zone(ValueDefinitions, EasyAcceesser, dict):
    def __init__(self, parse_result):
        assert parse_result['node_type'] == 'zone'
        super(Zone, self).__init__(
            node_type=parse_result['node_type'],
            name=parse_result['name'],
            value=parse_result['value'],
        )

    def __str__(self):
        v = str(self['value'])
        return 'zone ' + self['name'] + ' {\n' + v + '\n};'

    def search(self, node_type):
        return self.value.search(node_type)

    def __contains__(self, node_type):
        return node_type in self.value.keys


class Key(ValueDefinitions, EasyAcceesser, dict):
    def __init__(self, parse_result):
        value = parse_result['value']
        super(Key, self).__init__(
            node_type=parse_result['node_type'],
            name=parse_result['name'],
            algorithm=value.search('algorithm')[0],
            secret=value.search('secret')[0],
        )

    def __str__(self):
        return '\n'.join([
            'key {\n',
            'algorithm ' + str(self['algorithm']) + ';',
            'secret ' + str(self['secret']) + ';',
            '};'
        ])


class Acl(ValueDefinitions, EasyAcceesser, dict):
    def __init__(self, parse_result):
        super(Acl, self).__init__(
            node_type=parse_result['node_type'],
            name=parse_result['name'],
            value=parse_result['value'],
        )

    def __str__(self):
        v = str(self['value'])
        return 'acl {\n' + v + '\n};'

    def search(self, node_type):
        return self.value.search(node_type)


class Inet(ValueDefinitions, EasyAcceesser, dict):
    def __init__(self, parse_result):
        port = parse_result['port']['value'] if 'port' in list(parse_result.keys()) else ''
        super(Inet, self).__init__(
            node_type=parse_result['node_type'],
            ipaddr=parse_result['ipaddr'],
            port=port,
            allows=parse_result['allow-section']['value'],
            keys=parse_result['keys-section']['value'],
        )

    def __str__(self):
        port = ''
        if self['port']:
            port = ' port ' + self['port']
        return (
                'inet ' + self['ipaddr'] + port +
                ' allow ' + str(self['allows']) +
                ' keys ' + str(self['keys']) +
                ';'
        )


class Controls(ValueDefinitions, EasyAcceesser, dict):
    def __init__(self, parse_result):
        super(Controls, self).__init__(
            node_type=parse_result['node_type'],
            value=parse_result['inet-node'],
        )

    def __str__(self):
        v = str(self['value'])
        return 'controls {\n' + v + '\n};'

    def search(self, node_type):
        return self.value.search(node_type)


class DefinitionsContainer(object):
    """
    :warning:
        the handler of setParseAction should not return type of list.
    """

    def __init__(self, var):
        self.values = var
        self.keys = set(v.node_type for v in var)

    def __iter__(self):
        return self.values.__iter__()

    def __str__(self):
        return '\n'.join(str(v) for v in self.values)

    def search(self, node_type):
        return [v for v in self.values
                if v.is_same_nodetype(node_type)]

    def __contains__(self, node_type):
        return node_type in self.keys


class ValueLists(object):
    def __init__(self, var, quot=''):
        self.values = var
        self.quot = quot

    def __iter__(self):
        return self.values.__iter__()

    def __str__(self):
        q = self.quot
        return '{\n' + ';\n'.join(q + str(v) + q for v in self.values) + ';\n}'


StructuresDetection = dict(
    (_camel_to_hyphened(obj.__name__), obj)
    for obj in [
        Include,
        Directory,
        CheckNames,
        Options,
        Zone,
        Key,
        Algorithm,
        Secret,
        Acl,
        Inet,
        Controls,
    ]
)
