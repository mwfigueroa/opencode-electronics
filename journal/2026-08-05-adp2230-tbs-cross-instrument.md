# ADP2230 + TBS1102C — Cross-Instrument Verification

**Fecha**: 2026-08-05

## Contexto

Primer ejemplo de orquestación entre dos instrumentos desde OpenCode: generar una señal con el ADP2230 y verificarla con el Tektronix TBS1102C. Todo desde lenguaje natural, sin tocar ningún panel frontal.

## Setup físico

```
ADP2230 W1 (BNC amarillo) ──── cable BNC ──── TBS1102C CH1 (BNC)
```

## Ejecución

> *"generá una señal con el ADP2230 y revisala con el TBS"*

### Paso 1: ADP2230 genera señal

```python
# OpenCode invoca adp2230_awg_generate
{
  "channel": 1,
  "waveform": "sine",
  "frequency_hz": 10000,
  "amplitude_vpp": 1,       # 1V pico → 2Vpp real
  "offset_v": 0,
  "enable": true
}
```

### Paso 2: TBS1102C ejecuta AUTOSET y mide

```python
import usbtmc
tbs = usbtmc.Instrument(usbtmc.list_devices()[0])
tbs.timeout = 5.0

# Autoset para ajustar escalas automáticamente
tbs.write('AUTOSet EXECute')

# Mediciones automáticas
tbs.write('MEASUrement:IMMed:SOUrce CH1')
tbs.write('MEASUrement:IMMed:TYPe FREQuency')
freq = tbs.ask('MEASUrement:IMMed:VALue?')

tbs.write('MEASUrement:IMMed:TYPe PK2pk')
vpp = tbs.ask('MEASUrement:IMMed:VALue?')
```

### Resultados

| Medición | ADP2230 (set) | TBS1102C (medido) | Error |
|---|---|---|---|
| **Frecuencia** | 10 000 Hz | 10 016 Hz | +0.16% |
| **Vpp** | 2.0 V | 2.0 V | ~0% |
| **Vrms** | — | 1.397 V | — |
| **Vmin** | — | -1.0 V | — |
| **Vmax** | — | +1.0 V | — |

## Arquitectura

```
┌─────────────┐     ┌──────────────┐
│  ADP2230    │     │  TBS1102C    │
│  AWG Ch1    │     │  Scope Ch1   │
└──────┬──────┘     └──────┬───────┘
       │ BNC cable         │ USB
       │                   │
  ┌────▼────┐         ┌────▼───────┐
  │  pydwf  │         │  WinUSB    │
  │  (MCP)  │         │  (Zadig)   │
  └────┬────┘         └────┬───────┘
       │                   │ usbipd
       │              ┌────▼───────┐
       │              │ python-    │
       │              │ usbtmc     │
       │              └────┬───────┘
       │                   │
  ┌────▼───────────────────▼───────┐
  │          OpenCode              │
  │  "genera y revisa la señal"    │
  └────────────────────────────────┘
```

## Hallazgos

### ADP2230: amplitude vs Vpp

El parámetro `amplitude_vpp` de la herramienta MCP del ADP2230 usa la convención de pydwf: el valor es la **amplitud de pico** (no pico a pico). Es decir:

| `amplitude_vpp` | Señal real |
|---|---|
| 1.0 | ±1V → **2 Vpp** |
| 2.0 | ±2V → **4 Vpp** |
| 0.5 | ±0.5V → **1 Vpp** |

### TBS1102C: driver

Requirió instalar el driver WinUSB vía [Zadig](https://zadig.akeo.ie/). Sin esto, Windows no reconoce el dispositivo USBTMC y pyvisa-py no puede comunicarse.

### Stack de conexión del TBS

| Capa | Componente |
|---|---|
| Driver Windows | WinUSB (Zadig) |
| Forwarding WSL | usbipd |
| Permisos USB | `chmod 666 /dev/bus/usb/...` |
| Python | python-usbtmc 0.8 |
| Protocolo | SCPI estándar |

### Comandos SCPI probados en TBS1102C

| Comando | Función |
|---|---|
| `*IDN?` | Identificación |
| `AUTOSet EXECute` | Auto-ajuste de escalas |
| `HORizontal:SCAle?` | Timebase actual |
| `CH1:SCAle?` | Escala vertical CH1 |
| `MEASUrement:IMMed:SOUrce CH1` | Seleccionar fuente |
| `MEASUrement:IMMed:TYPe FREQuency` | Tipo de medición |
| `MEASUrement:IMMed:VALue?` | Leer valor |

### Comandos SCPI que fallaron

| Comando | Error |
|---|---|
| `HORizontal:MAIn:SAMPLERate?` | No implementado en TBS1000C |
| `HORizontal:RECOrdlength?` | No implementado |
| `CH1:BANdwidth?` | No implementado |
| `CH1:PRObe?` | No implementado (devuelve string por defecto) |

La serie TBS1000C tiene un subset limitado de SCPI comparado con las series MSO/DPO de Tektronix.

## Próximos pasos

- [ ] Captura de forma de onda (CURVe?) desde el TBS
- [ ] Cross-instrument: ADP2230 barrido de frecuencia + TBS medición automática (Bode plot manual)
- [ ] Agregar TBS1102C al README y ROADMAP
