from rubinlander import __version__


def test_version() -> None:
    assert isinstance(__version__, str)
