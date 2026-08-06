# Nexys A7 + ADP2230 — Sesión 5-6 Agosto 2026

## Logros

### Día 1 (5-Ago)
- ✅ Nexys A7 detectada (JTAG: XC7A100T, IDCODE 0x03631093)
- ✅ Toolchain FPGA instalado (10 herramientas en WSL)
- ✅ Vivado 2026.1 instalado y licenciado (Basic Tier, P:\AMDDesignTools\)
- ✅ LED blinker + UART echo sintetizado (0 errores)
- ✅ Bitstream generado (3.65 MB) y programado vía JTAG
- ✅ LED[0] parpadeando confirmado

### Día 2 (6-Ago)
- ✅ Pines UART C4/D4 verificados contra XDC oficial
- ✅ UART TX funcionando (beacon + contador de frecuencia)
- ❌ UART RX no funciona (problema hardware FTDI→pin C4)
- ✅ Loopback interno confirma código Verilog correcto
- ✅ Programación QSPI flash (diseño persiste entre power cycles)
- ✅ **Triple cross-instrument**: ADP2230 → TBS1102C + Nexys A7
- ✅ Contador de frecuencia calibrado (error 0.13% vs TBS)
- ✅ Barrido de frecuencia ADP2230 → TBS verificado
- ✅ Nueva herramienta `awg_sweep` agregada al MCP server

---

## Cross-Instrument Final

```
ADP2230 AWG (W1) ──► Nexys A7 Pmod JD[1] (H4) ──► Frecuencímetro
     │                      │
     │                      └──► UART 115200 → "010000"
     │
     └──────────────────► TBS1102C CH1 ──► "10.013 kHz"
```

| Instrumento | Frecuencia | Vpp |
|---|---|---|
| ADP2230 (set) | 10 000 Hz | 3.3V |
| TBS1102C (ref) | 10 013 Hz | 3.36V |
| Nexys A7 | **10 000 Hz** | — |

**Error: 0.13%** — calibración exitosa.

---

## Nexys A7 — Estado Final

| Función | Estado |
|---|---|
| LED blinker | ✅ LED[0] ~0.75 Hz |
| UART TX | ✅ 115200 baud |
| UART RX | ❌ HW: FTDI→C4 sin señal |
| Frecuencímetro | ✅ Calibrado, 0.13% error |
| Display 7-seg | ✅ Muestra kHz |
| Flash QSPI | ✅ Diseño persistente |
| Vivado 2026.1 | ✅ Licencia Basic Tier |
| JTAG | ✅ OpenFPGALoader |

---

## Lecciones Aprendidas

1. **ADP2230 `amplitude_vpp`** = pico (no pico a pico). amp=1.65 = 3.3Vpp real
2. **NUNCA 5V en LVCMOS33**: Vmax seguro = 3.45V
3. **JTAG interfiere con FTDI UART**: programar flash + power cycle
4. **El MCP `awg_generate` resetea parámetros no especificados**: siempre pasar TODOS
5. **Contador necesitó calibración**: gate 93.2M ciclos + corrección ×1073/1000
6. **`awg_sweep`** agregado al MCP server: barridos automatizados sin reset

---

## Comandos Rápidos

```bash
# Sintetizar
P:\AMDDesignTools\2026.1\Vivado\bin\vivado -mode batch -source P:\NexysA7\scripts\build.tcl

# Programar SRAM (rápido, se pierde al apagar)
wsl openFPGALoader -b nexys_a7_100 /mnt/p/NexysA7/bitstreams/top.bit

# Programar FLASH (persistente)
wsl openFPGALoader -b nexys_a7_100 -f --unprotect-flash /mnt/p/NexysA7/bitstreams/top.bit

# Leer UART
wsl python3 -c "import serial; s=serial.Serial('/dev/ttyUSB1',115200,timeout=4); print(s.read(200).decode())"

# Barrido con ADP2230
# > "hace un barrido de 50 Hz a 500 kHz, 13 puntos, 10 ciclos"
```

---

## Pendientes

- [ ] Debuggear UART RX (requiere acceso al pin C4 o chip FTDI)
- [ ] Probar `awg_sweep` post-reinicio de OpenCode
- [ ] Testbench cocotb para el UART
- [ ] Explorar LiteX para SoC RISC-V
- [ ] Barrido ADP2230+Nexys (cuando UART RX funcione)
