---
name: spice-sim
description: Use when simulating an electronic circuit with SPICE — running transient (.tran), AC/frequency response (.ac), DC operating point (.op), DC sweep, Bode plot, step response, Monte Carlo, or measuring gain, bandwidth, phase margin, ripple, settling time. Triggers on simulate, SPICE, netlist, .cir, Verilog-A, QSPICE, LTspice, ngspice, frequency response, transient analysis, AC analysis. Use ONLY for circuit simulation tasks.
---

# SPICE Simulation Skill

Wrap LTspice, Qspice, and ngspice into one workflow: pick the right engine for the
analysis, generate/edit the netlist, run it in batch (headless), and parse the results.
Integrates with `kicad-review` (step 6) to simulate critical analog blocks identified
during PCB/schematic review.

## Environment (WSL → Windows exes)

All three live on Windows; call them from bash via /mnt/c paths (quote spaces).

- **LTspice**: `/mnt/c/Users/marti/AppData/Local/Programs/ADI/LTspice/LTspice.exe`
  - Fastest analog/power. Best models for SMPS, filters, control loops.
- **Qspice**: `/mnt/c/Program Files/QSPICE/QSPICE64.exe`
  - Verilog-A, digital mixed-signal, C++ output. Modern engine (same author as LTspice).
- **ngspice**: bundled with KiCad 10 — locate via
  `ls "/mnt/c/Program Files/KiCad/"*/bin/ngspice.exe` or `*/lib/*/ngspice.exe`.
  - Native to KiCad schematics. Best for scripted/Monte Carlo. Open SPICE standard.

Verify paths at runtime — KiCad/ADI may relocate binaries between versions.

## Engine selection

| Task / analysis | Engine | Why |
|-----------------|--------|-----|
| SMPS / power / efficiency / ripple | **LTspice** | ADI power models, fastest transient |
| Filter, amplifier, Bode, phase margin | **LTspice** | fast .ac, good .meas |
| DC op point, bias, DC sweep | any (LTspice default) | all handle it |
| Verilog-A / digital / mixed-signal | **Qspice** | only one with Verilog-A + digital |
| Simulate the actual KiCad schematic | **ngspice** | KiCad exports ngspice netlist natively |
| Monte Carlo / parameter stepping (scripted) | **ngspice** | best control-block scripting |
| Behavioral / ideal fast sandbox | **LTspice** | BV/BI sources, instant |

Default when unsure: **LTspice** (analog) or **Qspice** (if Verilog/digital mentioned).

## Workflow

### 1. Determine the source
- **KiCad schematic**: export netlist via
  `kicad-cli sch export netlist --format spice -o sim.cir "<root>.kicad_sch"`
  (run `kicad-cli sch export netlist --help` to confirm format name in KiCad 10;
   fallback: build the netlist manually from .kicad_sch components + nets).
- **Existing netlist** (`.cir`/`.net`/`.sp`): use directly.
- **Described circuit**: write the netlist from scratch (component values, topology,
  sources, analysis commands).

### 2. Set up measurements (.meas)
Add `.meas` statements to extract the key figures so the result is parseable from the
.log without plotting:
- Gain: `.meas ac gain_db max db(mag(V(out)/V(in)))`
- Bandwidth: `.meas ac bw trig db(mag(V(out)))=gain_db-3 rise=1`
- Phase margin: `.meas ac pm param 180+ph(V(out)/V(in)) at=freq_where_gain_0db`
- Transient: `.meas tran vpp PP V(out) from=... to=...`
- Settling time: `.meas tran ts trig ... targ ...`
LTspice and Qspice support .meas; ngspice uses `meas` (no dot) in control blocks.

### 3. Run the engine (batch / headless)
- **LTspice**: `LTspice.exe -b sim.cir` → writes `sim.log` + `sim.raw` in cwd.
  Run from a writable dir (e.g. /tmp/spice/ or the project dir).
- **Qspice**: `QSPICE64.exe -b sim.cir` → `sim.log` + output.
- **ngspice**: `ngspice -b sim.cir` (or `ngspice -b -o out.txt sim.cir`) → stdout/out.txt.

Run via bash from WSL; the .exe writes to the Windows-visible cwd. Prefer a work dir
under the project so artifacts are findable. Use a timeout (long transient sims can hang).

### 4. Parse results
- `.meas` values → grep the `.log`:
  `grep -iE "meas|gain|bw|pm|vpp|settling" sim.log`
- Errors/convergence → grep `.log` for `error|fatal|convergence|timestep`.
- ngspice prints measurements to stdout — capture and parse directly.
- For waveforms: the .raw is binary (LTspice) — don't try to parse it in text. Rely on
  .meas for numbers; tell the user to open the .raw in the GUI if they need plots.

### 5. Report
- Analysis type + engine used + netlist file.
- Key measurements (table: quantity / value / spec / pass-fail if spec given).
- Convergence notes / warnings from the log.
- If spec given (e.g. "BW > 100kHz", "PM > 45°"), state pass/fail per metric.
- Save netlist + log to the project (e.g. `sim/<block>.cir`, `sim/<block>.log`).

## Integration with kicad-review

When `kicad-review` (step 6) flags a critical analog block (regulator feedback, filter,
oscillator, current sense, level shifter), it calls this skill to:
1. Extract that block to a netlist (or export the KiCad subcircuit).
2. Run the relevant analysis (AC loop stability for regulators, transient startup for
   oscillators, AC response for filters).
3. Feed the measured numbers back into the kicad-review action-items report.

## Verilog-A / digital (Qspice only)

- `.va` files: compile with Qspice (it ingests Verilog-A directly in the netlist via
  `Xname ... model.va`). Run `QSPICE64.exe -b sim.cir`.
- Digital: Qspice supports digital primitives and C++ device models — use when the
  circuit has logic mixed with analog (gate drivers, comparators with hysteresis, etc.).
- LTspice and ngspice do NOT do Verilog-A — route those requests to Qspice.

## Notes

- Always run from a writable work directory; the engines drop .log/.raw next to the .cir.
- Add `.option nomod` and `.option plotwinsize=0` (LTspice) for clean waveforms/compression-off.
- For long transients, set a timeout on the bash call and warn the user it may take minutes.
- If an engine is missing (e.g. ngspice not located), fall back to another that can run
  the same netlist (most plain SPICE netlists are portable across all three) and note it.
- Convergence problems: add `.option gmin=1e-10 reltol=1e-3 itl4=200`, check for floating
  nodes, missing DC paths, or ideal voltage source loops.
