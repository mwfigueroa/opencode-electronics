# 2026-08-02 (second entry) — Hardware-in-the-loop: GDB + serial MCP servers

**TL;DR:** Installed the Rust toolchain, built `mcp-server-gdb` and `serial-mcp-server` from crates.io, fixed a PATH visibility issue with symlinks, and now **6 MCP servers connect from OpenCode**. Phase 5 tooling is complete; testing against a real target is next.

---

## 1. Rust toolchain

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable --profile minimal
# → rustc 1.97.1, cargo in ~/.cargo/bin (added to PATH via ~/.bashrc and ~/.profile)
```

## 2. mcp-server-gdb ✅

```bash
cargo install mcp-server-gdb --locked
# → v0.2.3 (also installs gdb_client and test_app)
```

Tools exposed: create/delete GDB sessions, breakpoints, stack frames, registers, memory ops, remote debugging (with baud rate for serial remote targets).

**Gotcha found:** the server creates its log directory **relative to the current working directory**. Launched from a non-writable CWD (e.g. `/`) it panics with `PermissionDenied`. In practice OpenCode launches MCP servers with the project directory as CWD, so it's fine — but don't smoke-test it from `/`.

## 3. serial-mcp-server ✅ (after fixing a system dependency)

```bash
cargo install serial-mcp-server --locked
# FAILED: crate libudev-sys needs the system library libudev
```

Fix (requires sudo):

```bash
sudo apt update && sudo apt install -y pkg-config libudev-dev
cargo install serial-mcp-server --locked
# → v0.1.0
```

Tools exposed: `list_ports`, open/close connections, `write`, read with configurable encoding.

## 4. PATH gotcha: plugin detection vs. how OpenCode is launched

The oh-my-embedded plugin registers the GDB/serial servers at startup **only if `which` finds them on the PATH** (`commandExistsSync` in its config hook). Cargo puts them in `~/.cargo/bin`, which is only on the PATH of login/interactive shells — so OpenCode launched from the Windows wrapper (`wsl.exe -e ...`, non-interactive) would never see them.

Fix: symlinks into `~/.local/bin`, which is on the default PATH everywhere (including non-interactive WSL sessions):

```bash
ln -sf ~/.cargo/bin/mcp-server-gdb   ~/.local/bin/
ln -sf ~/.cargo/bin/serial-mcp-server ~/.local/bin/
```

Verified with a scrubbed environment (`env -i` + minimal PATH): both resolve.

## 5. Verification — all 6 servers connected

```
$ opencode mcp list
●  ✓ kicad              connected
●  ✓ esp-mcp            connected
●  ✓ jlcpcb-mcp         connected
●  ✓ spicebridge        connected
●  ✓ mcp-server-gdb     connected
●  ✓ serial-mcp-server  connected
└  6 server(s)
```

## 6. Side discoveries (useful)

- The plugin registers `kicad-mcp` (its own KiCad server) only if it finds KiCad's Python (`pcbnew.py`) on Linux paths — currently skipped because KiCad lives on Windows. Installing KiCad in WSL unlocks both this and the DRC tools in `kicad-mcp`. One `apt install kicad`, two wins.
- Skill-scoped `mcpConfig` (inside SKILL.md frontmatter) is **not** merged into the global config at startup; the plugin's runtime hook is what registers servers globally.

## 7. Pending

- [ ] **Real-target test**: ESP32 (Jig-Station firmware) via OpenOCD/JTAG + serial monitor through the new servers.
- [ ] USB serial devices in WSL need `usbipd-win` attach from Windows (`usbipd bind` + `usbipd attach --wsl`) before `/dev/ttyUSB*` exists.
- [ ] GDB for ESP32 needs `xtensa-esp32-elf-gdb` (ships with ESP-IDF) — ESP-IDF is not yet installed in WSL.
- [ ] Still pending from entry #1: KiCad in WSL, `/bom` on the HDMI board, spicebridge end-to-end test.
