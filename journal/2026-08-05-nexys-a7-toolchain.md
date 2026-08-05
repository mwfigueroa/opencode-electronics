# Nexys A7 — Toolchain FPGA y Discovery

**Fecha**: 2026-08-05

## Contexto

Se integró al ecosistema OpenCode una placa **Digilent Nexys A7-100T** (Artix-7 XC7A100T). Se instaló el toolchain completo para desarrollo FPGA: programación, simulación, testbenches y herramientas complementarias.

## Discovery

1. **Placa conectada por USB** → detectada como `USB Serial Converter A/B` (FTDI FT2232H, VID 0403:PID 6010)
2. **Canal A** = JTAG para programación del FPGA
3. **Canal B** = UART para comunicación con el diseño cargado
4. **Forwarding a WSL** vía usbipd (BUSID 6-4)
5. **Verificación JTAG**: OpenFPGALoader confirma XC7A100T (IDCODE 0x03631093)

```
Nexys A7 → USB → usbipd → WSL → OpenFPGALoader → JTAG: XC7A100T ✅
```

## Stack de herramientas instalado

### Programación

| Herramienta | Versión | Instalación |
|---|---|---|
| **OpenFPGALoader** | 0.12 | `apt install openfpgaloader` |
| **Vivado ML Standard** | Pendiente descargar | Instalador web AMD → `P:\NexysA7\Vivado\` |

### Síntesis open-source

| Herramienta | Versión |
|---|---|
| **yosys** | 0.33 |

### Simulación

| Herramienta | Versión | Uso |
|---|---|---|
| **iverilog** | 12.0 | Simulación rápida de Verilog |
| **verilator** | 5.020 | Simulación de alto rendimiento (compila a C++) |
| **GTKWave** | 3.3.116 | Visor de formas de onda (VCD, FST) |
| **cocotb** | 2.0.1 | Testbenches en Python sobre iverilog/verilator |

### Utilidades

| Herramienta | Versión | Uso |
|---|---|---|
| **fusesoc** | 2.4 | Package manager para cores HDL |
| **graphviz** | 2.43 | Visualización RTL (dot → SVG/PNG) |
| **picocom** | 3.1 | Terminal serial para debug UART |
| **LiteX** | 2024.12 | SoC builder: CPUs RISC-V + periféricos en FPGA |
| **migen** | 0.9.2 | Python framework HDL (dependencia de LiteX) |

## Diseño de ejemplo: LED blinker + UART echo

Creado en `P:\NexysA7\src\`:

| Archivo | Descripción |
|---|---|
| `top.v` | LED blinker (0.75 Hz) + UART echo (115200 baud, 8N1) |
| `NexysA7.xdc` | Constraints: reloj 100 MHz (E3), LEDs, UART, 7-segmentos |

### Funcionalidad del diseño

- **LED[0]**: parpadea a ~0.75 Hz
- **LED[1]**: actividad TX UART
- **LED[2]**: actividad RX UART
- **LED[3]**: eco de línea RX
- **UART**: 115200 baud — reenvía todo lo que recibe
- **7-seg**: muestra el nibble alto del último byte recibido

## Scripts de automatización

| Archivo | Propósito |
|---|---|
| `scripts/build.tcl` | Síntesis + implementación con Vivado |
| `scripts/program.tcl` | Programación con Vivado Lab |
| `scripts/program.py` | Programador Python (usa OpenFPGALoader o Vivado) |
| `scripts/program_fast.bat` | Un clic: forwardea USB + programa |

## Estructura de directorios

```
P:\NexysA7\
├── src\
│   ├── top.v               ← diseño Verilog
│   └── NexysA7.xdc         ← constraints
├── bitstreams\              ← destino de .bit generados
├── scripts\
│   ├── build.tcl            ← síntesis (requiere Vivado)
│   ├── program.tcl          ← programación (Vivado Lab)
│   ├── program.py           ← programador OpenCode
│   └── program_fast.bat     ← one-click programmer
├── docs\
│   └── README.md            ← guía de uso
└── Vivado\                  ← (pendiente instalar)
```

## Flujo de trabajo

### Sin Vivado (desarrollo + simulación)

```
top.v ──► iverilog ──► sim.vcd ──► GTKWave
  │
  ├──► cocotb (Python) ──► testbench automatizado
  │
  └──► yosys ──► netlist ──► graphviz ──► esquema RTL
```

### Con Vivado (síntesis + programación)

```
top.v + NexysA7.xdc ──► Vivado ──► top.bit
                                     │
                        OpenFPGALoader ──► Nexys A7 (JTAG)
                                             │
                        picocom ──► UART debug (115200 baud)
```

## Comandos rápidos

```bash
# Simular con iverilog
iverilog -o sim.vvp top.v tb.v && vvp sim.vvp

# Ver waveforms
gtkwave sim.vcd

# Sintetizar con yosys (análisis RTL)
yosys -p "read_verilog top.v; synth_xilinx -top top; show"

# Programar con OpenFPGALoader (ya funciona)
openFPGALoader -b nexys_a7_100 /mnt/p/NexysA7/bitstreams/top.bit

# Terminal serial
picocom -b 115200 /dev/ttyUSB1

# Generar SoC con LiteX (ejemplo: CPU RISC-V + periféricos)
litex_soc_gen --cpu=vexriscv --build --load
```

## Próximos pasos

- [ ] Descargar e instalar Vivado ML Standard (AMD requiere login via navegador)
- [ ] Sintetizar `top.bit` y programar la Nexys A7
- [ ] Verificar UART echo con picocom
- [ ] Probar cocotb para testbench automatizado del diseño
- [ ] Explorar LiteX para SoC con RISC-V en la Nexys
- [ ] Usar ADP2230 logic analyzer para decodificar señales del FPGA
