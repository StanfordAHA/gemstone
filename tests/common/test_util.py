import tempfile
import pathlib
from gemstone.common.util import ip_available, deprecated, compress_config_data


def test_ip_available():
    with tempfile.NamedTemporaryFile() as f:
        path = pathlib.Path(f.name)
        parent = path.parent
        assert parent.is_dir()
        assert ip_available(path.name, [str(parent)])

    assert not ip_available("random_file", ["/some/bad/path/"])


def test_deprecated():
    @deprecated("foo is deprecated")
    def foo():
        print("foo")

    try:
        foo()
        assert False
    except RuntimeError as e:
        expected_msg = "Function foo is deprecated: foo is deprecated"
        assert e.__str__() == expected_msg


def test_comparess_config_data():
    # test out compressing bitstream
    config_data = [(0, 1), (0, 2)]
    config_data = compress_config_data(config_data)
    assert len(config_data) == 1
    assert config_data[0][0] == 0
    assert config_data[0][1] == 1 | 2

    # test out duplicate without zeroing out, which is required to get rom
    # working under current lake design
    config_data = [(0, 0), (0, 1), (0, 2),
                   (1, 0), (1, 0), (1, 0)]
    config_data = compress_config_data(config_data, skip_compression=[1])
    assert len(config_data) == 1 + 3
    assert config_data[0][0] == 0
    assert config_data[0][1] == 1 | 2
    for i in range(1, 4):
        config_data[i][0] == 1
        config_data[i][1] == 0
