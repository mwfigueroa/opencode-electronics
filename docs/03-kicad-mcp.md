# 03 — kicad-mcp (global KiCad MCP server)

[lamaalrajih/kicad-mcp](https://github.com/lamaalrajih/kicad-mcp) is the most mature KiCad MCP server (~490★ at time of writing). Installed globally, every OpenCode agent can analyze KiCad projects — not just a PCB-specific skill.

Features: project discovery, project structure analysis, netlist extraction, BOM management, DRC via `kicad-cli`, PCB thumbnails, circuit pattern recognition (detects buck/boost/LDO topologies etc.).

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh` → `~/.local/bin`)
- KiCad 9+ *(optional but recommended — see "Without a KiCad binary" below)*

## Install

```bash
git clone --depth 1 https://github.com/lamaalrajih/kicad-mcp.git ~/opt/kicad-mcp
cd ~/opt/kicad-mcp
make install        # uv creates .venv and installs dependencies
```

## Register in OpenCode

Add to `~/.config/opencode/opencode.jsonc` (or `opencode.json`):

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "kicad": {
      "type": "local",
      "command": [
        "/home/<you>/opt/kicad-mcp/.venv/bin/python",
        "/home/<you>/opt/kicad-mcp/main.py"
      ],
      "enabled": true,
      "environment": {
        // comma-separated directories scanned for .kicad_pro files
        "KICAD_SEARCH_PATHS": "/home/<you>/projects,/mnt/c/Users/<you>/Documents"
      }
    }
  }
}
```

Restart OpenCode, then verify:

```bash
opencode mcp list     # → ● ✓ kicad connected
```

## Smoke-test the server standalone (optional)

MCP servers speak JSON-RPC over stdio. This sends `initialize` + `tools/list`:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | timeout 25 ~/opt/kicad-mcp/.venv/bin/python ~/opt/kicad-mcp/main.py
```

You should see the FastMCP banner followed by JSON responses listing tools (`list_projects`, `get_project_structure`, …).

## Without a KiCad binary (e.g. KiCad only on Windows)

The server starts fine, but its tools split in two groups:

| Works (pure file parsing) | Needs KiCad installed locally |
|---|---|
| `list_projects`, `get_project_structure` | DRC checks (`kicad-cli`) |
| Netlist extraction / analysis | PCB thumbnails/renders |
| BOM analysis & export | `open_project` (launches the GUI) |
| Circuit pattern recognition | |

In WSL, install KiCad to unlock everything:

```bash
sudo apt update && sudo apt install -y kicad
```

## Updating

```bash
cd ~/opt/kicad-mcp && git pull && make install
```
