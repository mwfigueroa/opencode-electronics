# 2026-08-04 — PlatformIO MCP bridge

## What changed

Built and connected the **PlatformIO MCP bridge** — the first new MCP server
created for this project. Previously the stack was ESP32-only via `esp-mcp`;
now PlatformIO CLI is available as 15 MCP tools covering STM32, NXP, ESP32,
RISC-V, and 1000+ boards.

## The gap

The toolchain had:
- **ESP32**: ESP-IDF via `esp-mcp` (full coverage)
- **Everything else**: nothing — no ARM GCC, no STM32/NXP, no PlatformIO

General-purpose AI coding agents know very little about embedded hardware,
so without tool-backed access to the PlatformIO CLI, multi-MCU work would be
limited to manual commands outside the agent.

## What was built

**Location:** `/home/martinf/opt/platformio-mcp/`

A Python MCP server (`FastMCP`, `mcp==1.5.0`, same version as `esp-mcp`)
wrapping the `pio` CLI via `asyncio.create_subprocess_shell`. All tools are
`async`, return `(stdout, stderr)` tuples, and include timing info.

### Tools (15 total)

| Tool | What it does |
|---|---|
| `pio_project_init` | Create new project: `--board`, `--platform`, `--project-name` |
| `pio_run` | Build/compile: `--target`, `--environment`, `--verbose` |
| `pio_upload` | Flash firmware: `--port`, `--environment` |
| `pio_clean` | Clean build artifacts |
| `pio_device_list` | List connected serial devices |
| `pio_device_monitor` | Capture serial output (timed, max 60s) |
| `pio_boards` | Search boards (`stm32`, `esp32`, `teensy`, ...), JSON output |
| `pio_test` | Run unit tests |
| `pio_check` | Static analysis (cppcheck) |
| `pio_lib_install` | Install libraries by name/ID/URL |
| `pio_lib_list` | List installed libs (JSON) |
| `pio_lib_search` | Search registry (JSON) |
| `pio_debug_start` | Start GDB debug server |
| `pio_update` | Update PlatformIO Core, platforms, libraries |
| `pio_system_info` | Version, paths, installed platforms |

### Stack

- MCP SDK: `mcp==1.5.0` (pinned to match `esp-mcp`, avoids v2 API break)
- Venv: `uv`-managed, Python 3.11.15
- PlatformIO Core: 6.1.19 (already installed system-wide)
- Registered in `~/.config/opencode/opencode.jsonc` and repo `config/opencode.jsonc`

## Verification

Three tools tested end-to-end before marking done:

```
pio_system_info  → PlatformIO Core 6.1.19, Python 3.12.3, Linux WSL2
pio_boards       → Found STM32F103 boards (Blue Pill, Black Pill, etc.) 
                    with debug tool info (stlink, cmsis-dap, jlink)
pio_device_list  → Detects /dev/ttyS0-7
```

## Repo changes

- `ROADMAP.md`: Phase 5b created + PlatformIO MCP bridge marked `[x]`
- `backlog/mcp-watchlist.md`: platformio-core, STM32CubeMX, mcux-sdk tracked + "build our own" section
- `config/opencode.jsonc`: `platformio` MCP server entry added
- `journal/2026-08-04-platformio-mcp-bridge.md`: this file

## Next steps (pending)

The bridge is ready. What remains in Phase 5b:

1. **`arm-none-eabi-gcc`** — install `gcc-arm-none-eabi` package and verify
2. **ARM GDB config** — verify `arm-none-eabi-gdb` + `mcp-server-gdb` + OpenOCD 
   works over ST-Link/CMSIS-DAP
3. **Skills** — write `stm32-engineer` SKILL.md and `nxp-engineer` SKILL.md
4. **Physical test** — flash/debug a real STM32F103 Blue Pill and an NXP 
   LPC1768 (or i.MX RT1010)
5. **`embedded-review` audit** — check if the skill covers ARM Cortex-M 
   ISR/memory patterns

The PlatformIO bridge alone unlocks compile/flash/monitor for STM32 without
waiting for the rest — the agent can already `pio_project_init --board bluepill_f103c8`
and `pio_upload` today.
