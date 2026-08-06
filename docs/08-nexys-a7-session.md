# Nexys A7 + ADP2230 — Sesión 5-6 Agosto 2026

## Estado Final

### Nexys A7
- ✅ JTAG: XC7A100T, Flash QSPI programada
- ✅ Frecuencímetro calibrado 0.13% vs TBS
- ✅ UART TX 115200, Display 7-seg
- ❌ UART RX (hardware FTDI→C4)

### ADP2230
- ✅ AWG + Scope + Logic Analyzer
- ✅ `awg_sweep`: barridos log/lineal, multiciclo, variable dwell
- ✅ Sweep verificado con TBS (100 Hz → 500 kHz)
- 🔧 Fix final: `configure(True)` en loop + mantener salida al final

### Cross-Instrument
- ✅ Triple: ADP2230 + TBS1102C + Nexys A7 (0.13% error)
- ✅ Barrido de frecuencia verificado

---

## Comandos

```bash
# Síntesis Nexys
P:\AMDDesignTools\2026.1\Vivado\bin\vivado -mode batch -source P:\NexysA7\scripts\build.tcl

# Flash
wsl openFPGALoader -b nexys_a7_100 -f --unprotect-flash /mnt/p/NexysA7/bitstreams/top.bit

# UART
wsl python3 -c "import serial; s=serial.Serial('/dev/ttyUSB1',115200,timeout=4); print(s.read(200).decode())"

# Sweep ADP2230
# > "barrido 100Hz a 500kHz, 10 puntos, cuadrado 3.3Vpp, 0.6s"
```
