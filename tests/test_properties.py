import json

from implicitdict import ImplicitDict


class MyData(ImplicitDict):
    foo: str

    @property
    def bar(self) -> str:
        return self.foo + 'bar'

    def get_baz(self) -> str:
        return self.foo + 'baz'

    def set_baz(self, value: str) -> None:
        self.foo = value

    baz = property(get_baz, set_baz)

    @property
    def booz(self) -> str:
        return self.foo + 'booz'

    @booz.setter
    def booz(self, value: str) -> None:
        self.foo = value


def test_property_exclusion():
    """Ensure implicitdict doesn't serialize dynamic properties.

    Properties of a class instance are computed dynamically -- they are
    methods with syntactic sugar which makes them look like fields.  Because we
    shouldn't serialize the result of a class method, we also shouldn't
    serialize the result of a class property, even if that property includes a
    setter.
    """
    # Create class instance and ensure it works as expected
    data = MyData(foo='foo')
    assert data.bar == 'foobar'
    assert data.baz == 'foobaz'
    assert data.booz == 'foobooz'

    # Serialize class instance and ensure the properties weren't serialized
    obj = json.loads(json.dumps(data))
    assert 'bar' not in obj
    assert 'baz' not in obj
    assert 'booz' not in obj

    # Ensure serialization can be deserialized to class instance
    data: MyData = ImplicitDict.parse(obj, MyData)

    # Ensure deserialized instance works as expected
    assert data.bar == 'foobar'
    assert data.baz == 'foobaz'
    assert data.booz == 'foobooz'


class MyDict(dict):
    @property
    def foo(self) -> str:
        return 'foo'

    def get_bar(self) -> str:
        return self.foo + 'bar'

    def set_bar(self, value: str) -> None:
        self['bar'] = value

    bar = property(get_bar, set_bar)

    @property
    def baz(self) -> str:
        return self.foo + 'baz'

    @baz.setter
    def baz(self, value: str) -> None:
        self['baz'] = value


def test_dict_inheritance():
    """Demonstrate that classes inheriting dict do not have their properties serialized."""
    data = MyDict()
    assert data.foo == 'foo'
    assert data.bar == 'foobar'
    assert data.baz == 'foobaz'

    data['booz'] = 'biz'
    deserialized = json.loads(json.dumps(data))

    assert 'foo' not in deserialized
    assert 'bar' not in deserialized
    assert 'baz' not in deserialized
    assert deserialized['booz'] == 'biz'
