import json
from typing import Optional

import pytest

from implicitdict import ImplicitDict


class MyData(ImplicitDict):
    required_field: str
    optional_field1: Optional[str]
    field_with_default: str = "default value"
    optional_field2_with_none_default: Optional[str] = None
    optional_field3_with_default: Optional[str] = "concrete default"


def test_fully_defined():
    data = MyData(
        required_field="foo1",
        optional_field1="foo2",
        field_with_default="foo3",
        optional_field2_with_none_default="foo4",
        optional_field3_with_default="foo5",
    )
    assert "required_field" in data
    assert "optional_field1" in data
    assert "field_with_default" in data
    assert "optional_field2_with_none_default" in data
    assert "optional_field3_with_default" in data
    s = json.dumps(data)
    assert "required_field" in s
    assert "optional_field1" in s
    assert "field_with_default" in s
    assert "optional_field2" in s
    assert "optional_field3" in s
    assert "foo1" in s
    assert "foo2" in s
    assert "foo3" in s
    assert "foo4" in s
    assert "foo5" in s


def test_over_defined():
    data = MyData(
        required_field="foo1",
        optional_field1="foo2",
        field_with_default="foo3",
        optional_field2_with_none_default="foo4",
        optional_field3_with_default="foo5",
        unknown_field="foo6",
    )
    d = json.loads(json.dumps(data))
    d["another_unknown_field"] = {"third_unknown_field": "foo7"}
    _ = ImplicitDict.parse(d, MyData)


def test_minimally_defined():
    # An unspecified optional field will not be present in the object at all
    data = MyData(required_field="foo1")
    assert "required_field" in data
    assert "optional_field1" not in data
    assert "field_with_default" in data
    assert "optional_field2_with_none_default" in data
    assert "optional_field3_with_default" in data
    with pytest.raises(KeyError):
        # Trying to reference the Optional field will result in a KeyError
        # To determine whether an Optional field is present, the user must check
        # whether `"<FIELD_NAME>" in <OBJECT>` (see above).
        assert data.optional_field1 == None
    s = json.dumps(data)
    assert "required_field" in s
    assert "optional_field1" not in s
    assert "field_with_default" in s
    assert "optional_field2" in s
    assert "optional_field3" in s
    assert "foo1" in s


def test_provide_optional_field():
    data = MyData(required_field="foo1", optional_field1="foo2")
    assert "required_field" in data
    assert "optional_field1" in data
    assert "field_with_default" in data
    assert "optional_field2_with_none_default" in data
    assert "optional_field3_with_default" in data
    s = json.dumps(data)
    assert "required_field" in s
    assert "optional_field1" in s
    assert "field_with_default" in s
    assert "optional_field2" in s
    assert "optional_field3" in s
    assert "foo1" in s
    assert "foo2" in s


def test_provide_optional_field_as_none():
    # If an optional field with no default is explicitly provided as None, then that field will not be included in the object
    data = MyData(required_field="foo1", optional_field1=None)
    assert "required_field" in data
    assert "optional_field1" not in data  # <--
    assert "field_with_default" in data
    assert "optional_field2_with_none_default" in data
    assert "optional_field3_with_default" in data
    s = json.dumps(data)
    assert "required_field" in s
    assert "optional_field1" not in s  # <--
    assert "field_with_default" in s
    assert "optional_field2" in s
    assert "optional_field3" in s
    assert "foo1" in s


def test_provide_optional_field_with_none_default_as_none():
    # If a field has a default value, the field will always be present in the object, even if that default value is None and the field is Optional
    data = MyData(required_field="foo1", optional_field2_with_none_default=None)
    assert "required_field" in data
    assert "optional_field1" not in data
    assert "field_with_default" in data
    assert "optional_field2_with_none_default" in data  # <--
    assert "optional_field3_with_default" in data
    s = json.dumps(data)
    assert "required_field" in s
    assert "optional_field1" not in s
    assert "field_with_default" in s
    assert "optional_field2" in s  # <--
    assert "optional_field3" in s
    assert "foo1" in s


def test_provide_optional_field_with_default_as_none():
    # If a field has a default value, the field will always be present in the object
    data = MyData(required_field="foo1", optional_field3_with_default=None)
    assert "required_field" in data
    assert "optional_field1" not in data
    assert "field_with_default" in data
    assert "optional_field2_with_none_default" in data
    assert "optional_field3_with_default" in data  # <--
    s = json.dumps(data)
    assert "required_field" in s
    assert "optional_field1" not in s
    assert "field_with_default" in s
    assert "optional_field2" in s
    assert "optional_field3" in s  # <--
    assert "foo1" in s
