# 2026-08-02 — Day one: from broken CLI to 4 MCP servers connected

**TL;DR:** OpenCode only worked inside WSL; fixed Windows access with a wrapper, researched the MCP ecosystem for electronics, installed the `oh-my-embedded` plugin plus the `kicad-mcp` server, and verified 4 MCP servers connecting from OpenCode. Two Rust-based servers (GDB, serial) are pending.

---

## 1. Fixing CLI access from Windows

OpenCode was installed with the official script inside WSL (`~/.opencode/bin/opencode`, v1.18.11) and worked fine there — but Windows had nothing: no native install, no `opencode` in the Windows `PATH`.

Fix: a tiny wrapper in a directory that was **already** on the Windows user `PATH`:

```cmd
:: C:\Users\marti\.local\bin\opencode.cmd
@echo off
wsl.exe -e /home/martinf/.opencode/bin/opencode %*
```

Notes:
- `wsl.exe -e opencode` alone does **not** work: non-interactive WSL invocations don't load the Bash `PATH` (`~/.opencode/bin` is missing). The absolute path is required.
- Verified from both PowerShell and CMD: `opencode --version` → `1.18.11`.
- Full guide: [../docs/01-opencode-on-windows-wsl.md](../docs/01-opencode-on-windows-wsl.md)

## 2. Ecosystem research: is there a "Context7 for electronics"?

Short answer: not one thing, but a growing constellation. Verified on GitHub today:

| Project | ~Stars | What it does |
|---|---|---|
| `lamaalrajih/kicad-mcp` | 492 | KiCad MCP: projects, netlist, BOM, DRC via kicad-cli, circuit pattern recognition |
| `oaslananka/kicad-mcp-pro` | 42 | ERC/DRC, DFM, manufacturing review |
| `oaslananka/easyeda-mcp-pro` | 26 | EasyEDA Pro + BOM sourcing (DigiKey/Mouser/LCSC/JLCPCB) |
| `ByteAsk/ByteAsk-Embedded-MCP` | 23 | Embedded docs retrieval with page-level citations (ARM, MISRA, reference manuals) |
| `es617/serial-mcp-server` | 13 | Serial port as an MCP tool |
| `captainluzik/oh-my-embedded` | 19 | OpenCode plugin: agents, skills, calc tools, MCP integrations |
| `charlesmmorais/coppermind` | 0 | KiCad copilot with a citable IPC-2221 design-rules engine |

Also: **Context7 itself** indexes ESP-IDF, FreeRTOS, Zephyr, PlatformIO and Arduino docs — it's not web-software-only.

## 3. Installed `oh-my-embedded`

Prerequisite: Bun (OpenCode plugins run on it) → installed to `~/.bun`.

```bash
bunx oh-my-embedded install --no-tui
```

Result:
- 3 agents: `@embedded`, `@hardware`, `@review-hw`
- 6 skills: embedded-engineer, embedded-review, pcb-designer, component-sourcer, firmware-debugger, circuit-simulator
- 5 commands: `/flash`, `/debug`, `/bom`, `/power-budget`, `/review-firmware`
- 5 always-on calculation tools (power budget, RF impedance, resistor divider, ESP32 pin mapper, decoupling advisor)
- MCP dependencies auto-installed: `esp-mcp`, `kicad-mcp-server`, `spicebridge`, `jlc-cli` (JLCPCB)
- **Skipped:** `mcp-server-gdb` and `serial-mcp-server` (need Rust/cargo)

Full guide: [../docs/02-oh-my-embedded.md](../docs/02-oh-my-embedded.md)

## 4. Installed `kicad-mcp` (lamaalrajih) as a global MCP server

The plugin's own KiCad server only runs inside its `pcb-designer` skill; I wanted KiCad analysis available to **every** agent, so the more mature `kicad-mcp` was installed separately:

```bash
git clone --depth 1 https://github.com/lamaalrajih/kicad-mcp.git ~/opt/kicad-mcp
cd ~/opt/kicad-mcp && make install   # uses uv, creates .venv
```

Registered in `~/.config/opencode/opencode.jsonc` (see [../config/opencode.jsonc](../config/opencode.jsonc)) with `KICAD_SEARCH_PATHS` pointing at the active project repo and Windows document folders.

Handshake test (stdio, JSON-RPC `initialize` + `tools/list`) passed — tools exposed include `list_projects`, `get_project_structure`, netlist extraction, BOM, DRC, thumbnails, pattern recognition.

**Limitation found:** KiCad lives on the Windows side only (`C:\Program Files\KiCad\10.0`). File-parsing tools work fine in WSL; DRC and thumbnails need `kicad-cli` inside WSL → pending (`sudo apt install kicad`).

Full guide: [../docs/03-kicad-mcp.md](../docs/03-kicad-mcp.md)

## 5. Verification

```
$ opencode mcp list
●  ✓ kicad          connected
●  ✓ esp-mcp        connected
●  ✓ jlcpcb-mcp     connected
●  ✓ spicebridge    connected
└  4 server(s)
```

`opencode debug config` shows the merged configuration resolving correctly (plugin + all MCP entries).

## 6. Pending / next

- [ ] Install Rust → `cargo install mcp-server-gdb --locked serial-mcp-server --locked` (Phase 5, hardware-in-the-loop)
- [ ] Install KiCad in WSL → unlock DRC/thumbnails in kicad-mcp
- [ ] First real end-to-end test: `/bom` on the Jig-Station HDMI board
- [ ] Validate spicebridge on a real power-supply simulation
- [ ] Start Phase 6 research: CAD MCP options (FreeCAD first, then Fusion 360 / SolidWorks)

## Environment snapshot

- Windows 11 + WSL2 (Ubuntu 24.04), OpenCode 1.18.11
- Bun `~/.bun`, uv `~/.local/bin`, Node 24, Python 3.12
- KiCad 10.0 (Windows), PlatformIO 6.x (WSL)
