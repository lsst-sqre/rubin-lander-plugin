"""Test rubinlander.parsers.lsstdoc with test data based on DMTN-131.
"""

from __future__ import annotations

from pathlib import Path

from rubinlander.parsers.lsstdoc import LsstDocParser


def test_dmtn131() -> None:
    root_tex_path = (
        Path(__file__).parent / "data" / "dmtn-131" / "DMTN-131.tex"
    )
    parser = LsstDocParser(root_tex_path)

    assert parser.metadata.title == "When clouds might be good for LSST"
