# CLAUDE.md — gemstone (session notes)

Generator framework under garnet/canal: `Generator`, configurable registers, and the AOI muxes
(`gemstone/common/mux_wrapper_aoi.py`) every switch box / connection box uses.

## Branch

aha `mek` points gemstone at the personal branch `thesis` (since 2026-10-23, aha mek af3f8db);
master is upstream's. garnet's rtl container step fetches `thesis` for thesis-fabric builds
(garnet `mflowgen/common/rtl/gen_rtl.sh`, like canal).

## AOI mux inner module names (thesis c3f0acc, 2026-10-23)

Each `_generate_mux_wrapper(height, width, type)` emits its own Verilog: the wrapper
(`mux_aoi[_ready_valid][_const]_<h>_<w>`) plus two inner modules, `precoder_<w>_<h>` and
`mux_logic_<w>_<h>`, whose contents depend on the type (valid ports, the constant input). Two
types of one width and height in one design used to define two different modules under one
name; tools keep one (Genus kept the plain one: "Unable to find port 'valid_in' of instance
'u_mux_logic' of module 'mux_logic_32_5'" on the 32-bit thesis RV fabric, where the 32-bit RV data
muxes meet the 32-bit config muxes). Simulators that keep the first definition ran it.
- Now `_INNER_NAME_OWNER`: the first type to use a (width, height) keeps the plain names, any
  other gets `_<type>` names (`mux_logic_32_5_regularreadyvalid`). A design without such a pair
  is byte-identical (Zircon 8x2, thesis dw16, dw32 static checked under aha's vcompare).
- The owner map is process-global, like magma's definition cache: names depend on the order
  types are first generated in a process (deterministic for one garnet.py run).
- Test: `tests/common/test_mux_aoi.py::test_aoi_mux_inner_names_unique_per_type`.

## Tests

`PATH=/cad/oss-cad-suite/bin:$PATH python -m pytest -q tests/common/test_mux_aoi.py` (21 tests,
~1.5 min; fault + verilator, which /aha has only under /cad/oss-cad-suite). Run from a private
clone with `PYTHONPATH=<clone>` to test it instead of the installed /aha/gemstone.
Style: `python -m pycodestyle` with setup.cfg (80 columns); the AOI file has 12 old findings,
add none.

## CI

GitHub "CI Test" (linux.yml, docker keyiz/garnet-flow) fails at "Install deps" before any test
runs: pip builds Z3 from source and its cmake configure fails (2026-10-23, run on c3f0acc). Not a
code failure; master has had no recent runs. Use `[skip ci]` for docs-only commits.
