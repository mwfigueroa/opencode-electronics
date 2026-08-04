# 2026-08-04 — MCXA153 physical test + platformio-mcp deployed

## What changed

Completed the **Phase 5b hardware-in-the-loop test** on a real NXP FRDM-MCXA153 board. This closes the loop: flash firmware from the agent, verify serial output, and confirm debug probe connectivity — all through the MCP toolchain.

## Hardware

- **Board:** NXP FRDM-MCXA153 (Cortex-M33 r1p0, v8.0-M)
- **Debug probe:** Onboard MCU-LINK CMSIS-DAP V3.128 (VID:PID 1fc9:0143)
- **Test firmware:** `mcxa153_app` — RGB LED blinky (VERDE → AZUL → ROJO, 70ms) with SW2 speed toggle (600ms / 70ms / 100ms) and UART debug output
- **Firmware source:** `P:\NXP_Test\projects\mcxa153_app\src\main.c` — non-blocking SysTick, debounced button ISR, conditional `APP_LOG` via `PRINTF`

## PlatformIO MCP bridge deployment

The `platformio-mcp` bridge was deployed on the **laboratorio** machine:

| Item | Detail |
|---|---|
| Location | `/home/laboratorio/opt/platformio-mcp/` |
| Stack | Python 3.11, `mcp==1.5.0`, `uv`-managed venv |
| Tools | 15: init, run, upload, clean, device_list, device_monitor, boards, test, check, lib_install, lib_list, lib_search, debug_start, update, system_info |
| Config | Registered in `~/.config/opencode/opencode.jsonc` |

### Verification

```
pio_system_info  → PlatformIO Core 6.1.19, Python 3.12.3, Linux WSL2
pio_boards stm32 → BluePill F103C8, BlackPill F103C8, Maple, etc.
pio_boards lpc   → LPC1768 (mbed), Seeed Arch Pro
pio_boards nxp   → i.MX RT1010-1064 EVK, LPC1768
```

## arm-none-eabi-gdb

- `gdb-multiarch` 15.1 installed via apt (`gdb-arm-none-eabi`)
- Symlinked: `~/.local/bin/arm-none-eabi-gdb → /usr/bin/gdb-multiarch`

## Physical test: FRDM-MCXA153

### Connection flow

```
Windows (MCU-LINK USB)
  └─ usbipd bind → attach → WSL2 (/dev/ttyACM0 + CMSIS-DAP)
```

### Flash

```powershell
# Detach from WSL, flash from Windows (pyocd via embedded Python)
usbipd detach --busid 5-4

$env:NXP_ROOT = "P:\NXP_Test"
$env:PATH = "$env:NXP_ROOT\tools\python\Scripts;$env:PATH"
$env:PYTHONIOENCODING = "utf-8"
pyocd flash --target mcxa153vlh "mcxa153_app.hex"
# → 15616 bytes programmed at 17.36 kB/s
```

Key detail: the generic `cortex_m` target failed with "Memory transfer fault". The fix was installing the CMSIS pack `NXP.MCXA153_DFP.26.06.00` via `pyocd pack install mcxa153` and using `--target mcxa153vlh`.

### Serial verify

```
MCUX SDK version: 2026.06.00
mcxa153_app: blinky LED RGB no bloqueante iniciado.
Boton SW2: cambia velocidad (lento -> normal -> rapido).

LED: VERDE [70 ms]
LED: AZUL [70 ms]
LED: ROJO [70 ms]
...
```

### Debug (PyOCD via WSL)

```
$ pyocd cmd -t cortex_m
> halt
Successfully halted device

> reg
PC:  0x00002c54   SP: 0x20005fd8   LR: 0x00002cbf
XPSR: 0x29000000 (Thumb state, normal execution)
```

## New custom skills

Created two MCU-family-specific skills (copied to both WSL and Windows sides):

| Skill | Covers |
|---|---|
| `stm32-engineer` | STM32F0/F1/F4/G0/G4/H7/U5, HAL/LL, DMA, NVIC, ST-Link, PlatformIO templates |
| `nxp-engineer` | LPC17xx (PINSEL/PCONP), i.MX RT (FlexSPI/TCM/CCM), Kinetis, CMSIS-DAP, PlatformIO templates |

## What this validates

The full toolchain works end-to-end on a physical non-ESP32 target:

1. **PlatformIO detects boards** across STM32, NXP LPC, NXP i.MX RT
2. **arm-none-eabi-gdb** connects and halts a real Cortex-M33
3. **PyOCD flashes** with the correct Device Family Pack
4. **Serial monitor** captures debug output (via both `cat` and `serial-mcp-server`)
5. **usbipd** reliably forwards USB between Windows host and WSL

## Remaining Phase 5b items

- [ ] Test STM32F103 Blue Pill (physical flash + debug)
- [ ] Test NXP LPC1768 or i.MX RT1010 (physical flash + debug)
- [ ] Verify `mcp-server-gdb` integration with `arm-none-eabi-gdb` + OpenOCD on physical target
- [ ] Add MCXA153 board definition to PlatformIO (upstream contribution candidate)

## Repo changes

- `journal/2026-08-04-mcxa153-physical-test.md` — this file
- `ROADMAP.md` — Phase 5b items updated
- `skills/stm32-engineer/SKILL.md` — new
- `skills/nxp-engineer/SKILL.md` — new
- `platformio-mcp/` — bridge source (15 tools)
