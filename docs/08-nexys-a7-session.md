# Nexys A7 — Sesiones Ago 2026

## Estado Final (7-Ago)

### Nexys A7 — FPGA
- ✅ JTAG: XC7A100T detectado (IDCODE 0x03631093)
- ✅ **NEORV32 RV32IMC @ 100 MHz** — bootloader 115200, sys_test ALL PASSED
- ✅ **QSPI flash**: boot persistente (jumper QSPI → power-cycle → bootloader OK)
- ✅ Frecuencímetro calibrado 0.13%
- ✅ UART TX 115200, Display 7-seg
- ❌ UART RX (hardware FTDI→C4)

### ADP2230
- ✅ AWG + Scope + Logic Analyzer
- ✅ Barrido con `awg_generate` individual
- ⚠️ `awg_sweep`: pydwf `configure(True)` no re-aplica frecuencia on-the-fly

### Cross-Instrument
- ✅ Triple: ADP2230 + TBS1102C + Nexys A7 (0.13%)

---

## Lecciones acumuladas

### Hardware
1. ADP2230 `amplitude_vpp` = pico, no pico a pico
2. NUNCA 5V en LVCMOS33 (Vih_max = 3.45V)
3. JTAG interfiere FTDI UART → programar flash + power cycle
4. FTDI necesita detach/reattach post-JTAG para UART fiable

### NEORV32 Toolchain
5. `riscv64-unknown-elf-gcc` + picolibc **no soporta rv32e** → compilar con `rv32i/ilp32`
6. `--specs=picolibc.specs` **rompe el crt0** del bootloader → usar `-nostartfiles -nodefaultlibs`
7. Upload UART: enviar `u` **sin `\r`** (el CR corrompe el header binario)
8. Baud rate debe coincidir entre **bootloader y aplicación** (ambos a 115200)

### QSPI Flash
9. Vivado 2026.1 `program_hw_cfgmem` **se cuelga** con S25FL128S → usar `openFPGALoader --unprotect-flash`
10. Después de erase parcial con Vivado, la flash queda **protegida** (block protection)

---

## Comandos rápidos

```bash
# === NEORV32 ===

# Terminal bootloader (WSL)
picocom -b 115200 /dev/ttyUSB1

# Programar QSPI flash (NEORV32)
openFPGALoader -b nexys_a7_100 -f --unprotect-flash --verify /mnt/p/NexysA7/neorv32/top.bit

# Recargar FPGA por JTAG (si se bloqueó)
openFPGALoader -b nexys_a7_100 /mnt/p/NexysA7/neorv32/top.bit

# Subir y ejecutar programa
python3 /mnt/p/NexysA7/neorv32/upload.py /mnt/p/NexysA7/neorv32/sw/sys_test/neorv32_exe.bin

# === Frecuencímetro ===

# Flash frecuencímetro
openFPGALoader -b nexys_a7_100 -f --unprotect-flash /mnt/p/NexysA7/bitstreams/top.bit

# UART frecuencímetro
python3 -c "import serial; s=serial.Serial('/dev/ttyUSB1',115200,timeout=4); print(s.read(200).decode())"
```
