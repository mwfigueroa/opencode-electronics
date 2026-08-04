---
name: n9000a-cxa
description: "(oh-my-embedded) Agilent/Keysight CXA Signal Analyzer N9000A. RF spectrum analyzer 9 kHz - 3/7.5 GHz. Use for spectrum analysis, phase noise, channel power, occupied BW, spurious emissions. Access via SCPI over LAN (VXI-11) or USB (USBTMC) using pyvisa-py."
---

# Keysight CXA N9000A Signal Analyzer

RF spectrum analyzer: 9 kHz – 3.0 GHz (std) or 7.5 GHz (opt 503), DANL -148 dBm/Hz, 10 MHz analysis BW.

---

## Setup

### Connection

```python
import pyvisa

rm = pyvisa.ResourceManager('@py')

# LAN (VXI-11)
cxa = rm.open_resource('TCPIP::192.168.1.50::inst0::INSTR')

# USB (USBTMC — requires usbipd forwarding to WSL)
cxa = rm.open_resource('USB0::0x0957::0x1805::MY51234567::INSTR')

cxa.timeout = 10000
print(cxa.query('*IDN?'))
# → Agilent Technologies,N9000A,MY51234567,A.14.16
```

### Verify basic functions

```python
# Check options installed
print(cxa.query('*OPT?'))
# → 503,PFR,EMC,B25,...

# Self-test
print(cxa.query('*TST?'))
# → 0 (pass)
```

---

## Spectrum Analysis

### Basic sweep

```python
# Center 1 GHz, span 100 MHz, RBW 100 kHz
cxa.write('FREQ:CENT 1 GHz')
cxa.write('FREQ:SPAN 100 MHz')
cxa.write('BAND 100 kHz')
cxa.write('BAND:VID 1 MHz')

# Single sweep
cxa.write('INIT:CONT OFF')
cxa.write('INIT:IMM')
cxa.query('*OPC?')  # wait for completion

# Read trace
cxa.write('TRAC? TRACE1')
raw = cxa.read_raw()

# Parse binary trace data (definite-length block: #<digits><length><data>)
import struct
header = raw[:2]     # e.g. '#6'
n_digits = int(raw[1:2])
n_bytes = int(raw[2:2+n_digits])
data_start = 2 + n_digits
count = n_bytes // 4
trace = struct.unpack(f'>{count}f', raw[data_start:data_start+n_bytes])

print(f"Trace points: {len(trace)}, Max: {max(trace):.2f} dBm")
```

### Marker measurements

```python
# Peak search
cxa.write('CALC:MARK1:MAX')
peak_freq = float(cxa.query('CALC:MARK1:X?'))
peak_amp = float(cxa.query('CALC:MARK1:Y?'))
print(f"Peak: {peak_amp:.2f} dBm at {peak_freq/1e6:.3f} MHz")

# Delta marker
cxa.write('CALC:MARK2 ON')
cxa.write('CALC:MARK2:X 1.1 GHz')
cxa.write('CALC:DELT2:MODE ON')
cxa.write('CALC:DELT2:REF 1')
delta = float(cxa.query('CALC:DELT2:Y?'))
print(f"Delta: {delta:.2f} dB")
```

---

## Channel Power / ACPR

```python
# W-CDMA channel power measurement
cxa.write('INST:SEL CHP')
cxa.write('CONF:CHP')
cxa.write('FREQ:CENT 2.14 GHz')
cxa.write('CHP:BAND:INT 3.84 MHz')  # integration BW

cxa.write('INIT:CHP')
cxa.query('*OPC?')

ch_power = float(cxa.query('FETC:CHP:CHP?'))
psd = float(cxa.query('FETC:CHP:DENS?'))
print(f"Channel power: {ch_power:.2f} dBm / 3.84 MHz")
print(f"Power density: {psd:.2f} dBm/Hz")
```

---

## Occupied Bandwidth

```python
cxa.write('INST:SEL OBW')
cxa.write('CONF:OBW 99.0')          # 99% power bandwidth
cxa.write('FREQ:CENT 915 MHz')

cxa.write('INIT:OBW')
cxa.query('*OPC?')

obw = float(cxa.query('FETC:OBW?'))
print(f"Occupied BW: {obw/1e3:.3f} kHz")
```

---

## Phase Noise

```python
# Requires Phase Noise personality (opt PFR)
cxa.write('INST:SEL PN')
cxa.write('CONF:PN')
cxa.write('FREQ:CENT 1 GHz')

cxa.write('INIT:PN')
cxa.query('*OPC?')

# Read phase noise at multiple offsets
for offset_khz in [1, 10, 100, 1000]:
    cxa.write(f'CALC:PN:OFFS {offset_khz} KHz')
    pn = float(cxa.query('CALC:PN:DATA?'))
    print(f"PN @ {offset_khz} kHz: {pn:.1f} dBc/Hz")
```

---

## Spurious Emissions Mask

```python
# Set limit line
cxa.write('CALC:LLIN1:NAME "FCC_Part15"')
cxa.write('CALC:LLIN1:CONT:DOM FREQ')
cxa.write('CALC:LLIN1:DATA 30 MHz,-20,88 MHz,-20,88 MHz,-15,216 MHz,-15,216 MHz,-10,960 MHz,-10')

# Enable limit test
cxa.write('CALC:LLIN1:STAT ON')
cxa.write('CALC:LLIN1:FAIL?')
result = cxa.query('CALC:LLIN1:FAIL?')
if int(result.strip()) > 0:
    print("⚠ Limit line violations detected")
```

---

## Trace Math

```python
# Trace 2 = Trace 1 minus reference (for comparison)
cxa.write('TRAC2:MATH (TRACE1 - TRACE3)')
cxa.write('TRAC2:TYPE AVER')

# Max hold
cxa.write('TRAC1:TYPE MAXH')
cxa.write('INIT:CONT ON')  # continuous sweep

# Clear max hold
cxa.write('TRAC1:TYPE WRIT')
```

---

## Preamp & Attenuation

```python
# Internal preamp (opt P03)
cxa.write('POW:GAIN 30 dB')     # preamp on
cxa.write('POW:GAIN:STAT ON')

# Manual attenuation
cxa.write('POW:ATT 10 dB')

# Auto attenuation (default)
cxa.write('POW:ATT:AUTO ON')

# Reference level
cxa.write('DISP:WIND:TRAC:Y:RLEV -10 dBm')
```

---

## Key SCPI Commands

| Command | Description |
|---|---|
| `*IDN?` | Identity |
| `*OPT?` | Installed options |
| `FREQ:CENT <f>` | Center frequency |
| `FREQ:SPAN <f>` | Span |
| `BAND <f>` | Resolution bandwidth (RBW) |
| `BAND:VID <f>` | Video bandwidth (VBW) |
| `SWE:TIME <t>` | Sweep time |
| `INIT:CONT ON/OFF` | Continuous sweep |
| `INIT:IMM` | Single sweep |
| `TRAC? TRACE1` | Read trace data |
| `CALC:MARK1:MAX` | Peak search |
| `CALC:MARK1:X?` | Marker frequency |
| `CALC:MARK1:Y?` | Marker amplitude |
| `POW:ATT <dB>` | Input attenuation |
| `DISP:WIND:TRAC:Y:RLEV <dBm>` | Reference level |

---

## Pro Tips

- **DANL improvement**: reduce RBW, enable preamp, reduce attenuation for best noise floor
- **Sweep time**: `SWE:TIME:AUTO ON` auto-calculates; for manual, `SWE:TIME > (span / RBW^2) * k` where k ≈ 1 for sweep, 2.5 for FFT
- **IQ capture**: opt B25 (IQ Analyzer) enables IQ data streaming at up to 10 MHz BW
- **EMC measurements**: opt EMC enables quasi-peak/EMI detectors and CISPR bandwidths
- **Preset**: `SYST:PRES:DEF` resets to default state before measurements
- **USB connection**: requires Keysight IO Libraries on Windows OR `pyvisa-py` with usbipd forwarding to WSL
