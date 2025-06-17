"""Basic tests to verify the package is installed correctly."""


def test_version() -> None:
    """Test that the version is defined."""
    from isynspec import __version__

    assert __version__ == "0.1.0"
