# 2026-08-02 (third entry) — Circuit lab core layer: design, simulation, analysis

**TL;DR:** Installed the full circuit development & analysis layer: KiCad 10 in WSL (version-matched to Windows via PPA), ngspice, OpenOCD, sigrok-cli, and a Python analysis stack (lcapy / scikit-rf / control). Fixed a missing-dependency bug that was silently killing the plugin's KiCad server. **7/7 MCP servers now connect.**

---

## 1. System packages (apt)

```bash
sudo apt install -y --no-install-recommends kicad ngspice libngspice0 openocd sigrok-cli
```

- **KiCad 7.0.11** came from the Ubuntu repos — too old: it cannot open files saved by the Windows KiCad **10.0**, so DRC on real projects would fail. Fixed with the official PPA:
  ```bash
  sudo add-apt-repository -y ppa:kicad/kicad-10.0-releases
  sudo apt update && sudo apt install -y --no-install-recommends kicad
  # → kicad-cli 10.0.5, matches the Windows install
  ```
  **Lesson:** always version-match the WSL KiCad to the desktop KiCad; file formats are not backwards compatible.
- `pcbnew.py` now exists at `/usr/lib/python3/dist-packages/pcbnew.py` → the oh-my-embedded plugin detects it and registers its own `kicad-mcp` server at startup.
- **openocd 0.12.0** (JTAG/SWD backend for the GDB server) and **sigrok-cli 0.7.2** (logic analyzers + SCPI instruments over TCP/serial/USBTMC) installed cleanly.

## 2. Real DRC test (end-to-end proof)

```bash
kicad-cli pcb drc --format report ".../KiCad/10.0/projects/test/test.kicad_pcb"
# Found 1 violations / 0 unconnected → report saved
```

This is the same engine the `kicad` MCP server calls, so agent-driven DRC now works on real KiCad 10 projects.

## 3. Python analysis stack

```bash
pip install --break-system-packages lcapy scikit-rf control
```

**The numpy trap (worth documenting):** Ubuntu's Debian-patched numpy 1.26.4 does not expose `np.typing` as an attribute the way upstream wheels do, and scikit-rf imports `np.typing.NDArray` at module load → `AttributeError`. pip initially refused to help ("requirement already satisfied" by the apt package). Resolution: install a modern scientific trio into user-site, which shadows the apt versions:

```bash
pip install --user --break-system-packages -U "numpy>=2" "scipy>=1.14" "matplotlib>=3.9"
# numpy 2.5.1 · scipy 1.18.0 · matplotlib 3.11.1 · lcapy 1.26 · scikit-rf 2.0.1 · control 0.10.2
```

Known cosmetic issue: matplotlib warns about Axes3D because both apt and pip builds coexist; 2D plotting is unaffected.

Verified working: symbolic transfer functions (lcapy), S-parameter networks (scikit-rf), control system models (control), plus ngspice batch simulation (`ngspice -b rc_test.cir`).

## 4. Bug hunt: plugin's `kicad-mcp` server timing out

After KiCad landed, the plugin registered its `kicad-mcp` server — but it failed with a 30s timeout. Trace:

1. Standalone run of the node server: registers all tools, then hangs at `Starting Python proc`.
2. Running its Python backend (`python/kicad_interface.py`) directly: **`ModuleNotFoundError: sexpdata`** — the process died instantly and the wrapper waited forever.
3. Root cause: the oh-my-embedded installer installed the node server but not its Python requirements.
4. Fix:
   ```bash
   pip install --user --break-system-packages -r ~/.local/share/oh-my-embedded/kicad-mcp-server/requirements.txt
   ```
   Backend now prints `{"type": "ready"}` and the server connects.

(Worth upstreaming: the installer should either install these Python deps or the server should fail loudly instead of hanging.)

## 5. Final state

```
$ opencode mcp list
●  ✓ kicad              connected   (lamaalrajih, global — analysis, DRC via kicad-cli)
●  ✓ esp-mcp            connected
●  ✓ kicad-mcp          connected   (plugin's — board edit, UI sync, exports)  ← woke up today
●  ✓ jlcpcb-mcp         connected
●  ✓ spicebridge        connected   (now with a real ngspice engine behind it)
●  ✓ mcp-server-gdb     connected   (now with openocd available as backend)
●  ✓ serial-mcp-server  connected
└  7 server(s)
```

## 6. Lab capability map (what any agent can do now)

| Capability | Engine | Entry point |
|---|---|---|
| Schematic/PCB analysis, BOM, patterns | kicad-mcp (global) | MCP tools |
| DRC/ERC on real KiCad 10 projects | kicad-cli 10.0.5 | MCP tools / bash |
| Board editing, exports, UI sync | plugin's kicad-mcp | pcb-designer skill |
| SPICE simulation | ngspice 42? (apt) via spicebridge | circuit-simulator skill / spice-sim skill |
| Symbolic circuit analysis | lcapy | bash python3 |
| RF / S-parameters | scikit-rf | bash python3 |
| Control systems (Bode, margins) | control | bash python3 |
| Component sourcing | jlcpcb-mcp | component-sourcer skill |
| JTAG/SWD debug | openocd + mcp-server-gdb | firmware-debugger skill |
| Serial monitor | serial-mcp-server | firmware-debugger skill |
| Logic analyzers / SCPI instruments | sigrok-cli | bash |

## 7. Pending

- [ ] First real board analysis through the agent: `/bom` + DRC on `asac-fc-rev-a` (found in OneDrive) or the Jig-Station HDMI board.
- [ ] Real HIL test on ESP32 (usbipd attach + ESP-IDF gdb in WSL).
- [ ] Remove apt's `python3-matplotlib` if the Axes3D warning becomes annoying.
- [ ] Upstream the kicad-mcp-server Python-deps issue to oh-my-embedded.
- [ ] Phase 6 research: mechanical CAD (FreeCAD → Fusion 360 → SolidWorks).
