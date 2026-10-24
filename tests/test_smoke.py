import dhadkan


def test_package_imports_and_has_version() -> None:
    assert dhadkan.__version__ == "0.0.1"
