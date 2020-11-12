"""Test cases for lsstdoc document parsing."""

import datetime

from dateutil import tz

from rubinlander.parsers.lsstdoc import LsstDocParser


def test_parse_authors() -> None:
    source = (
        "\\title{Test}\n"
        "\\author{\n"
        "A.~Author,\n"
        "B.~Author,\n"
        "and\n"
        "C.~Author}\n"
    )
    parsed_authors = LsstDocParser._parse_author(source)
    assert parsed_authors[0].name == "A. Author"
    assert parsed_authors[1].name == "B. Author"
    assert parsed_authors[2].name == "C. Author"


def test_parse_authors_latex_conversion() -> None:
    source = "\\title{Test}\n" "\\author{St\\'{e}phane}\n"
    parsed_authors = LsstDocParser._parse_author(source)
    assert parsed_authors[0].name == "Stéphane"


def test_parse_date() -> None:
    source = "\\date{2020-01-01}"
    parsed_date = LsstDocParser._parse_date(source)
    # 12:00 Pacific is 20:00 UTC
    assert parsed_date == datetime.datetime(2020, 1, 1, 20, tzinfo=tz.UTC)
