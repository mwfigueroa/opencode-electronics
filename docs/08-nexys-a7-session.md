# Nexys A7 + ADP2230 — Sesión 5-6 Agosto 2026

## Logros

### Nexys A7
- ✅ JTAG detectada (XC7A100T, IDCODE 0x03631093)
- ✅ Toolchain FPGA (10 herramientas WSL)
- ✅ Vivado 2026.1 + licencia Basic Tier
- ✅ LED blinker + UART (TX ✅, RX ❌)
- ✅ Contador frecuencia calibrado 0.13% vs TBS
- ✅ Flash QSPI programada (persistente)

### Cross-Instrument
- ✅ Triple: ADP2230 → TBS1102C + Nexys A7
- ✅ Barrido ADP2230 → TBS verificado
- 🔧 `awg_sweep` arreglado (configure(False) en vez de True)

### MCP Server
- ✅ `awg_sweep` agregado (log/lineal, multiciclo, variable dwell)
- 🔧 Bug fix: `configure(ch, False)` aplica frecuencia sin reiniciar AWG
- ⚠️ Sweeps largos necesitan async

---

## Barrido Rápido (post-reinicio)

```
> "barrido 100Hz a 500kHz, 10 puntos, cuadrado 3.3Vpp"
```

---

## Comandos

```bash
# Síntesis
P:\AMDDesignTools\2026.1\Vivado\bin\vivado -mode batch -source P:\NexysA7\scripts\build.tcl

# Flash
wsl openFPGALoader -b nexys_a7_100 -f --unprotect-flash /mnt/p/NexysA7/bitstreams/top.bit

# UART
wsl python3 -c "import serial; s=serial.Serial('/dev/ttyUSB1',115200,timeout=4); print(s.read(200).decode())"
```
