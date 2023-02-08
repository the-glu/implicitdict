from datetime import datetime, timedelta

import arrow
import pytest

from implicitdict import StringBasedDateTime


ZERO_SKEW = timedelta(microseconds=0)


def test_consistency():
    t = datetime.utcnow()
    sbdt = StringBasedDateTime(t)
    with pytest.raises(TypeError):  # can't subtract offset-naive and offset-aware datetimes
        assert abs(sbdt.datetime - t) <= ZERO_SKEW
    with pytest.raises(TypeError):  # can't compare offset-naive and offset-aware datetimes
        assert not (sbdt.datetime > t)
    assert abs(sbdt.datetime - arrow.get(t).datetime) <= ZERO_SKEW

    sbdt = StringBasedDateTime(t.isoformat())
    assert abs(sbdt.datetime - arrow.get(t).datetime) <= ZERO_SKEW

    t = arrow.utcnow().datetime
    sbdt = StringBasedDateTime(t)
    assert abs(sbdt.datetime - t) <= ZERO_SKEW

    sbdt = StringBasedDateTime(t.isoformat())
    assert abs(sbdt.datetime - t) <= ZERO_SKEW

    t = arrow.now('US/Pacific').datetime
    sbdt = StringBasedDateTime(t)
    assert abs(sbdt.datetime - t) <= ZERO_SKEW

    sbdt = StringBasedDateTime(t.isoformat())
    assert abs(sbdt.datetime - t) <= ZERO_SKEW

    t = arrow.now('US/Pacific')
    sbdt = StringBasedDateTime(t)
    assert abs(sbdt.datetime - t) <= ZERO_SKEW

    sbdt = StringBasedDateTime(t.isoformat())
    assert abs(sbdt.datetime - t) <= ZERO_SKEW

    t = arrow.get("1234-01-23T12:34:56.12345678")
    sbdt = StringBasedDateTime(t)
    assert "12345678" not in sbdt  # arrow only stores (after rounding) integer microseconds

    with pytest.raises(ValueError):  # unconverted data remains (datetime only parses down to microseconds)
        datetime.strptime("1234-01-23T12:34:56.12345678", "%Y-%m-%dT%H:%M:%S.%f")


def test_non_mutation():
    """When a string is provided, expect the string representation to remain the same unless reformatting."""

    s = "2022-02-01T01:01:00.123456789123456789123456789"
    assert StringBasedDateTime(s) == s
    sbdt = StringBasedDateTime(s, reformat=True)
    assert sbdt != s
    assert sbdt.endswith('Z')

    s = "1800-12-01T18:15:00"
    assert StringBasedDateTime(s) == s
    sbdt = StringBasedDateTime(s, reformat=True)
    assert sbdt != s
    assert sbdt.endswith('Z')

    s = "2022-06-23T00:00:00+00:00"
    assert StringBasedDateTime(s) == s
    sbdt = StringBasedDateTime(s, reformat=True)
    assert sbdt != s
    assert sbdt.endswith('Z')


def test_zulu_default():
    """When a non-string datetime is provided, expect the string representation to use Z as the UTC timezone."""

    assert StringBasedDateTime(datetime.utcnow()).endswith('Z')
    assert StringBasedDateTime(arrow.utcnow().datetime).endswith('Z')
    assert StringBasedDateTime(arrow.utcnow()).endswith('Z')
