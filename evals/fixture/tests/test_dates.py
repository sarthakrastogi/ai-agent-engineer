from tools.dates import parse_date


def test_parse_date():
    assert parse_date.invoke("2026-10-09T10:00:00+13:00") == "2026-10-09"
