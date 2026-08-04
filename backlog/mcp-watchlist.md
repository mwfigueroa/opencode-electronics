# MCP watchlist & backlog

Servers and ideas tracked for this toolchain. Star counts are snapshots (2026-08-02) — recheck before adopting anything; this space moves weekly.

## Installed and in use

| Server | Source | Role |
|---|---|---|
| oh-my-embedded | [captainluzik/oh-my-embedded](https://github.com/captainluzik/oh-my-embedded) | Plugin: agents, skills, calc tools |
| kicad-mcp | [lamaalrajih/kicad-mcp](https://github.com/lamaalrajih/kicad-mcp) ~492★ | Global KiCad analysis |
| esp-mcp | [horw/esp-mcp](https://github.com/horw/esp-mcp) | ESP-IDF tooling (via plugin) |
| kicad-mcp-server | [mixelpixx/KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server) | KiCad inside pcb-designer skill |
| jlcpcb-mcp | [l3wi/jlc-cli](https://github.com/l3wi/jlc-cli) | JLCPCB/LCSC sourcing |
| spicebridge | [clanker-lover/spicebridge](https://github.com/clanker-lover/spicebridge) | ngspice via MCP |

## Watching (electronics / firmware)

| Project | ~★ | Why it's interesting |
|---|---|---|
| [oaslananka/kicad-mcp-pro](https://github.com/oaslananka/kicad-mcp-pro) | 42 | DFM + manufacturing review on top of ERC/DRC |
| [oaslananka/easyeda-mcp-pro](https://github.com/oaslananka/easyeda-mcp-pro) | 26 | EasyEDA Pro + BOM sourcing across distributors |
| [charlesmmorais/coppermind](https://github.com/charlesmmorais/coppermind) | 0 | **Citable IPC-2221 rules engine** for KiCad — unique |
| [ByteAsk/ByteAsk-Embedded-MCP](https://github.com/ByteAsk/ByteAsk-Embedded-MCP) | 23 | Embedded docs with page-level citations (ARM, MISRA) — closest thing to a "Context7 for firmware" |
| [es617/serial-mcp-server](https://github.com/es617/serial-mcp-server) | 13 | Serial port as MCP tool (pip-installable variant of the cargo one) |
| [flaco-source/altium-mcp](https://github.com/flaco-source/altium-mcp) | 8 | Altium Designer bridge via DelphiScript |
| Context7 | — | Already indexes ESP-IDF, FreeRTOS, Zephyr, PlatformIO, Arduino docs |
| [platformio/platformio-core](https://github.com/platformio/platformio-core) | — | CLI for 1000+ boards, 40+ platforms (STM32, NXP, ESP32, RISC-V, etc.). Candidate for our own MCP bridge. |
| [STMicroelectronics/STM32CubeMX](https://github.com/STMicroelectronics/STM32CubeMX) | — | HAL code gen — headless scripting mode via `STM32CubeMX -s script` or CubeMX MCU Finder for pinout. Evaluate as MCP or keep as manual pre-step. |
| [nxp-mcuxpresso/mcux-sdk](https://github.com/nxp-mcuxpresso/mcux-sdk) | — | NXP MCUXpresso SDK. Open-source core drivers; config tools still Windows-only. Zephyr covers most NXP targets; PlatformIO uses framework-lpcxpresso / framework-mcux. |

## Multi-MCU expansion (Phase 5b — build our own?)

- **PlatformIO MCP bridge** — wrap `platformio` CLI as an MCP server. Tools: `init`, `build`, `upload`, `monitor`, `debug`, `test`, `boards`, `update`. Python, stdio transport like `esp-mcp`. This single bridge unlocks STM32, NXP, RISC-V, native ARM, and everything PlatformIO supports — far more efficient than writing per-vendor MCPs.
- **`stm32-engineer` skill** — HAL/CubeMX-aware agent: knows STM32F1/F4/H7 peripheral register maps, clock trees, DMA, and CubeMX project patterns. Guides on `stm32cubeprogrammer` for flashing/option bytes vs OpenOCD.
- **`nxp-engineer` skill** — MCUXpresso/LPC/i.MX RT patterns: pin muxing (IOCON/SWM), FlexComm, SCTimer. Guides on LPC-Link2 / MCU-Link probes.
- **ARM Cortex-M RAG pipeline** — ByteAsk-Embedded-MCP already covers ARM/MISRA docs generically. Evaluate whether we need to self-host vendor PDFs (STM32 ref manuals, NXP user manuals) for deeper citations.

## Mechanical CAD (Phase 6 research)

Nothing adopted yet. Evaluation axes: API maturity, where the server must run (Windows vs Linux), and read-only (interrogate a model) vs read-write (drive modeling ops).

- **FreeCAD** — open source, Python API, runs headless on Linux. Easiest target; good proving ground for CAD-agent patterns.
- **Fusion 360** — documented API (Python/C++ add-ins). A bridge would wrap an add-in exposing ops to MCP.
- **SolidWorks** — COM API, Windows-only. Server would need to run on the Windows side (possibly called from WSL via interop).

## Ideas (build our own?)

- **Lab-instruments MCP** — wrap PyVISA/sigrok for bench gear: Rigol DS1054Z scope (SCPI over LAN/USBTMC), programmable PSU, logic analyzers (sigrok). Tools: `measure`, `capture_waveform`, `screenshot`, `set_trigger`. The DS1054Z plumbing is already done (see journal 2026-08-02-rigol-ds1054z).
- **Datasheet RAG MCP** — local server over manufacturer PDFs (reference manuals, driver ICs, motor drives) with page citations, à la ByteAsk but self-hosted on our own document set.
- **Design-rules server** — IPC-2221 clearances/creepage, JLCPCB capabilities, and house rules as a queryable MCP tool (coppermind may make this redundant — watch it first).
- **Fixture/test-jig tooling** — domain MCP servers for production test equipment (jig state machines, DUT databases).
