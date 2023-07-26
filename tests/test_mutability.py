from implicitdict import ImplicitDict

from .test_types import MutabilityData


def test_mutability_from_constructor():
    primitive = 'foobar'
    primitive_list = ['one', 'two']
    generic_dict = {'level1': 'foo', 'level2': {'bar': 'baz'}}
    data = MutabilityData(primitive=primitive, list_of_primitives=primitive_list, generic_dict=generic_dict)
    assert data.primitive == primitive
    assert data.list_of_primitives == primitive_list
    assert data.generic_dict == generic_dict

    primitive = 'foobar2'
    assert data.primitive != primitive

    primitive_list[1] = 'three'
    assert data.list_of_primitives[1] == 'three'

    generic_dict['level1'] = 'bar'
    assert data.generic_dict['level1'] == 'bar'

    generic_dict['level2']['bar'] = 'buzz'
    assert data.generic_dict['level2']['bar'] == 'buzz'


def test_mutability_from_parse():
    primitive = 'foobar'
    primitive_list = ['one', 'two']
    generic_dict = {'level1': 'foo', 'level2': {'bar': 'baz'}}
    data_source = MutabilityData(primitive=primitive, list_of_primitives=primitive_list, generic_dict=generic_dict)
    data: MutabilityData = ImplicitDict.parse(data_source, MutabilityData)
    assert data.primitive == primitive
    assert data.list_of_primitives == primitive_list
    assert data.generic_dict == generic_dict

    primitive = 'foobar2'
    assert data.primitive != primitive

    primitive_list[1] = 'three'
    assert data.list_of_primitives[1] == 'two'  # <-- lists are reconstructed with `parse`

    generic_dict['level1'] = 'bar'
    assert data.generic_dict['level1'] == 'foo'  # <-- dicts are reconstructed with `parse`

    generic_dict['level2']['bar'] = 'buzz'
    assert data.generic_dict['level2']['bar'] == 'buzz'
