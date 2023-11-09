import inspect
from dataclasses import dataclass
import re

import arrow
import datetime
from datetime import datetime as datetime_type
from typing import get_args, get_origin, get_type_hints, Dict, Literal, \
    Optional, Type, Union, Set, Tuple

import pytimeparse


_DICT_FIELDS = set(dir({}))
_KEY_FIELDS_INFO = '_fields_info'
_PARSING_ERRORS = (ValueError, TypeError)


def _bubble_up_parse_error(child: Union[ValueError, TypeError], field: str) -> Union[ValueError, TypeError]:
    location_regex = r'^At ([A-Za-z0-9_.[\]]*):((?:.|[\n\r])*)$'
    m = re.search(location_regex, str(child))
    if m:
        suffix = m.group(1)
        if suffix.startswith("["):
            location = field + suffix
        else:
            location = f"{field}.{suffix}"
        return type(child)(f"At {location}:{m.group(2)}")
    else:
        return type(child)(f"At {field}: {str(child)}")


class ImplicitDict(dict):
    """Base class that turns a subclass into a dict indexing attributes.

    The expected usage of this class is to declare a subclass with typed
    attributes:

      class MySubclass1(ImplicitDict):
        a: float
        b: int = 2
        c: Optional[str]
        d = 4

    All non-optional attributes must be specified when constructing an instance of
    the subclass.  Untyped attributes with a default value are considered
    optional.  In the above example, an instance of MySubclass can only be
    constructed when the values for `a` and `b` are specified in the constructor:

      MySubclass1()
        >> ValueError

      MySubclass1(a=1)
        >> ValueError

      MySubclass1(a=1, b=2)

    But, more values can be specified:

      MySubclass1(a=1, b=2, c='3', d='foo')

    The subclass allows access to all the declared attributes, but stores and
    retrieves the attributes' values in and from the underlying dict.  This means
    that the subclass will always present itself as a dict with appropriate
    entries for all declared attributes that are present.  As a result, subclasses
    are JSON-serializable by the default encoder.  Example:

      x = MySubclass1(a=1, b=2)
      x.d = 'foo'
      import json
      json.dumps(x)
        >> '{"b": 2, "d": "foo", "a": 1}'

    To deserialize JSON into an ImplicitDict subclass, use ImplicitDict.parse:

      y: MySubclass1 = ImplicitDict.parse({'b': 2, 'd': 'foo', 'a': 1}, MySubclass1)
      print(y.d)
        >> foo

    If __init__ is overridden, ImplicitDict.__init__ should be called with
    **kwargs.  For example:

      class MySubclass2(ImplicitDict):
        a: float
        b: int = 2
        c: Optional[str]
        d = 4

        def __init__(self, **kwargs):
          self.e = 5
          super(ImplicitDict, self).__init__(**kwargs)
    """

    @classmethod
    def parse(cls, source: Dict, parse_type: Type):
        if not isinstance(source, dict):
            raise ValueError(f'Expected to find dictionary data to populate {parse_type.__name__} object but instead found {type(source).__name__} type')
        kwargs = {}
        hints = get_type_hints(parse_type)
        for key, value in source.items():
            if key in hints:
                # This entry has an explicit type
                try:
                    kwargs[key] = _parse_value(value, hints[key])
                except _PARSING_ERRORS as e:
                    raise _bubble_up_parse_error(e, key)
            else:
                # This entry's type isn't specified
                kwargs[key] = value
        return parse_type(**kwargs)

    def __init__(self, previous_instance: Optional[dict]=None, **kwargs):
        ancestor_kwargs = {}
        subtype = type(self)

        all_fields, optional_fields = _get_fields(subtype)

        # Copy explicit field values passed to the constructor
        provided_values = set()
        if previous_instance:
            for key, value in previous_instance.items():
                if key in all_fields:
                    ancestor_kwargs[key] = value
                    provided_values.add(key)
        for key, value in kwargs.items():
            if key in all_fields:
                if value is None and key in optional_fields and key not in provided_values:
                    # Don't consider an explicit null provided for an optional field as
                    # actually providing a value; instead, consider it omitting a value.
                    pass
                else:
                    ancestor_kwargs[key] = value
                    provided_values.add(key)

        # Copy default field values
        for key in all_fields:
            if key not in provided_values:
                if hasattr(subtype, key):
                    ancestor_kwargs[key] = super(ImplicitDict, self).__getattribute__(key)

        # Make sure all fields without a default and not labeled Optional were provided
        for key in all_fields:
            if key not in ancestor_kwargs and key not in optional_fields:
                raise ValueError('Required field "{}" not specified in {}'.format(key, subtype.__name__))

        super(ImplicitDict, self).__init__(**ancestor_kwargs)

    def __getattribute__(self, item):
        self_type = type(self)
        if hasattr(self_type, _KEY_FIELDS_INFO):
            fields_info_by_type: Dict[str, FieldsInfo] = getattr(self_type, _KEY_FIELDS_INFO)
            self_type_name = _fullname(self_type)
            if self_type_name in fields_info_by_type:
                if item in fields_info_by_type[self_type_name].all_fields:
                    return self[item]
        return super(ImplicitDict, self).__getattribute__(item)

    def __setattr__(self, key, value):
        self_type = type(self)
        if hasattr(self_type, _KEY_FIELDS_INFO):
            fields_info_by_type: Dict[str, FieldsInfo] = getattr(self_type, _KEY_FIELDS_INFO)
            self_type_name = _fullname(self_type)
            if self_type_name in fields_info_by_type:
                if key in fields_info_by_type[self_type_name].all_fields:
                    self[key] = value
                    return
                else:
                    raise KeyError('Attribute "{}" is not defined for "{}" object'.format(key, type(self).__name__))
        super(ImplicitDict, self).__setattr__(key, value)

    def has_field_with_value(self, field_name: str) -> bool:
        return field_name in self and self[field_name] is not None


def _parse_value(value, value_type: Type):
    generic_type = get_origin(value_type)
    if generic_type:
        # Type is generic
        arg_types = get_args(value_type)
        if generic_type is list:
            try:
                value_list = [v for v in value]
            except TypeError as e:
                if "not iterable" in str(e):
                    raise ValueError(f"Cannot parse non-iterable value '{value}' of type '{type(value).__name__}' into list type '{value_type}'")
                raise
            result = []
            for i, v in enumerate(value_list):
                try:
                    result.append(_parse_value(v, arg_types[0]))
                except _PARSING_ERRORS as e:
                    raise _bubble_up_parse_error(e, f"[{i}]")
            return result

        elif generic_type is dict:
            # value is a dict of some kind
            result = {}
            for k, v in value.items():
                parsed_key = k if arg_types[0] is str else _parse_value(k, arg_types[0])
                try:
                    parsed_value = _parse_value(v, arg_types[1])
                except _PARSING_ERRORS as e:
                    raise _bubble_up_parse_error(e, k)
                result[parsed_key] = parsed_value
            return result

        elif generic_type is Union and len(arg_types) == 2 and arg_types[1] is type(None):
            # Type is an Optional declaration
            if value is None:
                # An optional field specified explicitly as None is equivalent to
                # omitting the field's value
                return None
            else:
                return _parse_value(value, arg_types[0])

        elif generic_type is Literal and len(arg_types) == 1:
            # Type is a Literal (parsed value must match specified value)
            if value != arg_types[0]:
                raise ValueError('Value {} does not match required Literal {}'.format(value, arg_types[0]))
            return value

        else:
            raise ValueError(f'Automatic parsing of {value_type} type is not yet implemented')

    elif issubclass(value_type, ImplicitDict):
        # value is an ImplicitDict
        return ImplicitDict.parse(value, value_type)

    if hasattr(value_type, "__orig_bases__") and value_type.__orig_bases__:
        return value_type(_parse_value(value, value_type.__orig_bases__[0]))

    else:
        # value is a non-generic type that is not an ImplicitDict
        return value_type(value) if value_type else value


@dataclass
class FieldsInfo(object):
    all_fields: Set[str]
    optional_fields: Set[str]



def _get_fields(subtype: Type) -> Tuple[Set[str], Set[str]]:
    """Determine all fields and optional fields for the specified type.

    When all & optional fields are determined for a type, the result is cached
    as an entry in the _KEY_FIELDS_INFO attribute added to the type itself so
    this evaluation only needs to be performed once per type.

    Returns:
        * Names of all fields for subtype
        * Names of all optional fields for subtype
    """
    if not hasattr(subtype, _KEY_FIELDS_INFO):
        setattr(subtype, _KEY_FIELDS_INFO, {})
    fields_info_by_type: Dict[str, FieldsInfo] = getattr(subtype, _KEY_FIELDS_INFO)
    subtype_name = _fullname(subtype)
    if subtype_name not in fields_info_by_type:
        # Enumerate fields defined for superclasses
        all_fields = set()
        optional_fields = set()
        ancestors = inspect.getmro(subtype)
        for ancestor in ancestors:
            if issubclass(ancestor, ImplicitDict) and ancestor is not subtype and ancestor is not ImplicitDict:
                ancestor_all_fields, ancestor_optional_fields = _get_fields(ancestor)
                all_fields = all_fields.union(ancestor_all_fields)
                optional_fields = optional_fields.union(ancestor_optional_fields)

        # Enumerate all fields defined for the subclass
        annotations = get_type_hints(subtype)
        for key in annotations:
            all_fields.add(key)

        attributes = set()
        for key in dir(subtype):
            if (
                    key != _KEY_FIELDS_INFO
                    and key not in _DICT_FIELDS
                    and key[0:2] != '__'
                    and not callable(getattr(subtype, key))
                    and not isinstance(getattr(subtype, key), property)
            ):
                all_fields.add(key)
                attributes.add(key)

        # Identify which fields are Optional
        for key, field_type in annotations.items():
            generic_type = get_origin(field_type)
            if generic_type is Optional:
                optional_fields.add(key)
            elif generic_type is Union:
                generic_args = get_args(field_type)
                if len(generic_args) == 2 and generic_args[1] is type(None):
                    optional_fields.add(key)
        for key in attributes:
            if key not in annotations:
                optional_fields.add(key)

        fields_info_by_type[subtype_name] = FieldsInfo(
            all_fields=all_fields,
            optional_fields=optional_fields
        )
    result = fields_info_by_type[subtype_name]
    return result.all_fields, result.optional_fields


def _fullname(class_type: Type) -> str:
    module = class_type.__module__
    if module == "builtins":
        return class_type.__qualname__  # avoid outputs like 'builtins.str'
    return module + "." + class_type.__qualname__


class StringBasedTimeDelta(str):
    """String that only allows values which describe a timedelta."""

    timedelta: datetime.timedelta
    """Timedelta matching the string value of this instance."""

    def __new__(cls, value: Union[str, datetime.timedelta, int, float], reformat: bool = False):
        """Create a new StringBasedTimeDelta.

        Args:
            value: Timedelta representation.  May be a pytimeparse-compatible string, Python timedelta, or number of
              seconds (float).
            reformat: If true, override a provided string with a string representation of the parsed timedelta.
        """
        if isinstance(value, str):
            dt = datetime.timedelta(seconds=pytimeparse.parse(value))
            s = str(dt) if reformat else value
        elif isinstance(value, float) or isinstance(value, int):
            dt = datetime.timedelta(seconds=value)
            s = f'{value}s'
        elif isinstance(value, datetime.timedelta):
            dt = value
            s = str(dt)
        else:
            raise ValueError(f'Could not parse type {type(value).__name__} into StringBasedTimeDelta')
        str_value = str.__new__(cls, s)
        str_value.timedelta = dt
        return str_value


class StringBasedDateTime(str):
    """String that only allows values which describe an absolute datetime."""

    datetime: datetime.datetime
    """Timezone-aware datetime matching the string value of this instance."""

    def __new__(cls, value: Union[str, datetime_type, arrow.Arrow], reformat: bool = False):
        """Create a new StringBasedDateTime instance.

        Args:
            value: Datetime representation.  May be an ISO/RFC3339-compatible string, datetime, or arrow.  If timezone
              is not specified, UTC will be assumed.
            reformat: If true, override a provided string with a string representation of the parsed datetime.
        """
        t_arrow = arrow.get(value)
        if isinstance(value, str):
            s = t_arrow.isoformat() if reformat else value
            zuluize = reformat
        else:
            s = t_arrow.isoformat()
            zuluize = True
        if zuluize and s.endswith('+00:00'):
            s = s[0:-len('+00:00')] + 'Z'
        str_value = str.__new__(cls, s)
        str_value.datetime = t_arrow.datetime
        return str_value
