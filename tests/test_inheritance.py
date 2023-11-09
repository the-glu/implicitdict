import json

from implicitdict import ImplicitDict

from .test_types import InheritanceData, MySubclass, SpecialSubclassesContainer, SpecialListClass, MySpecialClass, \
    SpecialComplexListClass


def test_inheritance():
    data: InheritanceData = InheritanceData.example_value()
    assert json.loads(json.dumps(data)) == {"foo": "asdf", "bar": 1, "has_default_baseclass": "In MyData"}
    assert data.hello() == "MyData"
    assert data.has_default_baseclass == "In MyData"

    subclass: MySubclass = ImplicitDict.parse(json.loads(json.dumps(data)), MySubclass)
    assert subclass.foo == "asdf"
    assert subclass.bar == 1
    assert "baz" not in subclass
    assert subclass.hello() == "MySubclass"
    assert subclass.base_method() == 123
    subclass.buzz = "burrs"
    assert subclass.has_default_baseclass == "In MyData"
    assert subclass.has_default_subclass == "In MySubclass"
    subclass.has_default_baseclass = "In MyData 2"
    subclass.has_default_subclass = "In MySubclass 2"

    subclass = MySubclass(data)
    assert subclass.foo == "asdf"
    assert subclass.bar == 1
    assert "baz" not in subclass
    assert subclass.hello() == "MySubclass"
    assert subclass.base_method() == 123
    assert "buzz" not in subclass
    subclass.buzz = "burrs"
    assert subclass.has_default_baseclass == "In MyData"
    assert subclass.has_default_subclass == "In MySubclass"
    subclass.has_default_baseclass = "In MyData 3"
    subclass.has_default_subclass = "In MySubclass 3"

    data2 = InheritanceData(subclass)
    assert data2.foo == "asdf"
    assert data2.bar == 1
    assert "baz" not in data2
    assert data2.hello() == "MyData"
    assert "buzz" not in data2
    assert data2.has_default_baseclass == "In MyData 3"
    data2.has_default_baseclass = "In MyData 4"

    subclass2 = MySubclass(subclass)
    assert subclass2.buzz == "burrs"
    assert subclass.has_default_baseclass == "In MyData 3"
    assert subclass.has_default_subclass == "In MySubclass 3"


def test_inherited_classes():
    data: SpecialSubclassesContainer = SpecialSubclassesContainer.example_value()
    assert isinstance(data.special_list, SpecialListClass)
    assert data.special_list.hello() == "SpecialListClass"
    for item in data.special_list:
        assert isinstance(item, MySpecialClass)
        assert item.is_special

    assert isinstance(data.special_complex_list, SpecialComplexListClass)
    assert data.special_complex_list.hello() == "SpecialComplexListClass"
    for item in data.special_complex_list:
        assert isinstance(item, MySubclass)
        assert item.hello() == "MySubclass"
