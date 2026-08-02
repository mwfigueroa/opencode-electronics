# 2026-08-02 (fourth entry) — First real board review: asac-fc-rev-a

**TL;DR:** Ran the full kicad-review workflow on a real project (ASAC FC rev A, an open-source RP2040 flight controller). ERC + DRC via WSL `kicad-cli` 10.0.5, component/net extraction via Python, board stats via the `pcbnew` API, structured report saved next to the project. The toolchain delivers; the board has a schematic↔PCB sync problem as its main finding.

---

## What was done

1. **ERC**: 530 violations (4 errors — all `power_pin_not_driven`, fixable with `PWR_FLAG`; 526 warnings, mostly legacy-grid noise).
2. **DRC**: 125 violations + 49 schematic-parity issues; **0 unconnected nets**.
3. **Specs extraction** (65 components): RP2040 + W25Q128 flash, MPU-6050 IMU, 2× AMS1117 (5 V → 3.3 V), USB-C, 4× ESC out, 2× I2C, 2× UART, SWD, buzzer, RGB LEDs, VBAT/CURR analog inputs. Board: 36×43 mm, 2 layers, 119 footprints, 148 vias, GND zones both sides.
4. **Key findings**:
   - Schematic↔PCB desync (49 parity + 43 `net_conflict` warnings) — the #1 action item.
   - AMS1117-5.0 input limit (15 V) vs possible 4S VBAT (16.8 V) — needs confirmation.
   - USB-C CC pull-downs must be 5.1 kΩ — verify.
   - Two overlapping GND zones, same priority; 8 connector footprints with wrong SMD/TH attribute; gerbers on disk stale (2023).
   - Verified-good: RP2040 decoupling scheme, 27.4 Ω USB series resistors, MPU-6050 REGOUT/CPOUT caps, I2C pull-ups, crystal load caps.
5. **Report**: `kicad-review-asac-fc-rev-a-2026-08-02.md` saved in the project folder with prioritized action items.

## Tooling notes

- `kicad-cli` from WSL handled everything — no need to call the Windows `.exe`. The kicad-review skill was updated to prefer the WSL-native CLI and document the `pcbnew` Python path.
- `sexpdata`-based regex extraction of KiCad 10 S-expressions works well for inventories; net labels give a quick functional map before any GUI is opened.
- `pcbnew.LoadBoard()` is the fastest way to get board stats (size, layers, vias, zones) headlessly.

## Pending (from the review)

- The board's action items live in the report — biggest ones: schematic/PCB re-sync and the VBAT/LDO voltage question.
- Still open from earlier entries: real HIL test (ESP32 + usbipd), upstream the kicad-mcp-server Python-deps issue, Phase 6 CAD research.
