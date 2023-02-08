from datetime import timedelta

import pytest

from implicitdict import StringBasedTimeDelta


def test_behavior_strings():
    s = '1s'
    sbtd = StringBasedTimeDelta(s)
    assert sbtd == s
    assert sbtd.timedelta.total_seconds() == 1

    sbtd = StringBasedTimeDelta(s, reformat=True)
    assert sbtd != s
    assert sbtd.timedelta.total_seconds() == 1

    s = '1.1s'
    sbtd = StringBasedTimeDelta(s)
    assert sbtd == s
    assert sbtd.timedelta.total_seconds() == 1.1

    sbtd = StringBasedTimeDelta(s, reformat=True)
    assert sbtd != s
    assert sbtd.timedelta.total_seconds() == 1.1

    s = '1m'
    sbtd = StringBasedTimeDelta(s)
    assert sbtd == s
    assert sbtd.timedelta.total_seconds() == 60

    sbtd = StringBasedTimeDelta(s, reformat=True)
    assert sbtd != s
    assert sbtd.timedelta.total_seconds() == 60

    s = '5 hours, 34 minutes, 56 seconds'
    sbtd = StringBasedTimeDelta(s)
    assert sbtd == s
    assert sbtd.timedelta.total_seconds() == 5 * 60 * 60 + 34 * 60 + 56

    sbtd = StringBasedTimeDelta(s, reformat=True)
    assert sbtd != s
    assert sbtd.timedelta.total_seconds() == 5 * 60 * 60 + 34 * 60 + 56

    s = '0.1234567s'
    sbtd = StringBasedTimeDelta(s)
    assert sbtd == s
    assert '1234567' not in str(sbtd.timedelta.total_seconds())  # timedelta only stores integer microseconds

    sbtd = StringBasedTimeDelta(s, reformat=True)
    assert sbtd != s


def test_behavior_seconds():
    for s in (1, 1.1, 0.5, 0.123456):
        sbtd = StringBasedTimeDelta(s)
        assert sbtd.endswith('s')
        assert sbtd.timedelta.total_seconds() == s

    sbtd = StringBasedTimeDelta(0.1234567)
    assert '1234567' not in str(sbtd.timedelta.total_seconds())  # timedelta only stores integer microseconds


def test_behavior_timedelta():
    deltas = (
        timedelta(seconds=1),
        timedelta(seconds=1.1),
        timedelta(seconds=0.9),
        timedelta(minutes=5),
        timedelta(hours=5, minutes=34, seconds=56),
        timedelta(hours=5, minutes=34, seconds=56, milliseconds=1234),
    )
    for dt in deltas:
        sbtd = StringBasedTimeDelta(dt)
        assert sbtd.timedelta == dt
        s = str(sbtd)
        with pytest.raises(AttributeError):  # 'str' object has no attribute 'timedelta'
            assert s.timedelta == dt
        sbtd2 = StringBasedTimeDelta(s)
        assert sbtd2.timedelta == dt
