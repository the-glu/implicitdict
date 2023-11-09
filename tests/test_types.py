import enum
from datetime import datetime
from typing import Optional, List

from implicitdict import ImplicitDict, StringBasedDateTime, StringBasedTimeDelta


class MySpecialClass(str):
    @property
    def is_special(self) -> bool:
        return True


class ContainerData(ImplicitDict):
    single_value: MySpecialClass
    value_list: List[MySpecialClass]
    optional_list: Optional[List[MySpecialClass]]
    optional_value_list: List[Optional[MySpecialClass]]
    list_of_lists: List[List[MySpecialClass]]

    @staticmethod
    def example_value():
        return ImplicitDict.parse(
            {
                "single_value": "foo",
                "value_list": ["value1", "value2"],
                "optional_list": ["bar"],
                "optional_value_list": ["baz", None],
                "list_of_lists": [["list1v1", "list1v2"], ["list2v1"]]
            }, ContainerData)


class InheritanceData(ImplicitDict):
    foo: str
    bar: int = 0
    baz: Optional[float]
    has_default_baseclass: str = "In MyData"

    def hello(self) -> str:
        return "MyData"

    def base_method(self) -> int:
        return 123

    @staticmethod
    def example_value():
        return ImplicitDict.parse({'foo': 'asdf', 'bar': 1}, InheritanceData)


class MySubclass(InheritanceData):
    buzz: Optional[str]
    has_default_subclass: str = "In MySubclass"

    def hello(self) -> str:
        return "MySubclass"


class SpecialListClass(List[MySpecialClass]):
    def hello(self) -> str:
        return "SpecialListClass"


class SpecialComplexListClass(List[MySubclass]):
    def hello(self) -> str:
        return "SpecialComplexListClass"


class SpecialSubclassesContainer(ImplicitDict):
    special_list: SpecialListClass
    special_complex_list: SpecialComplexListClass

    @staticmethod
    def example_value():
        return ImplicitDict.parse({'special_list': ['foo'], 'special_complex_list': [{'foo': 'oof'}]}, SpecialSubclassesContainer)


class MutabilityData(ImplicitDict):
    primitive: str
    list_of_primitives: List[str]
    generic_dict: dict
    subtype: Optional["MutabilityData"]


class NormalUsageData(ImplicitDict):
    foo: str
    """The foo characterizing the data."""

    bar: int = 0
    """The bar of the data.
    
    Indents should not be included in docstrings."""

    baz: Optional[float]
    """If this baz is specified, it provides additional information.
    
    Final docstring newlines should be omitted.
    """


class OptionalData(ImplicitDict):
    required_field: str
    optional_field1: Optional[str]
    field_with_default: str = "default value"
    optional_field2_with_none_default: Optional[str] = None
    optional_field3_with_default: Optional[str] = "concrete default"

    @staticmethod
    def example_values():
        return {
            "fully_defined": OptionalData(
                required_field="foo1",
                optional_field1="foo2",
                field_with_default="foo3",
                optional_field2_with_none_default="foo4",
                optional_field3_with_default="foo5",
            ),
            "over_defined": OptionalData(
                required_field="foo1",
                optional_field1="foo2",
                field_with_default="foo3",
                optional_field2_with_none_default="foo4",
                optional_field3_with_default="foo5",
                unknown_field="foo6",
            ),
            "minimally_defined": OptionalData(required_field="foo1"),
            "provide_optional_field": OptionalData(required_field="foo1", optional_field1="foo2"),
            "provide_optional_field_as_none": OptionalData(required_field="foo1", optional_field1=None),
            "provide_optional_field_with_none_default_as_none": OptionalData(required_field="foo1", optional_field2_with_none_default=None),
            "provide_optional_field_with_default_as_none": OptionalData(required_field="foo1", optional_field3_with_default=None)
        }


class PropertiesData(ImplicitDict):
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

    @staticmethod
    def example_value():
        return PropertiesData(foo='foo')


class YesNo(str, enum.Enum):
    YesOption = "Yes"
    NoOption = "No"


class SpecialTypesData(ImplicitDict):
    datetime: StringBasedDateTime
    timedelta: StringBasedTimeDelta
    yesno: YesNo
    boolean: bool

    @staticmethod
    def example_value():
        return ImplicitDict.parse({"datetime": datetime.utcnow().isoformat(), "timedelta": "12h", "yesno": "Yes", "boolean": "true"}, SpecialTypesData)


class NestedDefinitionsData(ImplicitDict):
    special_types: SpecialTypesData

    @staticmethod
    def example_value():
        return ImplicitDict.parse({"special_types": {"datetime": datetime.utcnow().isoformat(), "timedelta": "12h", "yesno": "Yes", "boolean": "true"}}, NestedDefinitionsData)
