import inspect
from dataclasses import dataclass
from datetime import datetime
import enum
import json
import re
from typing import get_args, get_origin, get_type_hints, Dict, Literal, Optional, Type, Union, Tuple, Callable

from . import ImplicitDict, _fullname, _get_fields, StringBasedDateTime, StringBasedTimeDelta


@dataclass
class SchemaVars(object):
    name: str
    """Unique name that can be used to reference this type/schema."""

    path_to: Optional[Callable[[Type, Type], str]] = None
    """Function to compute $ref path to schema describing the first type from the schema describing the second type"""

    schema_id: Optional[str] = None
    """ID of the schema describing this type.  Will be used to populate $schema."""

    description: Optional[str] = None
    """Description of this type/schema."""


SchemaVarsResolver = Callable[[Type], SchemaVars]
"""Function producing the characteristics of a schema (SchemaVars) for a given Type."""

_implicitdict_doc = inspect.getdoc(ImplicitDict)


def make_json_schema(
        schema_type: Type[ImplicitDict],
        schema_vars_resolver: SchemaVarsResolver,
        schema_repository: Dict[str, dict],
) -> None:
    """Create JSON Schema for the specified schema type and all dependencies.

    Args:
        schema_type: ImplicitDict subclass to produce JSON Schema for.
        schema_vars_resolver: Mapping between Python Type and characteristics of the schema for that type.
        schema_repository: Mapping from reference path (see reference_resolver) to JSON Schema for the corresponding
            type.  The schema for schema_type will be populated in this repository, along with all other nested types.
    """
    schema_vars = schema_vars_resolver(schema_type)
    if schema_vars.name in schema_repository:
        return

    # Add placeholder to avoid recursive definition attempts while we're making this schema
    schema_repository[schema_vars.name] = {"$generating": True}

    properties = {"$ref": {"type": "string", "description": "Path to content that replaces the $ref"}}
    all_fields, optional_fields = _get_fields(schema_type)
    required_fields = []
    hints = get_type_hints(schema_type)
    field_docs = _field_docs_for(schema_type)
    for field in all_fields:
        if field in hints:
            value_type = hints[field]
        else:
            # See if this field has a default
            if hasattr(schema_type, field):
                value_type = type(getattr(schema_type, field))
            else:
                raise ValueError(f"Could not make JSON Schema for {_fullname(schema_type)} because field `{field}` does not have type hints nor default values")

        try:
            properties[field], is_optional = _schema_for(value_type, schema_vars_resolver, schema_repository, schema_type)
            if not is_optional and not hasattr(schema_type, field):
                required_fields.append(field)
        except NotImplementedError as e:
            # Simply omit fields with types that we can't describe with jsonschema
            print(f"Warning: Omitting {schema_type.__name__}.{field} from definition because: {e}")
            continue

        if field in field_docs:
            properties[field]["description"] = field_docs[field]

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": properties
    }
    if schema_vars.schema_id is not None:
        schema["$id"] = schema_vars.schema_id

    docs = inspect.getdoc(schema_type)
    if docs != _implicitdict_doc:
        if schema_vars.description is not None:
            schema["description"] = docs + "\n\n" + schema_vars.description
        else:
            schema["description"] = docs
    elif schema_vars.description is not None:
        schema["description"] = schema_vars.description

    if required_fields:
        required_fields.sort()
        schema["required"] = required_fields

    schema_repository[schema_vars.name] = schema


def _schema_for(value_type: Type, schema_vars_resolver: SchemaVarsResolver, schema_repository: Dict[str, dict], context: Type) -> Tuple[dict, bool]:
    """Get the JSON Schema representation of the value_type.

    Args:
        value_type: Data type for which to return a JSON Schema.
        schema_vars_resolver: Mapping from data type to information about the schema for that data type.
        schema_repository: If the schema for this data type needs to refer to schemas for other data types, those data
            types must already be present in this repository or else they will be added to it during this function.
        context: The parent/top-level JSON Schema in which the schema for value_type is being included (affects the $ref
            paths used to refer to external schemas).

    Returns:
        * JSON Schema representation of the value_type
        * Boolean indication of whether the value_type is optional as a field in an ImplicitDict.
          E.g., _schema_for(Optional[float], ...) would indicate True because an Optional[float] field within an
          ImplicitDict would be an optional field in that object.
    """
    generic_type = get_origin(value_type)
    if generic_type:
        # Type is generic
        arg_types = get_args(value_type)
        if generic_type is list:
            items_schema, _ = _schema_for(arg_types[0], schema_vars_resolver, schema_repository, context)
            return {"type": "array", "items": items_schema}, False

        elif generic_type is dict:
            schema = {
                "type": "object",
                "properties": {
                    "$ref": {"type": "string", "description": "Path to content that replaces the $ref"}
                }
            }
            if len(arg_types) >= 2:
                value_schema, _ = _schema_for(arg_types[1], schema_vars_resolver, schema_repository, context)
                schema["additionalProperties"] = value_schema
            return schema, False

        elif generic_type is Union and len(arg_types) == 2 and arg_types[1] is type(None):
            # Type is an Optional declaration
            subschema, _ = _schema_for(arg_types[0], schema_vars_resolver, schema_repository, context)
            schema = json.loads(json.dumps(subschema))
            if "type" in schema:
                if "null" not in schema["type"]:
                    schema["type"] = [schema["type"], "null"]
            else:
                schema = {"oneOf": [{"type": "null"}, schema]}
            return schema, True

        elif generic_type is Literal and len(arg_types) == 1:
            # Type is a Literal (parsed value must match specified value)
            return {"type": "string", "enum": [arg_types[0]]}, False

        else:
            raise NotImplementedError(f"Automatic JSON schema generation for {value_type} generic type is not yet implemented")

    schema_vars = schema_vars_resolver(value_type)

    if issubclass(value_type, ImplicitDict):
        make_json_schema(value_type, schema_vars_resolver, schema_repository)
        return {"$ref": schema_vars.path_to(value_type, context)}, False

    if value_type == bool or issubclass(value_type, bool):
        return {"type": "boolean"}, False

    if value_type == float or issubclass(value_type, float):
        return {"type": "number"}, False

    if value_type == int or issubclass(value_type, int):
        return {"type": "integer"}, False

    if value_type == str or issubclass(value_type, str):
        schema = {"type": "string"}
        if issubclass(value_type, StringBasedDateTime):
            schema["format"] = "date-time"
        elif issubclass(value_type, StringBasedTimeDelta):
            schema["format"] = "duration"
        if issubclass(value_type, enum.Enum):
            schema["enum"] = [v.value for v in value_type]
        return schema, False

    if value_type == datetime or issubclass(value_type, datetime):
        return {"type": "string", "format": "date-time"}, False

    if value_type == dict or issubclass(value_type, dict):
        return {"type": "object"}, False

    if hasattr(value_type, "__orig_bases__") and value_type.__orig_bases__:
        return _schema_for(value_type.__orig_bases__[0], schema_vars_resolver, schema_repository, context)

    raise NotImplementedError(f"Automatic JSON schema generation for {value_type} type is not yet implemented")


def _field_docs_for(t: Type[ImplicitDict]) -> Dict[str, str]:
    # Curse Guido for rejecting PEP224!  Fine, we'll do it ourselves.
    result = {}
    src = inspect.getsource(t)
    doc_pattern = r"\n\s+([_a-zA-Z][_a-zA-Z0-9]*)(?:: [^\n]+)?\n(\s+)(?:\"\"\"|''')((?:.|\s)*?)(?:\"\"\"|''')"
    for m in re.finditer(doc_pattern, src):
        indent = m.group(2)
        lines = m.group(3).split("\n")
        for i in range(1, len(lines)):
            if lines[i].startswith(indent):
                lines[i] = lines[i][len(indent):]
        while not lines[-1]:
            lines = lines[0:-1]
        docstring = "\n".join(lines)
        result[m.group(1)] = docstring
    return result
