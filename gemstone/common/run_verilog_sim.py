import os
import shutil
import tempfile
from .util import deprecated


class IrunCommand:
    def __init__(self, outfile=None, run_ns=1000000):
        self.outfile = "verilog.vcd" if outfile is None else outfile
        self.run_ns = run_ns

    def source(self):
        return f"""
database -open -vcd vcddb -into {self.outfile}.vcd -default -timescale ps
probe -create -all -vcd -depth all
run {int(self.run_ns)}ns
quit"""


def irun_available():
    return shutil.which("irun") is not None


@deprecated("iverilog does not support system verilog")
def iverilog_available():
    return shutil.which("iverilog") is not None


def verilog_sim_available():
    # Note(rsetaluri): we do not consider iverilog for now, since it does not
    # support system verilog.
    return irun_available()


# We don't cover this function because irun is not available on travis
def irun(files,
         irun_cmd=None,
         top_name="top",
         cleanup=False):  # pragma: nocover
    if len(files) == 0:
        print("Warning: irun requires at least 1 input file. Skipping irun.")
        return True
    if irun_cmd is None:
        irun_cmd = IrunCommand()
    files_string = " ".join(files)
    with tempfile.NamedTemporaryFile(delete=cleanup) as cmd_file:
        with open(cmd_file, "w") as cmd_file_w:
            cmd_file_w.write(irun_cmd.source())
        irun_cmd = f"irun -sv -top {top_name} -timescale 1ns/1ps -l irun.log " \
                   f"-access +rwc -notimingchecks -input {cmd_file} " \
                   f"{files_string}"
        print(f"Running irun cmd: {irun_cmd}")
        if not os.system(irun_cmd) == 0:
            return False
        if not cleanup:
            return True
        cleanup_cmd = "rm -rf verilog.vcd INCA_libs irun.*"
        return os.system(cleanup_cmd) == 0


@deprecated("iverilog does not support system verilog")
def iverilog(files,
             top_name="top",
             cleanup=False):
    if len(files) == 0:
        print("Warning: iverilog requires at least 1 input file. "
              "Skipping iverilog.")
        return True
    with tempfile.NamedTemporaryFile(delete=cleanup) as temp_file:
        iverilog_cmd = f"iverilog -s {top_name} -o {temp_file.name} "\
                       f"{' '.join(files)}"
        print(f"Running iverilog cmd: {iverilog_cmd}")
        if not os.system(iverilog_cmd) == 0:
            return False
        return os.system(f"{temp_file.name}") == 0


def run_verilog_sim(files, **kwargs):
    # Note(rsetaluri): we do not consider iverilog for now, since it does not
    # support system verilog.
    options = (
        (irun, irun_available),
    )
    for run_func, available_func in options:
        if available_func():
            return run_func(files, **kwargs)  # pragma: nocover
    raise Exception("Verilog simulator not available")  # pragma: nocover
