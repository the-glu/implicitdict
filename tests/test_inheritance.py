import json
from typing import Optional

from implicitdict import ImplicitDict


class MyData(ImplicitDict):
    foo: str
    bar: int = 0
    baz: Optional[float]
    has_default_baseclass: str = "In MyData"

    def hello(self) -> str:
        return "MyData"

    def base_method(self) -> int:
        return 123


class MySubclass(MyData):
    buzz: Optional[str]
    has_default_subclass: str = "In MySubclass"

    def hello(self) -> str:
        return "MySubclass"


def test_inheritance():
    data: MyData = ImplicitDict.parse({'foo': 'asdf', 'bar': 1}, MyData)
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

    data2 = MyData(subclass)
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
