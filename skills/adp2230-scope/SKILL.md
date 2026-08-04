---
name: adp2230-scope
description: "(oh-my-embedded) Digilent Analog Discovery Pro ADP2230 mixed-signal oscilloscope. Use for waveform capture, FFT, bode analysis, logic analyzer, pattern generator, protocol decoding. Requires pydwf + usbipd forwarding."
---

# ADP2230 Scope & Instruments Skill

Digilent Analog Discovery Pro ADP2230 — 2-ch scope (100 MS/s, 55 MHz BW), 2-ch AWG, 16-ch logic analyzer, pattern generator, network analyzer, spectrum analyzer, impedance analyzer.

---

## Setup

### Prerequisites (already installed)

- `pydwf` 1.1.19 — Python wrapper for WaveForms SDK
- `usbipd-win` — USB forwarding from Windows to WSL
- `adp2230-attach` script in `~/.local/bin/` — auto-attach the ADP2230 to WSL

### Verify connection

```bash
# Run the auto-attach monitor (once per WSL session)
adp2230-attach

# Test via pydwf
python3 -c "
from pydwf import DwfLibrary
dwf = DwfLibrary()
print(f'WaveForms version: {dwf.version}')
dev = dwf.deviceEnum.enumDevices()
print(f'Devices found: {dev.count}')
dwf.deviceEnum.deviceOpen(0)
print('Device opened OK')
"
```

---

## Scope (Oscilloscope)

```python
from pydwf import DwfLibrary, DwfEnumFilter
from pydwf.utilities import openDwfDevice
import numpy as np

dwf = DwfLibrary()
with openDwfDevice(dwf, DwfEnumFilter.AnalogIn) as device:
    ain = device.analogIn
    
    # Configure channel 1
    ain.channelEnableSet(0, True)
    ain.channelRangeSet(0, 5.0)     # ±5V range
    ain.channelOffsetSet(0, 0.0)
    
    # Acquisition config
    ain.acquisitionModeSet(0)         # single
    ain.frequencySet(10e6)            # 10 MS/s
    ain.bufferSizeSet(8192)
    
    # Trigger
    ain.triggerSourceSet(0)           # trigsrcDetectorAnalogIn
    ain.triggerPositionSet(0.0)       # 0% pre-trigger
    ain.triggerChannelSet(0)
    ain.triggerLevelSet(1.5)
    ain.triggerConditionSet(0)        # rising edge
    
    # Capture
    ain.configure(False, True)
    while ain.status(True) != 3:      # DwfStateDone
        pass
    
    samples = ain.statusData(0, 8192)
    print(f"Captured {len(samples)} samples, range: {min(samples):.3f}V to {max(samples):.3f}V")
```

### Key acquisition modes
| Mode | Use |
|---|---|
| `acqmodeSingle` (0) | One-shot capture |
| `acqmodeScanShift` (2) | Rolling view |
| `acqmodeScanScreen` (3) | Oscilloscope-like |
| `acqmodeRecord` (4) | Deep capture (to RAM) |

---

## AWG (Waveform Generator)

```python
with openDwfDevice(dwf, DwfEnumFilter.AnalogOut) as device:
    awg = device.analogOut
    
    # Channel 1: 1kHz sine, 2Vpp, 0V offset
    awg.nodeEnableSet(0, 0, True)      # carrier enable
    awg.nodeFunctionSet(0, 0, 1)        # funcSine = 1
    awg.nodeFrequencySet(0, 0, 1000.0)
    awg.nodeAmplitudeSet(0, 0, 2.0)
    awg.nodeOffsetSet(0, 0, 0.0)
    awg.configure(0, True)
```

### Waveform types
```
funcSine=1, funcSquare=2, funcTriangle=3, funcRampUp=4,
funcRampDown=5, funcNoise=6, funcDC=7, funcCustom=30
```

---

## Logic Analyzer

```python
with openDwfDevice(dwf, DwfEnumFilter.DigitalIn) as device:
    din = device.digitalIn
    
    din.internalClockInfo()  # shows max clock rate
    din.dividerSet(10)       # for 100 MHz base: 10 = 10 MS/s
    din.sampleFormatSet(16)  # 16-bit wide
    din.bufferSizeSet(4096)
    
    din.configure(False, True)
    while din.status(True) != 3:
        pass
    
    data = din.statusData(4096, return_bytearray=True)
    print(f"DIO[0..7]: {[(data[i] & 0xFF) for i in range(10)]}")
```

---

## Network Analyzer (Bode Plot)

```python
with openDwfDevice(dwf) as device:
    device.analogImpedance. ...
    # Uses Wavegen channel 1 as stimulus
    # Scope channel 1 = reference, channel 2 = response
    # Measures gain/phase vs frequency
```

**Quick approach**: use WaveForms SDK `AnalogImpedance` for Bode plots. Set AWG sine sweep with stepped frequencies, measure gain/phase at each step.

---

## Pattern Generator

```python
with openDwfDevice(dwf, DwfEnumFilter.DigitalOut) as device:
    dout = device.digitalOut
    
    # Generate custom pattern
    pattern = [0xAA, 0x55, 0xAA, 0x55] * 256
    dout.enableSet(0, True)
    dout.dividerSet(0, 100)  # clock divider
    dout.dataSet(0, pattern)
    dout.configure(True)
```

---

## Pro Tips

- **Always close the device** with a context manager (`with`) or `device.close()`
- **Bandwidth limit**: enable 20 MHz BW limit on scope for cleaner low-freq measurements: `ain.channelFilterSet(0, 5)` (filterDecimate)
- **Impedance analyzer**: use the Wavegen + Scope in tandem with a reference resistor to measure component impedance
- **Protocol decoding**: capture with logic analyzer, decode UART/SPI/I2C in Python
- **ADC calibration**: calibrate offset/gain with `device.analogIn.channelOffsetSet` and `channelRangeSet` after a known reference
