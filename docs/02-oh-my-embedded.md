# 02 — oh-my-embedded plugin

[captainluzik/oh-my-embedded](https://github.com/captainluzik/oh-my-embedded) turns OpenCode into an embedded-systems workbench: specialized agents, on-demand skills with their own MCP servers, and always-available calculation tools.

## Prerequisites

- OpenCode working (see [01](01-opencode-on-windows-wsl.md))
- Bun runtime (OpenCode plugins execute on Bun):

```bash
curl -fsSL https://bun.sh/install | bash    # installs to ~/.bun
export PATH="$HOME/.bun/bin:$PATH"
```

## Install

```bash
bunx oh-my-embedded install --no-tui
```

The installer registers the plugin in `~/.config/opencode/opencode.json`, copies 6 skills / 5 commands / 3 agents into `~/.config/opencode/`, and installs most MCP server dependencies automatically.

Then **restart OpenCode**.

## What you get

### Agents (Tab to cycle)

| Agent | Mode | Domain |
|---|---|---|
| `@embedded` | primary | ESP32/STM32 firmware, FreeRTOS, peripherals, power management |
| `@hardware` | primary | Schematics, layout, component selection, RF |
| `@review-hw` | subagent | Read-only firmware review, P0–P3 severity findings |

### Skills (load on demand, each may start its own MCP servers)

| Skill | MCP servers | Domain |
|---|---|---|
| `embedded-engineer` | esp-mcp | ESP-IDF, FreeRTOS, WiFi/BLE, deep sleep, OTA |
| `embedded-review` | — | Memory safety, ISR, RTOS pitfalls, C/C++ UB |
| `pcb-designer` | kicad-mcp-server | KiCad design, DRC, Gerber, JLCPCB |
| `component-sourcer` | @jlcpcb/mcp | LCSC/JLCPCB catalog, BOM optimization |
| `firmware-debugger` | mcp-server-gdb, serial-mcp-server | GDB, JTAG/SWD, serial monitor |
| `circuit-simulator` | spicebridge | ngspice simulations |

### Commands

`/flash` · `/debug` · `/bom` · `/power-budget` · `/review-firmware`

### Always-on calculation tools (no install needed)

`embedded-power-calculator` · `embedded-impedance-calculator` · `embedded-resistor-divider` · `embedded-pin-mapper` · `embedded-decoupling-advisor`

## MCP dependency status after install

| Server | Auto-installed | Notes |
|---|---|---|
| esp-mcp | ✅ (via uv) | Needs ESP-IDF sourced for full functionality |
| kicad-mcp-server | ✅ (via npm) | Needs KiCad installed for DRC/Gerber |
| spicebridge | ✅ (via uv) | Needs `ngspice` (`sudo apt install ngspice`) |
| @jlcpcb/mcp | ✅ (via npm/npx) | Optional `NEXAR_API_KEY` for Octopart |
| mcp-server-gdb | ⚠️ skipped | Needs Rust: `cargo install mcp-server-gdb --locked` |
| serial-mcp-server | ⚠️ skipped | Needs Rust: `cargo install serial-mcp-server --locked` |

To finish the skipped ones:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
sudo apt install -y pkg-config libudev-dev   # required by serial-mcp-server (libudev-sys)
cargo install mcp-server-gdb --locked
cargo install serial-mcp-server --locked
```

Two gotchas (details in [journal/2026-08-02-hardware-in-the-loop](../journal/2026-08-02-hardware-in-the-loop.md)):

1. The plugin detects these servers via `which` at startup. Cargo installs to `~/.cargo/bin`, which is missing from non-interactive PATHs (e.g. launching OpenCode through a Windows→WSL wrapper). Fix with symlinks:
   ```bash
   ln -sf ~/.cargo/bin/mcp-server-gdb    ~/.local/bin/
   ln -sf ~/.cargo/bin/serial-mcp-server ~/.local/bin/
   ```
2. `mcp-server-gdb` creates its log directory relative to its CWD — it panics if launched from a read-only directory. Fine under OpenCode (project dir), annoying in ad-hoc smoke tests.

## Verify

```bash
opencode debug skill    # the 6 new skills should be listed
opencode mcp list       # esp-mcp, jlcpcb-mcp, spicebridge should connect
```

In the TUI: press **Tab** → `@embedded` / `@hardware` appear; type `/flash` → command exists.

## Uninstall

```bash
jq '.plugin = [.plugin[] | select(. != "oh-my-embedded")]' \
  ~/.config/opencode/opencode.json > /tmp/oc.json && \
  mv /tmp/oc.json ~/.config/opencode/opencode.json
rm -rf ~/.config/opencode/skills/{embedded-engineer,embedded-review,pcb-designer,component-sourcer,firmware-debugger,circuit-simulator}
rm -f  ~/.config/opencode/commands/{flash,debug,bom,power-budget,review-firmware}.md
rm -f  ~/.config/opencode/agents/{embedded,hardware,review-hw}.md
```
