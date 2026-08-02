# 01 — OpenCode on Windows via WSL

OpenCode works best inside WSL, but you usually want to launch it from PowerShell, CMD, or Windows Terminal too. This guide sets up both.

## 1. Install inside WSL

```bash
curl -fsSL https://opencode.ai/install | bash
```

The binary lands in `~/.opencode/bin/opencode` and the installer adds that directory to your Bash `PATH`. Verify:

```bash
opencode --version
```

## 2. Make it callable from Windows

The problem: Windows knows nothing about the WSL binary, and `wsl.exe -e opencode ...` fails because non-interactive WSL sessions don't source `.bashrc` — so `~/.opencode/bin` is not on the `PATH` inside that invocation.

The fix is a wrapper that calls the binary by **absolute path**, placed in any directory already on the Windows user `PATH` (here `C:\Users\<you>\.local\bin`):

```cmd
:: C:\Users\<you>\.local\bin\opencode.cmd
@echo off
wsl.exe -e /home/<wsl-user>/.opencode/bin/opencode %*
```

Open a **new** PowerShell/CMD window and verify:

```powershell
opencode --version
```

All arguments (`%*`) are forwarded, so `opencode web`, `opencode serve`, etc. work too.

## 3. Optional: expose OpenCode servers to Windows

If you run a server in WSL and want to reach it from Windows browsers/apps:

```bash
# Web UI
opencode web --hostname 0.0.0.0

# API server for the desktop app (protect it!)
OPENCODE_SERVER_PASSWORD=your-password opencode serve --hostname 0.0.0.0 --port 4096
```

Access from Windows at `http://localhost:<port>` (WSL2 mirrored networking makes localhost work; otherwise use the WSL IP from `hostname -I`).

## 4. Config locations (WSL side)

| What | Path |
|---|---|
| Global config | `~/.config/opencode/opencode.json` / `.jsonc` |
| Agents | `~/.config/opencode/agents/` |
| Skills | `~/.config/opencode/skills/` |
| Commands | `~/.config/opencode/commands/` |
| Sessions/data | `~/.local/share/opencode/` |

Config is loaded at startup — **restart OpenCode after any config change**.

Useful debug commands:

```bash
opencode debug config   # show resolved (merged) configuration
opencode debug skill    # list all discovered skills
opencode mcp list       # list MCP servers and connection status
```
