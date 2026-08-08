# NEORV32 Bootloader + QSPI — Sesión 7 Agosto 2026

**Fecha**: 2026-08-07

## Logros

- ✅ NEORV32 RV32IMC @ 100 MHz con **bootloader 115200 baud** funcional
- ✅ **QSPI flash programada**: boot persistente verificado (jumper QSPI → power-cycle → bootloader OK)
- ✅ **sys_test**: === ALL TESTS PASSED === (CLK, MISA, GPIO, MUL/DIV)
- ✅ **hello_world**: upload + ejecución correcta vía UART
- ✅ **GitHub**: [NexysA7@aplicacion](https://github.com/mwfigueroa/NexysA7) actualizado

---

## Lecciones estratégicas

### 1. Toolchain RISC-V: picolibc + rv32e = INCOMPATIBLE

**Problema**: `riscv64-unknown-elf-gcc` (Ubuntu 24.04) usa picolibc 1.8.6. Picolibc solo tiene multilibs `rv32iac/ilp32`, no `rv32e/ilp32e`. El NEORV32 compila por defecto con `MARCH=rv32e`.

```
Error: mis-matched ISA string to merge 'e' and 'i'
Error: picolibc libc.a uses 16-byte stack alignment, output uses 4-byte
```

**Solución**: compilar bootloader y aplicaciones con `rv32i/ilp32`:
```bash
make bootloader MARCH=rv32i_zicsr_zifencei MABI=ilp32
```

El NEORV32 con 32 registros ejecuta código `rv32i` sin problemas (es un superset de `rv32e`).

### 2. Bootloader: `--specs=picolibc.specs` ROMPE el crt0

**Problema**: usar `--specs=picolibc.specs` para resolver includes de picolibc **sobreescribe** el `crt0.S` y linker script del bootloader con los de picolibc. El bootloader compila pero no arranca (UART mudo).

**Solución**: NO usar specs. Usar flags manuales:
```bash
USER_FLAGS='-isystem /usr/lib/picolibc/riscv64-unknown-elf/include
            -nostartfiles -nodefaultlibs
            -L/usr/lib/picolibc/riscv64-unknown-elf/lib/rv32iac/ilp32
            -lc -lgcc'
```

### 3. Upload UART: el `\r` CORROMPE el header binario

**Problema**: al enviar `u\r` para entrar en modo upload, el bootloader consume `u` como comando pero `\r` queda en el RX FIFO. Cuando `system_app_load()` empieza a leer el binario, el primer byte que recibe es `0x0D` (`\r`) en vez de `0x4E` (`N` de `NEO!`). Resultado: `ERROR_SIGNATURE`.

**Solución**: enviar solo `u` (sin `\r`):
```python
ser.write(b'u')      # correcto — sin \r
# NO: ser.write(b'u\r')  # \r se come el primer byte del binario
```

### 4. Baud rate: bootloader ≠ aplicación

**Problema**: bootloader a 115200 baud, pero `hello_world` y `sys_test` tenían `#define BAUD_RATE 19200`. Al ejecutar con `e`, el programa reconfiguraba UART a 19200 y la salida se veía como basura a 115200.

**Solución**: unificar baud rate en bootloader Y programas de aplicación:
```c
// En bootloader/config.h
#define UART_BAUD 115200

// En cada aplicación (hello_world, sys_test)
#define BAUD_RATE 115200
```

### 5. QSPI Flash: Vivado 2026.1 erase se CUELGA

**Problema**: `program_hw_cfgmem` con `s25fl128sxxxxxx0-spi-x1_x2_x4`:
- Primer intento: erase OK (~19 min), program/verify falla con "Invalid context"
- Intentos posteriores: erase se cuelga indefinidamente (>1 hora)
- La flash queda con **protección de bloques activada** tras el erase parcial

**Causa**: Vivado 2026.1 + XC7A100T + S25FL128S vía JTAG indirecto tiene bugs de timing/protección.

**Solución**: `openFPGALoader` con `--unprotect-flash`:
```bash
openFPGALoader -b nexys_a7_100 -f --unprotect-flash --verify top.bit
# → Detecta S25FL128S, desbloquea, borra, escribe, verifica: 100%
```

### 6. FTDI: reset necesario post-JTAG

**Problema**: después de usar `openFPGALoader` (JTAG por canal A), el canal B (UART) queda inestable. Las lecturas fallan o devuelven 0 bytes.

**Solución**: detach + reattach del FTDI en WSL:
```powershell
usbipd detach --busid 2-2
usbipd attach --wsl --busid 2-2
```

### 7. FPGA post-ejecución: HALT deja la CPU muerta

**Problema**: después de ejecutar un programa con `e` (execute), la CPU hace HALT al terminar. El bootloader NO vuelve. Solo power-cycle o JTAG reload recuperan la FPGA.

**Mitigación**: en programas de test, agregar loop infinito o `return` al bootloader. Para uso interactivo, mantener el bootloader sin ejecutar `e` a menos que sea necesario.

---

## Estado final del sistema

```
Nexys A7-100T (XC7A100T)
├── Bootloader NEORV32 @ 115200 baud
│   ├── Boot: QSPI flash (jumper QSPI → power-cycle)
│   ├── Comandos: h, i, u, e, r, l, s, x
│   └── Upload: binario NEO! por UART (u + enviar binario + e)
├── CLK: 100 MHz (oscilador onboard E3)
├── MISA: RV32IMC (0x40801104)
├── UART0: FTDI canal B (C4/D4) → /dev/ttyUSB1
├── GPIO[15:0]: LEDs (active high)
└── WNS: +0.884 ns (timing cerrado)
```

### Comandos rápidos

```bash
# Terminal bootloader (WSL)
picocom -b 115200 /dev/ttyUSB1

# Recargar FPGA por JTAG (si se bloqueó)
openFPGALoader -b nexys_a7_100 /mnt/p/NexysA7/neorv32/top.bit

# Programar QSPI flash
openFPGALoader -b nexys_a7_100 -f --unprotect-flash --verify /mnt/p/NexysA7/neorv32/top.bit

# Compilar app para NEORV32 (en WSL)
cd /mnt/p/NexysA7/neorv32/sw/sys_test
make exe RISCV_PREFIX=riscv64-unknown-elf- MARCH=rv32i_zicsr_zifencei MABI=ilp32 \
  USER_FLAGS='-isystem /usr/lib/picolibc/riscv64-unknown-elf/include \
              -nostartfiles -nodefaultlibs \
              -L/usr/lib/picolibc/riscv64-unknown-elf/lib/rv32iac/ilp32 \
              -lc -lgcc \
              -Wl,--defsym,__neorv32_ram_size=8192 \
              -Wl,--defsym,__neorv32_ram_base=0x80000000 \
              -flto -msave-restore'

# Subir y ejecutar (Python)
python3 upload.py /mnt/p/NexysA7/neorv32/sw/sys_test/neorv32_exe.bin
```
