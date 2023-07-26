from .test_types import ContainerData


def test_container_item_value_casting():
    containers: ContainerData = ContainerData.example_value()

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
