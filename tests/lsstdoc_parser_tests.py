"""Test cases for lsstdoc document parsing."""

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
