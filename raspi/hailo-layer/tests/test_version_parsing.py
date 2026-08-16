"""Version parsing used by the hailo-apps compatibility check."""

from hailo_layer.pipeline.hailo_compat import _parse_version


def test_parse_version_pads_missing_zeros():
    assert _parse_version("26.3.0") == (26, 3, 0)
    assert _parse_version("26.03.0") == (26, 3, 0)
    assert _parse_version("26.3.1") == (26, 3, 1)


def test_parse_version_ordering():
    assert _parse_version("26.3.0") < _parse_version("26.4.0")
    assert _parse_version("26.03.1") < _parse_version("26.4.0")
    assert _parse_version("26.3.0") >= _parse_version("26.3.0")


def test_parse_version_tolerates_suffixes():
    assert _parse_version("26.3.0.dev1")[:2] == (26, 3)
    assert _parse_version("26.3.0+local") == (26, 3, 0)
