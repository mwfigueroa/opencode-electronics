# HC32F4A0 — Guía de Desarrollo

> HDSC (Huada Semiconductor / XHSC) · ARM Cortex-M4 @ 240 MHz · 516 KB RAM · 1-2 MB Flash

---

## Especificaciones del núcleo

| Parámetro | Valor |
|---|---|
| **CPU** | ARM Cortex-M4 (FPU + DSP) |
| **Frecuencia máx** | 240 MHz |
| **Flash** | 1 MB (variantes G) o 2 MB (variantes T) |
| **RAM** | 516 KB |
| **ADC** | 12-bit |
| **DAC** | 12-bit |
| **Voltaje** | 1.8 V ~ 3.6 V |
| **Temp. operación** | -40 °C a +105 °C |
| **Oscilador** | Interno + externo |
| **Periféricos** | USB OTG, CAN, Ethernet MAC, SDIO, I2S, SPI, I2C, UART, Timers avanzados, RTC |

---

## Variantes y disponibilidad (LCSC)

Los sufijos siguen el patrón: **HC32F4A0 + [pines] + [Flash] + [encapsulado]**

- **Pines:** `P` = 100, `R` = 144, `S` = 176, `T` = 208
- **Flash:** `T` = 2 MB (2nd gen), `G` = 1 MB
- **Encapsulado:** `TB` = LQFP, `HB` = BGA/VFBGA/TFBGA

| SKU (LCSC) | Modelo | Encapsulado | Flash | I/O | Stock | Precio (1u) |
|---|---|---|---|---|---|---|
| `C963558` | HC32F4A0PITB | LQFP-100 (14×14) | 2 MB | 83 | 50 | ~$5.35 |
| `C963557` | HC32F4A0RITB | LQFP-144 (20×20) | 2 MB | 116 | 440 | ~$6.50 |
| `C963555` | HC32F4A0SITB | LQFP-176 (24×24) | 2 MB | 142 | 40 | ~$6.98 |
| `C963556` | HC32F4A0SIHB | VFBGA-176 (10×10) | 2 MB | 142 | 32 | ~$6.06 |
| `C5263760` | HC32F4A0TIHB | TFBGA-208 | 2 MB | — | 1243 | ~$6.91 |
| `C3036725` | HC32F4A0RGTB | LQFP-144 (20×20) | 1 MB | 116 | 0 | ~$5.75 |
| `C3036726` | HC32F4A0SGTB | LQFP-176 (24×24) | 1 MB | 142 | 0 | ~$9.07 |

**Mejor relación stock/precio para prototipado:** `C963557` (HC32F4A0RITB, LQFP-144) con 440 unidades a ~$6.50.

---

## Toolchain de desarrollo

Tres opciones oficiales soportadas por HDSC:

### Opción 1 — IAR EWARM 8.4+

- IDE propietario (licencia paga)
- CMSIS Pack incluido en el SDK oficial
- Windows solamente
- Mejor optimización de código, soporte oficial HDSC

### Opción 2 — Keil MDK

- IDE propietario (licencia paga)
- CMSIS Pack incluido en el SDK oficial
- Windows solamente
- El más usado en China para MCUs ARM

### Opción 3 — GCC ARM + CMake (recomendado para Linux/WSL)

Suite open source completa:

| Herramienta | Propósito | Instalación |
|---|---|---|
| **gcc-arm-none-eabi** | Compilador cruzado ARM | `sudo apt install gcc-arm-none-eabi` o [Arm GNU Toolchain](https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads) |
| **CMake** >= 3.27 | Sistema de build | `sudo apt install cmake` |
| **pyOCD** | Flasheo y debug por SWD | `pip install pyocd` |
| **MinGW** (solo Windows) | `make` y utilidades | [mingw-builds](https://github.com/niXman/mingw-builds-binaries/releases) |

---

## SDK (Device Driver Library)

### Repositorio oficial (espejo en GitHub)

**[Mmatsnev/hc32f4a0](https://github.com/Mmatsnev/hc32f4a0)** — mirror no oficial con todo el material relevante:

```
├── CMSISPack/                  # CMSIS Packs para IAR y Keil
├── DeviceDriverLibrary/        # DDL (HAL de HDSC)
│   └── hc32f4a0_ddl/           # Drivers + ejemplos por periférico
│       ├── driver/             # Código fuente de los drivers (src + inc)
│       ├── example/            # Proyectos de ejemplo (IAR, MDK, GCC)
│       └── ...
├── Document/                   # Datasheet, manual de usuario, guía rápida
├── Hardware/                   # Esquemático de la placa de evaluación (LQFP-176)
└── Utilities/
    └── hdsc_dap/               # Driver USB (Windows) y firmware del debug probe
        ├── driver/             # Driver para Windows (CMSIS-DAP)
        └── firmware/           # FW para el probe
```

### Template CMake listo para usar

**[nczyw/hc32f4a0-drivers](https://github.com/nczyw/hc32f4a0-drivers)** — proyecto CMake moderno con DDL v2.3.0:

- 3 modos configurables: `bootloader`, `app`, `normal`
- Soporte opcional para **RT-Thread**
- `printf` con float habilitado
- Warnings tratados como errores (strict mode)
- Submódulo git: `git submodule add https://github.com/nczyw/hc32f4a0-drivers.git drivers`

---

## Quickstart con GCC + CMake (desde cero)

```bash
# 1. Clonar el template CMake
git clone https://github.com/nczyw/hc32f4a0-drivers.git
cd hc32f4a0-drivers

# 2. Configurar el build
cmake -B build \
  -DCMAKE_BUILD_TYPE=Debug \
  -DMCU_TYPE=HC32F4A0xI \
  -DBOOTLOADER=OFF \
  -DAPP=OFF \
  -DRT-THREAD=OFF \
  -G "Unix Makefiles"

# 3. Compilar
cmake --build build

# 4. Flashear al MCU (con pyOCD)
pyocd flash -t hc32f4a0 build/*.hex

# 5. Debug (GDB remoto vía pyOCD)
pyocd gdbserver -t hc32f4a0 &
arm-none-eabi-gdb build/*.elf -ex "target remote :3333"
```

---

## Debug Probe

### HDSC DAP (probe oficial)

Debugger CMSIS-DAP oficial de Huada. Se conecta por USB a la PC y por SWD (SWCLK + SWDIO + GND) al MCU.

**Driver en Windows:** instalar desde `Utilities/hdsc_dap/driver/` del SDK.

**En Linux/WSL:** no requiere driver adicional — se detecta como USB HID automáticamente.

### Alternativas compatibles

| Probe | Protocolo | Notas |
|---|---|---|
| **CMSIS-DAP genérico** | CMSIS-DAP | Cualquier debugger compatible (RPi Pico con DAPLink funciona) |
| **J-Link** | SWD + JTAG | Necesita software de Segger |
| **ST-Link v2/v3** | SWD | Funciona con OpenOCD, no necesariamente soportado por HDSC |
| **pyOCD** | CMSIS-DAP | Comunicación directa sin drivers extras (recomendado para Linux) |

---

## Comparativa con STM32F4

| Característica | HC32F4A0 | STM32F407 | STM32F429 |
|---|---|---|---|
| CPU | Cortex-M4 240 MHz | Cortex-M4 168 MHz | Cortex-M4 180 MHz |
| Flash máx | 2 MB | 1 MB | 2 MB |
| RAM | 516 KB | 192 KB | 256 KB |
| Precio (100u) | ~$5-7 | ~$8-12 | ~$10-15 |
| Ecosistema | Joven, SDK básico | Maduro, HAL + CubeMX | Maduro, HAL + CubeMX |
| Documentación | En chino principalmente | Inglés y español | Inglés y español |
| Proveedor | Huada Semiconductor (China) | STMicroelectronics | STMicroelectronics |

---

## Notas y consideraciones

1. **Documentación mayormente en chino** — los datasheets y manuales están en chino mandarín. Hay algunos recursos traducidos por la comunidad.
2. **Ecosistema joven** — no tiene PlatformIO, Arduino, ni Mbed. Todo es sobre el SDK oficial o CMake artesanal.
3. **Sin símbolos KiCad pre-armados** — hay que crear los símbolos y footprints manualmente o importar desde LCSC (IDs listados arriba).
4. **Sin soporte en PlatformIO** — la búsqueda `pio boards` no arroja resultados para HC32.
5. **Precio competitivo** — ~30-40% más barato que STM32 equivalentes, con más RAM y frecuencia.
6. **RT-Thread** — el RTOS chino más popular tiene soporte para HC32F4A0. Ver [nczyw/hc32f4a0-drivers](https://github.com/nczyw/hc32f4a0-drivers).

---

## Recursos

- [Mmatsnev/hc32f4a0](https://github.com/Mmatsnev/hc32f4a0) — SDK completo (DDL, docs, ejemplos, CMSIS Pack)
- [nczyw/hc32f4a0-drivers](https://github.com/nczyw/hc32f4a0-drivers) — Template CMake moderno
- [nczyw/hc32f4a0-template](https://github.com/nczyw/hc32f4a0-template) — Template CMake sin RT-Thread/FATFS
- [jinsc123654/hc32f4a0_rtt](https://github.com/jinsc123654/hc32f4a0_rtt) — RT-Thread para HC32F4A0
- [nczyw/hc32f4a0-bootloader](https://github.com/nczyw/hc32f4a0-bootloader) — Bootloader
- [SoCXin/HC32F4A0](https://github.com/SoCXin/HC32F4A0) — Ejemplo mínimo para HC32F4A0PITB
- [Descargar GCC ARM](https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads)
- [pyOCD](https://github.com/pyocd/pyOCD)
- LCSC: [C963557](https://www.lcsc.com/product-detail/_XHSC-_C963557.html) · [C963558](https://www.lcsc.com/product-detail/_XHSC-_C963558.html) · [C5263760](https://www.lcsc.com/product-detail/_XHSC-_C5263760.html)
