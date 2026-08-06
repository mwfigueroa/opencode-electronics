# Nexys A7 + ADP2230 — Sesión 5-6 Agosto 2026

## Logros Completos

### Día 1 (5-Ago)
- ✅ Nexys A7 detectada (JTAG: XC7A100T, IDCODE 0x03631093)
- ✅ Toolchain FPGA (10 herramientas WSL)
- ✅ Vivado 2026.1 + licencia Basic Tier
- ✅ LED blinker + UART echo sintetizado (0 errores)
- ✅ Bitstream 3.65 MB generado y programado
- ✅ LED[0] parpadeando confirmado

### Día 2 (6-Ago)
- ✅ Pines UART C4/D4 verificados contra XDC oficial
- ✅ UART TX: beacon + contador frecuencia
- ❌ UART RX: hardware FTDI→C4 (loopback interno OK)
- ✅ Flash QSPI programada (diseño persistente)
- ✅ **Triple cross-instrument**: ADP2230 → TBS1102C + Nexys A7
- ✅ Contador calibrado 0.13% vs TBS
- ✅ **`awg_sweep`**: barridos automatizados de frecuencia
- ✅ Tiempo variable de dwell (0.5s→3s) agregado al MCP

---

## awg_sweep — Nueva Herramienta MCP

### Funcionalidades
| Feature | Estado |
|---|---|
| Barrido log/lineal | ✅ |
| Múltiples ciclos | ✅ |
| Tiempo fijo por paso | ✅ |
| Tiempo variable (0.5s→3s) | ✅ (código listo, requiere reinicio) |
| Waveform configurable | ✅ |
| No resetea parámetros | ✅ |

### Uso
```
> "barrido de 100 Hz a 1 MHz, 20 puntos, 5 ciclos, senoidal 2Vpp"
> "sweep cuadrado 50Hz a 500kHz, 13 puntos, 10 ciclos, 0.5s a 3s"
```

### Pendiente
- Sweeps largos (>30s) bloquean MCP → necesita async

---

## Cross-Instrument Final

```
ADP2230 AWG ──► Nexys A7 (H4) ──► Contador + UART
     │
     └────────► TBS1102C CH1 ──► Medición automática
```

| Instr. | Rol | Freq | Error |
|---|---|---|---|
| ADP2230 | Genera | 10 kHz | — |
| TBS1102C | Ref | 10.013 kHz | — |
| Nexys A7 | Mide | **10.000 kHz** | **0.13%** |

---

## Lecciones

1. ADP2230 `amplitude_vpp` = pico (no pico a pico)
2. NUNCA 5V en LVCMOS33 (max 3.45V)
3. JTAG interfiere con FTDI UART → flash + power cycle
4. MCP `awg_generate` resetea params → usar `awg_sweep`
5. Contador: gate 93.2M ciclos + corrección ×1073/1000
6. Sweeps largos necesitan async en MCP server

---

## Comandos Rápidos

```bash
# Síntesis
P:\AMDDesignTools\2026.1\Vivado\bin\vivado -mode batch -source P:\NexysA7\scripts\build.tcl

# Programar FLASH
wsl openFPGALoader -b nexys_a7_100 -f --unprotect-flash /mnt/p/NexysA7/bitstreams/top.bit

# Leer UART
wsl python3 -c "import serial; s=serial.Serial('/dev/ttyUSB1',115200,timeout=4); print(s.read(200).decode())"

# Barrido (desde OpenCode)
# > "barrido de 100 Hz a 1 MHz, 20 puntos, 5 ciclos, senoidal 2Vpp"
```
