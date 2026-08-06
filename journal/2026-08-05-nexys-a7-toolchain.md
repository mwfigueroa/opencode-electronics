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

- [x] Descargar e instalar Vivado ML Standard (AMD requiere login via navegador)
- [x] Activar licencia Vivado Basic Tier (Host ID: D843AE8CEFC5)
- [x] Sintetizar `top.bit` — **3.65 MB, 0 errores, 0 warnings, WNS=+6.49ns**
- [x] Programar la Nexys A7 vía JTAG con OpenFPGALoader — **100% cargado**
- [x] Verificar LED[0] parpadeando — ✅ Confirmado (6-Ago)
- [x] Corregir pines UART del FTDI canal B — ✅ Pines C4/D4 verificados contra XDC oficial
- [x] Verificar UART TX — ✅ Funcionando (beacon "Nexys A7 Online" cada 2s)
- [ ] Verificar UART RX — ❌ No recibe datos del FTDI (loopback interno confirmado → problema entre FTDI y pin C4)
- [ ] Probar cocotb para testbench automatizado del diseño
- [ ] Explorar LiteX para SoC con RISC-V en la Nexys
- [ ] Usar ADP2230 logic analyzer para decodificar señales del FPGA

---

## Vivado 2026.1 — Instalación y Build

### Instalación

| Dato | Valor |
|---|---|
| **Versión** | Vivado v2026.1 (64-bit) |
| **Build** | 6511674 (Jun 16 2026) |
| **Ubicación** | `P:\AMDDesignTools\2026.1\Vivado\` |
| **Dispositivos** | Solo Artix-7 (~15 GB) |
| **Licencia** | Vivado Basic Tier, Node-Locked |
| **Host ID** | D843AE8CEFC5 |
| **Expira** | 06-Ago-2027 |
| **Cuenta AMD** | martinfigueroa447@hotmail.com |

> **Nota**: AMD cambió el nombre de "Standard Edition" a "Basic Tier License". La licencia es gratuita pero requiere login. El Host ID debe coincidir con la MAC de la placa Ethernet física (no adaptadores virtuales).

### Build exitoso

```
Vivado v2026.1 | XC7A100T-1CSG324 | Ryzen 9 7900X (12 cores) | 64 GB RAM

Synthesis:     0 errors, 0 warnings
Implementation: 0 errors, 0 warnings  
Place:         0 errors, WNS=+6.956 ns
Route:         Router Completed Successfully (0 unrouted nets)
Timing:        WNS=+6.491 ns, WHS=+0.232 ns
Bitstream:     3.65 MB, generated in ~2 min

Total build time: ~4 minutes (Ryzen 7900X, 12 cores)
```

### Programación

```bash
openFPGALoader -b nexys_a7_100 /mnt/p/NexysA7/bitstreams/top.bit
# → Load SRAM: 100% Done
```

### UART Debug (6-Ago-2026)

**Descubrimientos:**
- Pines **C4/D4 confirmados** contra XDC oficial de Digilent ✅
- **UART TX funciona**: beacon "Nexys A7 Online" recibido en `/dev/ttyUSB1` @ 115200 ✅
- **UART RX NO funciona**: no se detectan start bits desde el FTDI hacia C4 ❌
- **Loopback interno** (TX → RX dentro del FPGA) **funciona**: confirma que el código Verilog es correcto ✅
- **Diagnóstico**: la señal del FTDI canal B no está llegando al pin C4 del FPGA. Posible problema de hardware (pista, cold joint, o configuración del FTDI)

**Pruebas realizadas:**
1. Diseño beacon: TX envía "Nexys A7 Online" → recibido OK
2. Loopback interno: `wire rx_line = tx` → eco funcional, LEDs de conteo RX incrementan
3. Programación QSPI flash: exitosa, diseño persiste entre power cycles
4. ADP2230 scope en pin C4: intentado pero la punta no hizo contacto (pin es BGA interno)

**Conclusión**: el diseño Verilog es correcto. La Nexys A7 funciona como transmisor UART. Para usar RX se necesita debuggear la ruta FTDI→C4 con acceso físico al pin (en el chip FTDI, no en el BGA del FPGA).

---

## Triple Cross-Instrument: ADP2230 + TBS1102C + Nexys A7 (6-Ago-2026)

### Configuración

```
ADP2230 AWG (W1) ──► Nexys A7 Pmod JD pin 1 (H4) ──► Frequency Counter
                   │
                   └──► TBS1102C CH1 ──► Medición automática
```

### Resultados

| Instrumento | Rol | Frecuencia | Vpp |
|---|---|---|---|
| **ADP2230** | Genera señal | 10 000 Hz (setpoint) | 3.36V |
| **TBS1102C** | Mide (referencia) | 10 013 Hz | 3.36V |
| **Nexys A7** | Mide + UART | **10 000 Hz** | — |

**Error Nexys vs TBS: 0.13%**

### Detalles técnicos

- **ADP2230 AWG**: square wave, `amplitude_vpp=1.65` (pico, 3.3Vpp real), `offset=1.65V` → señal 0-3.3V
- **Nexys A7**: contador de frecuencia en Verilog con puerta calibrada (93.2M ciclos = 1s empírico) + corrección software (×1073/1000)
- **TBS1102C**: autoset + medición automática FREQuency, PK2pk
- **Conexión**: cable BNC del ADP2230 W1 al Pmod JD de la Nexys. El TBS mide el mismo punto
- **Comunicación**: Nexys envía frecuencia por UART 115200 cada 1s. Los tres instrumentos controlados desde OpenCode

### Lecciones aprendidas

1. **ADP2230 `amplitude_vpp`** es amplitud de pico, no pico a pico → `amp=1.65` = 3.3Vpp real
2. **5V en LVCMOS33** puede dañar el FPGA (Vih_max = 3.45V)
3. **JTAG interfiere con UART** del FTDI → workflow: programar flash, luego power cycle
4. **El contador necesitó calibración**: el gate de 100M ciclos no equivale exactamente a 1 segundo real. Se usó 93.2M ciclos + corrección software → precisión 0.13%
5. **Tres instrumentos verificándose entre sí** desde un solo lenguaje natural
