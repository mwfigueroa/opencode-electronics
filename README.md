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
| Circuit simulation | `spicebridge` (ngspice via MCP) + custom `spice-sim` skill | ✅ Connected |
| PCB design | [kicad-mcp](https://github.com/lamaalrajih/kicad-mcp) + `kicad-mcp-server` | 🟡 File analysis works; DRC needs KiCad installed in WSL |
| Hardware-in-the-loop | `mcp-server-gdb`, `serial-mcp-server` | ⬜ Pending (requires Rust toolchain) |
| Mechanical CAD | SolidWorks / Fusion 360 integration | ⬜ Research phase |

## Repository layout

```
├── README.md            ← you are here
├── ROADMAP.md           ← phased plan: firmware → PCB → simulation → HIL → mechanical CAD
├── journal/             ← dated log entries: what was done, verified, and learned
├── docs/                ← reproducible setup guides
├── config/              ← sanitized opencode config examples
└── backlog/             ← MCP servers and ideas being watched / evaluated
```

## Start reading

- [ROADMAP.md](ROADMAP.md) — the plan, phase by phase
- [journal/2026-08-02-initial-setup.md](journal/2026-08-02-initial-setup.md) — day one: from broken CLI to 4 MCP servers connected
- [docs/](docs/) — setup guides if you want to replicate this

## Notes

- Commands and versions are verified on the date of each journal entry. This ecosystem moves fast — expect drift.
- Environment: Windows 11 + WSL2 (Ubuntu 24.04), KiCad on the Windows side, PlatformIO/ESP-IDF for firmware.
- Contributions, suggestions and pointers to MCP servers I missed are welcome via issues.

## License

[MIT](LICENSE)
