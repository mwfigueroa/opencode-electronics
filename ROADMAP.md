# Roadmap

From a working CLI to a full AI-assisted hardware engineering environment.
Status legend: ✅ done · 🟡 partial · ⬜ pending

---

## Phase 0 — CLI foundation ✅

**Goal:** OpenCode running reliably from any terminal (WSL and Windows).

- [x] OpenCode installed in WSL2 via `curl -fsSL https://opencode.ai/install | bash`
- [x] `opencode.cmd` wrapper in a Windows `PATH` directory so PowerShell/CMD/Windows Terminal can launch it (forwards to the WSL binary)
- [x] Bun runtime installed (required for OpenCode plugins)

## Phase 1 — Embedded / firmware agents ✅

**Goal:** domain-specific agents, skills, and calculation tools for firmware work.

- [x] [oh-my-embedded](https://github.com/captainluzik/oh-my-embedded) plugin installed
- [x] Agents: `@embedded` (firmware), `@hardware` (PCB/RF), `@review-hw` (read-only reviewer)
- [x] Commands: `/flash`, `/debug`, `/bom`, `/power-budget`, `/review-firmware`
- [x] Always-on tools: power calculator, impedance/RF matching, resistor divider (E24), ESP32 pin mapper, decoupling advisor
- [x] `esp-mcp` connected (ESP-IDF docs/tooling via MCP)

## Phase 2 — PCB design ✅

**Goal:** agent can read, analyze, and check KiCad projects.

- [x] [kicad-mcp](https://github.com/lamaalrajih/kicad-mcp) installed (`~/opt/kicad-mcp`) and registered globally in OpenCode
- [x] Working without a KiCad binary: project listing, netlist extraction, BOM analysis, circuit pattern recognition
- [x] KiCad installed **inside WSL** — 10.0.5 via `ppa:kicad/kicad-10.0-releases`, version-matched to the Windows desktop (Ubuntu repos ship 7.x, which can't read v10 files)
- [x] DRC verified end-to-end on a real KiCad 10 project via `kicad-cli`
- [x] Plugin's own `kicad-mcp` server awake (needed `pcbnew.py` + its Python `requirements.txt` — silent-hang bug documented in journal)
- [ ] Evaluate [kicad-mcp-pro](https://github.com/oaslananka/kicad-mcp-pro) (DFM, manufacturing review) and [coppermind](https://github.com/charlesmmorais/coppermind) (IPC-2221 citable rules engine) — see [backlog](backlog/mcp-watchlist.md)

## Phase 3 — Circuit simulation ✅

**Goal:** run and analyze SPICE simulations from the agent.

- [x] `spicebridge` MCP server connected (ngspice)
- [x] Custom `spice-sim` skill (transient, AC, operating point, measurements)
- [x] ngspice engine installed and verified (`ngspice -b` batch run OK)
- [x] Python analysis stack: lcapy (symbolic), scikit-rf (RF/S-params), control (Bode, stability margins)
- [ ] Validate end-to-end: agent-driven simulation of a real project power supply (e.g. buck stage)

## Phase 4 — Component sourcing ✅

**Goal:** BOM-aware component search without leaving the agent.

- [x] `jlcpcb-mcp` connected (JLCPCB/LCSC catalog, Basic vs Extended parts)
- [ ] Optional: Nexar/Octopart API key for cross-distributor stock/price search (`NEXAR_API_KEY`)

## Phase 5 — Hardware-in-the-loop 🟡

**Goal:** close the loop: flash, debug, and read logs from real hardware.

- [x] Install Rust toolchain (`rustup`, stable 1.97.1)
- [x] `cargo install mcp-server-gdb --locked` → GDB/OpenOCD debugging via MCP (v0.2.3, connected)
- [x] `cargo install serial-mcp-server --locked` → serial monitor as an MCP tool (v0.1.0, connected; needs `pkg-config libudev-dev` on the system)
- [x] Symlink both binaries into `~/.local/bin` so the plugin detects them regardless of how OpenCode is launched
- [x] OpenOCD 0.12 installed (JTAG/SWD backend) + sigrok-cli 0.7.2 (logic analyzers, SCPI instruments)
- [ ] Test on a real ESP32 target (Jig-Station firmware is the candidate) — needs `usbipd` attach for the serial port and ESP-IDF's `xtensa-esp32-elf-gdb` in WSL

## Phase 5b — Multi-MCU firmware expansion 🟡

**Goal:** expand beyond ESP32 to STM32, NXP, and other ARM Cortex-M platforms — plus RISC-V and any PlatformIO-supported target.

**Why:** the current stack is ESP32-only. ESP-IDF (`esp-mcp`) covers a single vendor. To be a usable lab for real-world embedded work, the toolchain needs to handle STM32 (STM32Cube/HAL), NXP (MCUXpresso), and generic ARM Cortex-M devices. PlatformIO is the most pragmatic bridge — it supports 1000+ boards across 40+ platforms from one CLI.

- [x] `arm-none-eabi-gcc` toolchain (`gcc-arm-none-eabi` package) — v13.2.1 via apt
- [x] PlatformIO CLI installed in WSL — Core 6.1.19 via install script
- [x] **PlatformIO MCP bridge** — deployed on laboratorio machine: 15 tools, Python 3.11, `mcp==1.5.0`, `uv`-managed venv
- [x] ARM GDB configuration — `gdb-multiarch` 15.1 installed + symlinked as `arm-none-eabi-gdb`
- [x] Custom skills: `stm32-engineer` (HAL/LL, DMA, NVIC, ST-Link, PlatformIO templates) and `nxp-engineer` (LPC17xx PINSEL/PCONP, i.MX RT FlexSPI/TCM, Kinetis, CMSIS-DAP)
- [x] Physical test: **NXP FRDM-MCXA153** (Cortex-M33) — flash via PyOCD + CMSIS-DAP, serial verify, debug halt/reg read. Full cycle confirmed.
- [ ] Test on physical STM32 target (e.g. STM32F103 Blue Pill) — flash, debug, serial
- [ ] Test on physical NXP LPC or i.MX RT target — flash, debug, serial
- [ ] Verify `mcp-server-gdb` integration with `arm-none-eabi-gdb` + OpenOCD on physical target
- [ ] Evaluate whether the existing `embedded-review` skill covers ARM Cortex-M ISR/Memory correctly

**Design decisions to make:**
- PlatformIO MCP: light wrapper (just forward CLI) or full tool (parse outputs, manage `platformio.ini`)?
- STM32CubeMX: generate HAL init code headlessly via `java -jar STM32CubeMX` scripting, or rely on PlatformIO's framework-stm32cube + manual pinmux?
- NXP: MCUXpresso Config Tools are Windows-only — invoke from Windows side via `cmd.exe /c` or use PlatformIO's framework-zephyr for NXP targets.

## Phase 6b — Test equipment integration 🟡

**Goal:** make lab instruments accessible from the agent via Python SDKs and SCPI over TCP/IP.

**Why:** the toolchain already designs boards and writes firmware. The missing piece is characterization: measuring
what was built. A full engineering loop needs the scope, signal analyzer, power supply, and electronic load
to be as scriptable as the compiler.

- [x] `pyvisa` + `pyvisa-py` SCPI stack (no NI-VISA required) — v1.16.2
- [x] `SoapySDR` 0.8 with modules: HackRF, Red Pitaya, RTL-SDR, Airspy, BladeRF, UHD, LimeSDR
- [x] **Digilent ADP2230** — pydwf 1.1.19, auto-attach via usbipd, skill done
- [x] **HackRF One** — libhackrf 2023.01.1, python-hackrf 1.5.0.1, SoapySDR, skill done
- [x] **Red Pitaya** — pyvisa SCPI over TCP/IP, SoapySDR, skill done
- [x] **Keysight CXA N9000A** — pyvisa SCPI over LAN (VXI-11), skill done
- [x] **Prodigit 3310F** — pyvisa serial SCPI, skill done
- [x] **Keysight E36231A** — pyvisa SCPI over LAN, skill done
- [x] **Tektronix TBS1102C** — python-usbtmc over USB (WinUSB), cross-instrument verified with ADP2230
- [ ] Physical test on each instrument (capture, sweep, load) — **3/7 done: ADP2230 ✅, E36231A ✅, TBS1102C ✅**
- [ ] MCP bridge: `scpi-mcp` — generic SCPI bridge for any VISA instrument
- [ ] MCP bridge: `pydwf-mcp` — WaveForms SDK bridge for ADP2230
- [ ] MCP bridge: `hackrf-mcp` — SDR bridge for HackRF One

**Design decisions to make:**
- One generic `scpi-mcp` server for all SCPI instruments (N9000A, E36231A, Red Pitaya, Prodigit) or separate MCP servers per instrument?
- SCPI MCP: light wrapper (forward raw commands) or smart (parse responses, high-level measurement functions)?
- Spectrum analyzer data: return raw trace points as JSON arrays or downsampled? (full sweep = 1001 points × 4 bytes = 4 KB)

## Phase 6 — Mechanical CAD ⬜ (research)

**Goal:** extend the workflow to mechanical design — SolidWorks and/or Fusion 360.

Open questions to research:

- **Fusion 360:** has a documented API (add-ins/scripts). An MCP bridge would wrap a Fusion add-in exposing modeling ops.
- **SolidWorks:** Windows COM API — an MCP server would need to run on the Windows side and drive the COM interface.
- **FreeCAD:** open source, Python API, runs on Linux — by far the easiest MCP target and a good proving ground for CAD-agent patterns before touching commercial tools.
- Existing community MCP servers for CAD: monitor the ecosystem (see [backlog](backlog/mcp-watchlist.md)).

Likely order: FreeCAD (proof of concept) → Fusion 360 → SolidWorks.

---

## Guiding principles

1. **Verify, don't assume** — every claimed capability gets tested before it's marked done.
2. **Reproducible** — every setup step lives in [docs/](docs/).
3. **Minimal moving parts** — prefer one well-tested tool over three overlapping ones.
4. **Upstream first** — contribute fixes/feedback to the MCP projects this depends on.
