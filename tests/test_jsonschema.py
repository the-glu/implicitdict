import json
from typing import Type

import implicitdict.jsonschema
from implicitdict.jsonschema import SchemaVars
from implicitdict import ImplicitDict
import jsonschema

from .test_types import ContainerData, InheritanceData, NestedDefinitionsData, NormalUsageData, OptionalData, \
    PropertiesData, SpecialTypesData, SpecialSubclassesContainer


def _resolver(t: Type) -> SchemaVars:
    def path_to(t_dest: Type, t_src: Type) -> str:
        return "#/definitions/" + t_dest.__module__ + t_dest.__qualname__

    full_name = t.__module__ + t.__qualname__

    return SchemaVars(name=full_name, path_to=path_to)


def _verify_schema_validation(obj, obj_type: Type[ImplicitDict]) -> None:
    repo = {}
    implicitdict.jsonschema.make_json_schema(obj_type, _resolver, repo)

    name = _resolver(obj_type).name
    schema = repo[name]
    del repo[name]
    if repo:
        schema["definitions"] = repo

    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)

    pure_json = json.loads(json.dumps(obj))

    error_messages = []
    for e in validator.iter_errors(pure_json):
        errors = [e]
        while errors:
            this_error = errors.pop(0)
            if this_error.context:
                for child in this_error.context:
                    errors.append(child)
            else:
                error_messages.append(f"[{this_error.json_path}] {this_error.message}")
    assert not error_messages, "\n".join(error_messages)


def test_basic_usage():
    data: NormalUsageData = ImplicitDict.parse({'foo': 'asdf', 'bar': 1}, NormalUsageData)
    _verify_schema_validation(data, NormalUsageData)


def test_field_docstrings():
    repo = {}
    implicitdict.jsonschema.make_json_schema(NormalUsageData, _resolver, repo)
    name = _resolver(NormalUsageData).name
    schema = repo[name]
    props = schema["properties"]

    assert props["foo"]["description"] == "The foo characterizing the data."
    assert props["bar"]["description"] == "The bar of the data.\n\nIndents should not be included in docstrings."
    assert props["baz"]["description"] == "If this baz is specified, it provides additional information.\n\nFinal docstring newlines should be omitted."


def test_containers():
    containers: ContainerData = ContainerData.example_value()
    _verify_schema_validation(containers, ContainerData)


def test_inheritance():
    data = InheritanceData.example_value()
    _verify_schema_validation(data, InheritanceData)

    data = SpecialSubclassesContainer.example_value()
    _verify_schema_validation(data, SpecialSubclassesContainer)
    repo = {}
    implicitdict.jsonschema.make_json_schema(SpecialSubclassesContainer, _resolver, repo)
    name = _resolver(SpecialSubclassesContainer).name
    schema = repo[name]
    props = schema["properties"]
    assert "special_list" in props
    assert "special_complex_list" in props


def test_optional():
    for data in OptionalData.example_values().values():
        _verify_schema_validation(data, OptionalData)


def test_properties():
    data = PropertiesData.example_value()
    _verify_schema_validation(data, PropertiesData)


def test_special_types():
    data = SpecialTypesData.example_value()
    _verify_schema_validation(data, SpecialTypesData)


def test_nested_definitions():
    data = NestedDefinitionsData.example_value()
    _verify_schema_validation(data, NestedDefinitionsData)
