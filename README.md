# opencode-electronics

> Building an AI-assisted electronics engineering workflow on top of [OpenCode](https://opencode.ai) — from firmware to PCB design, and eventually mechanical CAD (SolidWorks / Fusion 360).

This is a **learning-in-public journal**: what was set up, what worked, what broke, and what's next. Everything is documented as reproducible guides plus dated journal entries, so anyone (including future me) can rebuild the same environment from scratch.

## Why

General-purpose AI coding assistants know very little about embedded systems, PCB design, or hardware workflows. The MCP (Model Context Protocol) ecosystem is starting to fill that gap, but it's young and fragmented. This project tracks the process of assembling, testing, and extending a serious electronics toolchain on OpenCode — and sharing the findings.

## Current state

| Layer | Tooling | Status |
|---|---|---|
| CLI foundation | OpenCode 1.18.11 on WSL2 + `opencode.cmd` wrapper for Windows terminals | ✅ Working |
| Embedded agents | [oh-my-embedded](https://github.com/captainluzik/oh-my-embedded) plugin: `@embedded`, `@hardware`, `@review-hw` | ✅ Installed |
| Firmware context | `esp-mcp` (ESP-IDF tooling via MCP) | ✅ Connected |
| Component sourcing | `jlcpcb-mcp` (JLCPCB/LCSC catalog search) | ✅ Connected |
| Circuit simulation | `spicebridge` (ngspice via MCP) + custom `spice-sim` skill | ✅ Working (ngspice engine verified) |
| PCB design | [kicad-mcp](https://github.com/lamaalrajih/kicad-mcp) + `kicad-mcp-server` + KiCad 10.0.5 in WSL | ✅ Working (DRC verified on real projects) |
| Circuit analysis | Python: lcapy (symbolic), scikit-rf (RF), control (Bode/margins) | ✅ Working |
| Debug & instruments | openocd 0.12 (JTAG/SWD), sigrok-cli 0.7.2 (SCPI/USBTMC/logic analyzers) | ✅ Installed |
| Hardware-in-the-loop | `mcp-server-gdb` + `serial-mcp-server` (Rust) | ✅ Connected; tested on NXP FRDM-MCXA153 |
| Multi-MCU firmware | **`platformio-mcp`** (our own) — PlatformIO bridge for STM32, NXP, ARM, RISC-V | ✅ Built and verified (15 tools, physical test passed) |
| Test equipment | 7 instruments + FPGA: ADP2230, TBS1102C, N9000A, HackRF, Red Pitaya, Prodigit 3310F, E36231A + Nexys A7 | ✅ ADP2230 + E36231A + TBS1102C + Nexys A7 tested |
| Mechanical CAD | SolidWorks / Fusion 360 integration | ⬜ Research phase |

**MCP servers connected: 8/8** — `kicad`, `kicad-mcp`, `esp-mcp`, `jlcpcb-mcp`, `spicebridge`, `mcp-server-gdb`, `serial-mcp-server`, `platformio-mcp` (our own — Phase 5b)

## Lab bench — live instrument map

Physical instruments controllable from OpenCode via natural language. Each is bridged
through USB (usbipd → WSL) or LAN (pyvisa-py / VXI-11).

### Active & verified

| Instrument | Type | Interface | Bridge | Status |
|---|---|---|---|---|
| **Digilent ADP2230** | Oscilloscope / AWG / Logic Analyzer | USB | pydwf (MCP, 18 tools) | 🟢 Tested |
| **Keysight E36231A** | DC Power Supply 30V/30A/200W | LAN `192.168.1.43` | pyvisa-py (VXI-11) | 🟢 Tested |
| **Tektronix TBS1102C** | Oscilloscope 100 MHz / 1 GS/s | USB | python-usbtmc (WinUSB) | 🟢 Tested |
| **NXP FRDM-MCXA153** | Cortex-M33 dev board | USB | CMSIS-DAP + serial | 🟢 Tested |
| **Digilent Nexys A7-100T** | FPGA Artix-7 XC7A100T | USB | openFPGALoader + UART | 🟢 Tested |

### In ecosystem (SDK ready, not on bench now)

| Instrument | Type | Interface | Bridge |
|---|---|---|---|
| Keysight N9000A CXA | Spectrum Analyzer 9 kHz–7.5 GHz | LAN | pyvisa-py (VXI-11) |
| HackRF One | SDR transceiver 1 MHz–6 GHz | USB | python-hackrf / SoapySDR |
| Red Pitaya | FPGA scope / gen / spectrum | LAN | pyvisa-py (SCPI) |
| Prodigit 3310F | DC Electronic Load 300W | RS-232 | pyserial (SCPI-like) |

### Connection topology

```
USB  (usbipd → WSL2)                 LAN  (pyvisa-py, VXI-11)
 ├─ ADP2230       → pydwf             └─ E36231A   → 192.168.1.43
 ├─ TBS1102C      → python-usbtmc        (N9000A, Red Pitaya when on bench)
 ├─ FRDM-MCXA153  → CMSIS-DAP + serial
 └─ Nexys A7      → openFPGALoader + UART
```

### Cross-instrument proven

- **ADP2230 → TBS1102C**: generate + measure, frequency/amplitude verified
- **ADP2230 → Nexys A7 → TBS1102C**: triple-instrument frequency counter (0.13% error)
- **E36231A**: 0–12 V sweep, glitching profiles, < 0.03% voltage accuracy

## Repository layout

```
├── README.md            ← you are here
├── ROADMAP.md           ← phased plan: firmware → PCB → simulation → HIL → instruments → mechanical CAD
├── journal/             ← dated log entries: what was done, verified, and learned
├── docs/                ← reproducible setup guides
├── config/              ← sanitized opencode config examples
├── skills/              ← custom OpenCode skills (11 total: firmware, PCB, instruments)
├── platformio-mcp/      ← PlatformIO MCP bridge source (15 tools)
└── backlog/             ← MCP watchlist, lab-equipment candidates, ideas being evaluated
```

## Custom skills

Drop-in agent skills (copy into `~/.config/opencode/skills/`):

**Firmware:**
- [skills/stm32-engineer](skills/stm32-engineer/SKILL.md) — STM32: HAL/LL, DMA, NVIC, ST-Link, PlatformIO templates
- [skills/nxp-engineer](skills/nxp-engineer/SKILL.md) — NXP: LPC17xx, i.MX RT, Kinetis, CMSIS-DAP

**PCB & Manufacturing:**
- [skills/kicad-review](skills/kicad-review/SKILL.md) — KiCad project audit: ERC/DRC, schematic/PCB checklist
- [skills/manufacturing-data](skills/manufacturing-data/SKILL.md) — BOM, cavity tables, wire harness extraction

**Simulation:**
- [skills/spice-sim](skills/spice-sim/SKILL.md) — SPICE: transient, AC, op-point, measurements

**Test Equipment:**
- [skills/adp2230-scope](skills/adp2230-scope/SKILL.md) — ADP2230: scope, AWG, logic analyzer, Bode plots
- [skills/n9000a-cxa](skills/n9000a-cxa/SKILL.md) — CXA N9000A: phase noise, channel power, spurious mask
- [skills/hackrf-sdr](skills/hackrf-sdr/SKILL.md) — HackRF One: spectrum, IQ capture, GSM/GPS demod
- [skills/redpitaya-scope](skills/redpitaya-scope/SKILL.md) — Red Pitaya: scope, gen, spectrum, LCR
- [skills/prodigit-3310f](skills/prodigit-3310f/SKILL.md) — Prodigit 3310F: CC/CV/CR/CP, battery test
- [skills/e36231a-psu](skills/e36231a-psu/SKILL.md) — Keysight E36231A: precision PSU, sequencing

## Start reading

- [ROADMAP.md](ROADMAP.md) — the plan, phase by phase
- [journal/2026-08-02-initial-setup.md](journal/2026-08-02-initial-setup.md) — day one: from broken CLI to 4 MCP servers connected
- [journal/2026-08-02-hardware-in-the-loop.md](journal/2026-08-02-hardware-in-the-loop.md) — same day: GDB + serial servers, 6 MCP servers connected
- [journal/2026-08-02-circuit-lab-core.md](journal/2026-08-02-circuit-lab-core.md) — same day: KiCad 10 + ngspice + analysis stack, 7/7 servers
- [journal/2026-08-02-first-board-review.md](journal/2026-08-02-first-board-review.md) — same day: first real board review (ASAC FC rev A)
- [journal/2026-08-02-programmatic-kicad-fixes.md](journal/2026-08-02-programmatic-kicad-fixes.md) — same day: fixing review findings headlessly, with two honest mistakes
- [journal/2026-08-04-platformio-mcp-bridge.md](journal/2026-08-04-platformio-mcp-bridge.md) — PlatformIO MCP bridge built (STM32, NXP, ARM, RISC-V) + Phase 5b roadmap
- [journal/2026-08-04-mcxa153-physical-test.md](journal/2026-08-04-mcxa153-physical-test.md) — first physical HIL test: MCXA153 flashed, serial verified, debug probe confirmed
- [journal/2026-08-04-test-equipment.md](journal/2026-08-04-test-equipment.md) — 6 instruments added: scope, SDR, signal analyzer, PSU, DC load, FPGA platform
- [journal/2026-08-05-e36231a-discovery.md](journal/2026-08-05-e36231a-discovery.md) — E36231A: LAN discovery, VXI-11 connection, functional test 0-12V (error < 0.03%)
- [journal/2026-08-05-adp2230-tbs-cross-instrument.md](journal/2026-08-05-adp2230-tbs-cross-instrument.md) — ADP2230 + TBS1102C: cross-instrument verification (generate + measure)
- [journal/2026-08-05-nexys-a7-toolchain.md](journal/2026-08-05-nexys-a7-toolchain.md) — Nexys A7: JTAG discovery, toolchain FPGA (yosys, iverilog, cocotb, LiteX), diseño LED+UART
- [journal/ADP2230-session-2026-08-05.md](journal/ADP2230-session-2026-08-05.md) — ADP2230 MCP: 17 tools implemented, pydwf bridge verified
- [docs/](docs/) — setup guides if you want to replicate this
- [docs/05-e36231a-scpi-reference.md](docs/05-e36231a-scpi-reference.md) — E36231A: referencia SCPI completa (español), ejemplos probados
- [docs/06-tbs1102c-guide.md](docs/06-tbs1102c-guide.md) — TBS1102C: guía completa de capacidades, SCPI probado, casos de uso

## Notes

- Commands and versions are verified on the date of each journal entry. This ecosystem moves fast — expect drift.
- Environment: Windows 11 + WSL2 (Ubuntu 24.04), KiCad on the Windows side, PlatformIO/ESP-IDF for firmware.
- Contributions, suggestions and pointers to MCP servers I missed are welcome via issues.

## License

[MIT](LICENSE)
