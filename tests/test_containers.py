from typing import List, Optional

from implicitdict import ImplicitDict


class MySpecialClass(str):
    @property
    def is_special(self) -> bool:
        return True


class MyContainers(ImplicitDict):
    single_value: MySpecialClass
    value_list: List[MySpecialClass]
    optional_list: Optional[List[MySpecialClass]]
    optional_value_list: List[Optional[MySpecialClass]]
    list_of_lists: List[List[MySpecialClass]]


def test_container_item_value_casting():
    containers: MyContainers = ImplicitDict.parse(
        {
            "single_value": "foo",
            "value_list": ["value1", "value2"],
            "optional_list": ["bar"],
            "optional_value_list": ["baz", None],
            "list_of_lists": [["list1v1", "list1v2"], ["list2v1"]]
        }, MyContainers)

    assert containers.single_value.is_special

    assert len(containers.value_list) == 2
    for v in containers.value_list:
        assert v.is_special

    assert len(containers.optional_list) == 1
    assert containers.optional_list[0].is_special

    assert len(containers.optional_value_list) == 2
    for v in containers.optional_value_list:
        assert (v is None) or v.is_special

    assert len(containers.list_of_lists) == 2
    assert len(containers.list_of_lists[0]) == 2
    for v in containers.list_of_lists[0]:
        assert v.is_special
    assert len(containers.list_of_lists[1]) == 1
    for v in containers.list_of_lists[1]:
        assert v.is_special
