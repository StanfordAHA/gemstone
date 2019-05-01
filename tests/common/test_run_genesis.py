from gemstone.common.run_genesis import run_genesis


TOP = "test_run_genesis"
INFILES = ["tests/common/test_run_genesis.vp"]
PARAMS = {
    "width": 16,
}


def get_lines(filename):
    with open(filename) as f:
        return f.readlines()


def test_run_genesis_basic():
    """
    Check operation of run_genesis() helper function against a gold output, and
    that it raises an exception on failure.
    """
    GOLDEN = "tests/common/gold/test_run_genesis.v"
    verilog_files = run_genesis(TOP, INFILES, PARAMS)
    assert len(verilog_files) == 1
    verilog_file = verilog_files[0]
    golden_lines = get_lines(GOLDEN)
    genesis_lines = get_lines(verilog_file)
    assert golden_lines[40:] == genesis_lines[40:]


def test_run_genesis_bad_params():
    # Run the same command with bogus parameters injected to check that Genesis
    # fails.
    bad_params = PARAMS.copy()
    bad_params.update({"some_non_existent_param": 0})
    try:
        run_genesis(TOP, INFILES, bad_params)
        assert False
    except RuntimeError as e:
        msg = e.__str__()
    assert msg[:15] == "Genesis failed!"
