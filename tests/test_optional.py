import json

import pytest

from implicitdict import ImplicitDict

from .test_types import OptionalData


def test_fully_defined():
    data = OptionalData.example_values()["fully_defined"]
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
    data = OptionalData.example_values()["over_defined"]
    d = json.loads(json.dumps(data))
    d["another_unknown_field"] = {"third_unknown_field": "foo7"}
    _ = ImplicitDict.parse(d, OptionalData)


def test_minimally_defined():
    # An unspecified optional field will not be present in the object at all
    data = OptionalData.example_values()["minimally_defined"]
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
    data = OptionalData.example_values()["provide_optional_field"]
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
    data = OptionalData.example_values()["provide_optional_field_as_none"]
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
    data = OptionalData.example_values()["provide_optional_field_with_none_default_as_none"]
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
    data = OptionalData.example_values()["provide_optional_field_with_default_as_none"]
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
