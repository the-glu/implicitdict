from __future__ import annotations
import json
from typing import Optional, List

from implicitdict import ImplicitDict

import pytest


# This object must be defined with future annotations as Python 3.8 will not resolve string-based forward references correctly
class MassiveNestingData(ImplicitDict):
    children: Optional[List[MassiveNestingData]]
    foo: str
    bar: int = 0

    @staticmethod
    def example_value():
        return ImplicitDict.parse(
            {
                "foo": "1a",
                "children": [
                    {
                        "foo": "1a 2a"
                    },
                    {
                        "foo": "1a 2b",
                        "children": [
                            {
                                "foo": "1a 2b 3",
                                "children": [
                                    {
                                        "foo": "1a 2b 3 4a",
                                        "bar": 123
                                    },
                                    {
                                        "foo": "1a 2b 3 4b",
                                        "bar": 456
                                    },
                                    {
                                        "foo": "1a 2b 3 4c",
                                        "bar": 789,
                                        "children": []
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            MassiveNestingData
        )


def _get_correct_value() -> MassiveNestingData:
    return json.loads(json.dumps(MassiveNestingData.example_value()))


def test_stacktrace():
    obj_dict = _get_correct_value()
    obj_dict["bar"] = "wrong kind of value"
    with pytest.raises(ValueError, match=r"^At bar:"):
        ImplicitDict.parse(obj_dict, MassiveNestingData)

    obj_dict = _get_correct_value()
    obj_dict["bar"] = []
    with pytest.raises(TypeError, match=r"^At bar:"):
        ImplicitDict.parse(obj_dict, MassiveNestingData)

    obj_dict = _get_correct_value()
    obj_dict["bar"] = {}
    with pytest.raises(TypeError, match=r"^At bar:"):
        ImplicitDict.parse(obj_dict, MassiveNestingData)

    obj_dict = _get_correct_value()
    obj_dict["children"] = "this gets treated as a list"
    with pytest.raises(ValueError, match=r"^At children\[0]:"):
        ImplicitDict.parse(obj_dict, MassiveNestingData)

    obj_dict = _get_correct_value()
    obj_dict["children"] = 0
    with pytest.raises(ValueError, match=r"^At children:"):
        ImplicitDict.parse(obj_dict, MassiveNestingData)

    obj_dict = _get_correct_value()
    obj_dict["children"][0]["bar"] = "wrong kind of value"
    with pytest.raises(ValueError, match=r"^At children\[0].bar:"):
        ImplicitDict.parse(obj_dict, MassiveNestingData)

    obj_dict = _get_correct_value()
    obj_dict["children"][1]["children"] = False
    with pytest.raises(ValueError, match=r"^At children\[1].children:"):
        ImplicitDict.parse(obj_dict, MassiveNestingData)

    obj_dict = _get_correct_value()
    obj_dict["children"][1]["children"][0]["children"][2]["children"] = 2
    with pytest.raises(ValueError, match=r"^At children\[1].children\[0].children\[2].children:"):
        ImplicitDict.parse(obj_dict, MassiveNestingData)
