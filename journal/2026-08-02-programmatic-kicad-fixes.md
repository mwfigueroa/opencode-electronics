# 2026-08-02 (fifth entry) — Programmatic KiCad fixes: applying review findings headlessly

**TL;DR:** Took the asac-fc-rev-a review findings and fixed them directly on the files — no GUI. 4 ERC errors, 8 footprint-attribute errors, and 2 zone-priority errors cleared and verified by ERC/DRC re-runs. Two honest mistakes along the way (duplicate refs, floating-label trap) produced the most useful lessons of the day.

---

## The workflow that emerged

```
backup → inspect (pcbnew / sexp parse) → edit → kicad-cli ERC/DRC re-run → compare counts
```

Every edit was verified by re-running the checks. This loop is the core of a trustworthy "AI edits your PCB files" workflow — never edit without a verification pass.

## Fixes applied (all verified)

| Fix | Before | After |
|---|---|---|
| `power:PWR_FLAG` on GND, VBAT, VBUS, U5.VI rail | 4 ERC errors | **0** |
| Footprint `attr` SMD/TH corrected on 8 connectors/switch | 8 DRC errors | **0** |
| Overlapping GND zones → priority 1 on the small one | 2 DRC errors | **0** |

Techniques used:

- **Footprint attrs + zone priority** via `pcbnew` Python API (`LoadBoard` → mutate → `SaveBoard`). Note: saving through pcbnew re-serializes the whole file — `git diff` gets large but it's formatting normalization, not logic changes.
- **PWR_FLAG injection** into `.kicad_sch`: the symbol wasn't embedded in the file, so the definition was extracted from the official `power.kicad_sym` (Windows KiCad share dir), renamed to `power:PWR_FLAG`, injected into `lib_symbols`, plus 4 instances placed at exact wire/pin coordinates found by parsing the file.

## Mistake #1: duplicate reference designators

First injection used `#PWR0121–123`, assuming refs maxed at `#PWR0120` (the one instance I had sampled). They actually went to `#PWR0157` — my flags collided with existing GND/+1V1 symbols and ERC output became confusing garbage. **Fix:** restored from backup, re-injected with refs above the real max. Lesson: *always* enumerate existing refs before minting new ones.

## Mistake #2 / discovery: the floating VBUS label

The VBUS flag placed at the label's anchor `(307.975, 168.275)` did **not** drive the net. Root cause: the schematic came from a 50-mil-grid source, and many elements sit at half-grid coordinates. The VBUS label *looks* attached to its wire but is electrically floating — and the wire endpoints themselves are at half-grid positions. This single discovery explains the 340 `endpoint_off_grid` warnings and is exactly the kind of silent connectivity bug that survives visual inspection.

Practical rule learned: when attaching anything programmatically, use **exact wire endpoints / junctions / pin coordinates** read from the file — never label anchors, never "nice round" coordinates.

## What was deliberately NOT fixed

- 43 `net_conflict` + 49 schematic-parity issues → need *Update PCB from Schematic* with human review (it renames pads/nets; a decision, not a mechanical fix).
- The AMS1117 input-voltage question (VBAT vs 15 V max) → design decision.
- The 340 off-grid warnings → recommend a GUI re-grid pass before heavy editing.

## Tooling notes

- `kicad-cli` ERC/DRC as a CI-style gate after every edit works beautifully. This repo's `skills/kicad-review` now documents the WSL-native CLI as primary.
- The project is a git repo → every edit was visible in `git diff`; backups were still taken before touching anything. Both files left uncommitted for the owner to review.
- The review report in the project folder got an addendum with the fixes and the off-grid root-cause finding.
