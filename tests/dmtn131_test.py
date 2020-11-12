"""Test rubinlander.parsers.lsstdoc with test data based on DMTN-131.
"""

from __future__ import annotations

import datetime
from pathlib import Path

from dateutil import tz

from rubinlander.parsers.lsstdoc import LsstDocParser


def test_dmtn131() -> None:
    root_tex_path = (
        Path(__file__).parent / "data" / "dmtn-131" / "DMTN-131.tex"
    )
    parser = LsstDocParser(root_tex_path)

    assert parser.metadata.title == "When clouds might be good for LSST"
    assert parser.metadata.authors[0].name == "William O’Mullane"
    assert parser.metadata.date_modified == datetime.datetime(
        2019, 10, 9, 19, 0, tzinfo=tz.UTC
    )
    assert parser.metadata.identifier == "DMTN-131"
    assert parser.metadata.abstract.plain == (
        "In this short note we would like to consider potential annual "
        "operating costs for LSST as well as discuss long term archiving. "
        "The goal would be to see if we can come to an agreement with a "
        "major cloud provider."
    )
    assert parser.metadata.abstract.html == (
        "<p>In this short note we would like to consider potential annual "
        "operating costs for LSST as well as discuss long term archiving. "
        "The goal would be to see if we can come to an agreement with a "
        "major cloud provider.</p>"
    )
