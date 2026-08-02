---
name: kicad-review
description: Use when reviewing or auditing a KiCad project (.kicad_pro, .kicad_sch, .kicad_pcb), running ERC/DRC, or doing PCB/schematic design review. Triggers on KiCad files, PCB layout review, schematic review, ERC, DRC, decoupling, return path, ground plane, signal integrity, or analog block simulation. Use ONLY for electronics design review tasks on KiCad projects.
---

# KiCad Project Review Skill

Workflow to audit a KiCad project: run ERC/DRC, parse the schematic/PCB text files,
apply an engineering design checklist, and optionally simulate critical analog blocks
with ngspice. Produces a structured report.

## Environment

- **Preferred:** KiCad 10.0.5 is installed natively in WSL — just call `kicad-cli`
  (version-matched to the Windows desktop via `ppa:kicad/kicad-10.0-releases`).
- Fallback: KiCad also exists on **Windows**, CLI at:
  `/mnt/c/Program Files/KiCad/10.0/bin/kicad-cli.exe`
  (verify with `ls "/mnt/c/Program Files/KiCad/"*/bin/kicad-cli.exe` — version may change).
- `pcbnew` Python API available with `PYTHONPATH=/usr/lib/python3/dist-packages python3`.
- Call it directly from bash (the /mnt/c path works). Quote paths with spaces.
- ngspice is bundled with KiCad; locate it under the KiCad bin/ or via the project's
  simulation. If not found, skip SPICE steps and note it.
- KiCad files (`.kicad_sch`, `.kicad_pcb`, `.kicad_pro`) are S-expression text — readable
  and greppable. They may be under /mnt/c/... (Windows fs) or in WSL.

## Workflow

### 1. Locate the project
- Find the `.kicad_pro` (project root). From it, identify the `.kicad_sch` (root schematic,
  may reference hierarchical sub-sheets) and `.kicad_pcb` (board).
- If the user points to a specific file, walk up to find the `.kicad_pro`.

### 2. Run ERC (Electrical Rules Check)
- Discover exact flags: `kicad-cli sch erc --help` (run via the .exe path).
- Typical: `kicad-cli sch erc -o erc.txt "<root>.kicad_sch"` (or `--output`).
- Parse `erc.txt`: list violations by severity (errors vs warnings), group by type
  (unconnected, conflicting drivers, power pin not driven, ERC off-label, etc.).
- Note: hierarchical sheets need the root schematic; ERC resolves the full hierarchy.

### 3. Run DRC (Design Rules Check)
- Discover flags: `kicad-cli pcb drc --help`.
- Typical: `kicad-cli pcb drc -o drc.txt "<board>.kicad_pcb"`.
- Parse `drc.txt`: track width, clearance, courtyard, unconnected items, silk over pad,
  hole size, starved thermals, etc. Report counts + top offenders.

### 4. Schematic audit (parse .kicad_sch text)
Grep/read the schematic S-expressions and check:
- **Power nets**: every power label (GND, +3V3, +5V, VCC...) has a source (regulator/
  power input). Flag power flags missing or power nets driven by >1 source.
- **Decoupling**: each IC power pin has a bypass cap close (within ~10mm in PCB, or
  present in schematic). Flag ICs without decoupling.
- **Unconnected pins**: nets with only one pin (dangling) beyond ERC's catch.
- **Pull-ups/pull-downs**: I2C/SPI/RESET/ENABLE lines have defined levels (not floating).
- **Crystal/load caps**: oscillator pins have matching load caps per crystal spec.
- **Power sequencing / reverse polarity protection** on power inputs.
- **Voltage ratings**: caps rated above the rail they sit on (derating ~50%).
- **Reference designators**: sequential, no duplicates, no missing.

### 5. PCB audit (parse .kicad_pcb text)
Check by reading the layout S-expressions:
- **Ground return paths**: critical signals (clocks, high-speed, analog) have a continuous
  ground reference (no cuts under them). Flag traces crossing plane splits.
- **Decoupling placement**: bypass caps near their IC power pins (via.footprint proximity).
- **Trace width vs current**: power traces adequate for current (use IPC-2150 rule of thumb;
  flag < 0.5mm for > 1A as review point).
- **Component placement**: connectors on board edge, bypass caps adjacent to pins,
  crystal close to MCU, analog away from switching regulators.
- **Via count / starved thermals** on power pins.
- **Silkscreen**: reference designators visible, not overlapping pads.
- **Differential pairs / length matching**: if present, check gap/width consistent and
  length-matched (read length-tuning info if serialized).
- **Unrouted nets** (beyond DRC).

### 6. SPICE simulation (optional, for critical analog blocks)
- Export a netlist: `kicad-cli sch export netlist --format spice -o sim.cir "<sch>"`
  (check `--help` for available formats in KiCad 10; fallback: build netlist manually
  from the schematic by reading components + nets).
- Run ngspice on the critical block (regulator feedback, filter response, oscillator
  startup, current sense) — DC op, AC sweep, or transient as relevant.
- Locate ngspice: `ls "/mnt/c/Program Files/KiCad/"*/bin/ngspice.exe` or `*/lib/*/ngspice.exe`.
  Call via the .exe path. If unavailable, skip + note.

### 7. Report format
Produce a markdown report with sections:
1. **Summary** (project, KiCad version, file inventory)
2. **ERC results** (errors/warnings counts, top issues)
3. **DRC results** (counts, top offenders)
4. **Schematic audit** (findings by category, severity)
5. **PCB/layout audit** (findings by category, severity)
6. **Simulation** (if run — setup + key results)
7. **Action items** (prioritized list: critical / recommended / optional)

Save the report as `kicad-review-<project>-<date>.md` in the project root, and
print the action items to the chat.

## Notes

- Always run `--help` on kicad-cli subcommands first — flag names/positions vary
  between KiCad versions. Don't assume; verify.
- Paths with spaces (Program Files) MUST be quoted in bash.
- If kicad-cli.exe is not found, still do the manual text audit (steps 4-5) from the
  .kicad_sch/.kicad_pcb files and note that ERC/DRC were skipped.
- Severity guide: critical = won't work / damage risk; recommended = reliability/EMC;
  optional = polish.
