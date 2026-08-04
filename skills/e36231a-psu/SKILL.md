---
name: e36231a-psu
description: "(oh-my-embedded) Keysight E36231A DC Power Supply. 30V/30A/200W single-channel programmable PSU. Use for precision voltage sourcing, current monitoring, power sequencing, battery simulation. Access via SCPI over LAN (VXI-11) or USB using pyvisa-py."
---

# Keysight E36231A DC Power Supply

Programmable single-channel DC PSU: 0-30V, 0-30A, 200W max, 1 mV/1 mA resolution, LAN + USB.

---

## Setup

```python
import pyvisa

rm = pyvisa.ResourceManager('@py')

# LAN (preferred — no usbipd needed)
psu = rm.open_resource('TCPIP::192.168.1.30::inst0::INSTR')

# USB (requires usbipd forwarding to WSL)
psu = rm.open_resource('USB0::0x2A8D::0x2202::MY59001234::INSTR')

psu.timeout = 5000
print(psu.query('*IDN?'))
# → Keysight Technologies,E36231A,MY59001234,1.0.2-1.05
```

---

## Basic Operation

```python
# Set 3.3V, 1A limit, output on
psu.write('VOLT 3.3')
psu.write('CURR 1.0')
psu.write('OUTP ON')

# Read actual values
v = float(psu.query('MEAS:VOLT?'))
i = float(psu.query('MEAS:CURR?'))
p = float(psu.query('MEAS:POW?'))
print(f"{v:.4f}V  {i:.4f}A  {p:.3f}W")

# Output off
psu.write('OUTP OFF')
```

---

## Precision Measurement

The E36231A has built-in DVM-quality measurement:

```python
# High-resolution measurement (5.5 digit)
v = float(psu.query('MEAS:VOLT? 1.0V'))    # 1V range = best resolution
v_full = float(psu.query('MEAS:VOLT? AUTO'))

# Current measurement with auto-ranging
i = float(psu.query('MEAS:CURR? AUTO'))

# Array measurement (capture V/I over time)
psu.write('SENS:SWE:POIN 100')
psu.write('SENS:SWE:TINT 100 ms')
psu.write('SENS:SWE:OFFS:POIN 0')
psu.write('INIT')
psu.query('*OPC?')
voltages = psu.query_ascii_values('FETC:VOLT?')
currents = psu.query_ascii_values('FETC:CURR?')
```

---

## Sequencing / Arbitrary Waveform

```python
# Voltage ramp: 0V → 5V in 1s, hold 2s, ramp down
points = 100
v_ramp = [i * 5.0 / points for i in range(points)]   # 0→5V
v_hold = [5.0] * 200                                    # hold
v_down = [5.0 - i * 5.0 / points for i in range(points)] # 5→0V

waveform = v_ramp + v_hold + v_down

# Program arbitrary waveform (list mode)
psu.write(f'LIST:VOLT {",".join(f"{v:.3f}" for v in waveform)}')
psu.write(f'LIST:STEP 0.01')  # 10ms per step
psu.write('LIST:COUN 1')
psu.write('OUTP ON')
psu.write('INIT')
psu.query('*OPC?')
psu.write('OUTP OFF')
```

---

## Battery Simulation

```python
# Simulate Li-Ion cell: 4.2V full, 3.0V empty
# Output resistance 100mΩ (battery internal resistance)
psu.write('VOLT 4.2')
psu.write('CURR 2.0')           # 2A max
psu.write('VOLT:PROT 4.25')     # OVP at 4.25V

# Set output resistance (battery ESR simulation)
psu.write('OUTP:RES 0.1')       # 100 mΩ

psu.write('OUTP ON')

# Monitor as "battery" discharges into load
import time
while True:
    v = float(psu.query('MEAS:VOLT?'))
    i = float(psu.query('MEAS:CURR?'))
    v_actual = v - (i * 0.1)    # voltage at sense point
    print(f"Battery: {v_actual:.3f}V  Load: {i:.3f}A")
    if v < 3.0:
        break
    time.sleep(1)

psu.write('OUTP OFF')
```

---

## OCP/OVP Protection

```python
psu.write('VOLT:PROT 5.5')      # OVP trip at 5.5V
psu.write('VOLT:PROT:STAT ON')
psu.write('CURR:PROT 2.5')      # OCP trip at 2.5A
psu.write('CURR:PROT:STAT ON')

# Check if tripped
tripped = psu.query('VOLT:PROT:TRIP?')
if int(tripped.strip()):
    print("⚠ OVP tripped!")
    psu.write('VOLT:PROT:CLE')
```

---

## Power Supply Analysis (with E36231A + Prodigit 3310F + N9000A)

Orchestrate load regulation + ripple + EMI in one sweep:

```python
# PSU under test: E36231A set to 12V
psu.write('VOLT 12')
psu.write('CURR 3')
psu.write('OUTP ON')

loads = [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
for iload in loads:
    load.write(f'CURR {iload}')
    load.write('INP ON')
    time.sleep(0.5)
    
    v_out = float(psu.query('MEAS:VOLT?'))
    i_out = float(psu.query('MEAS:CURR?'))
    ripple = float(psu.query('MEAS:VOLT:AC?'))  # AC component
    
    # Spectrum at this load
    cxa.write(f'FREQ:CENT {300e6}')
    cxa.write('INIT:IMM')
    cxa.query('*OPC?')
    peak = float(cxa.query('CALC:MARK1:Y?'))
    
    print(f"{iload:.1f}A: {v_out:.3f}V  Ripple: {ripple*1e3:.1f}mVrms  EMI@300M: {peak:.1f}dBm")
    
    load.write('INP OFF')

psu.write('OUTP OFF')
```

---

## SCPI Quick Reference

| Command | Description |
|---|---|
| `VOLT <V>` | Set voltage |
| `CURR <A>` | Set current limit |
| `OUTP ON/OFF` | Output on/off |
| `MEAS:VOLT?` | Measure voltage |
| `MEAS:CURR?` | Measure current |
| `MEAS:POW?` | Measure power |
| `MEAS:VOLT:AC?` | Measure AC ripple (mVrms) |
| `VOLT:PROT <V>` | OVP level |
| `CURR:PROT <A>` | OCP level |
| `OUTP:RES <ohm>` | Output resistance (battery sim) |
| `LIST:VOLT <v1,v2,...>` | Arbitrary voltage list |
| `LIST:STEP <s>` | List step time |
| `LIST:COUN <n>` | List repeat count |
| `INIT` | Trigger/start list |
| `*RST` | Factory reset |
| `SYST:ERR?` | Read error queue |

---

## Specifications

| Parameter | Rating |
|---|---|
| Voltage | 0-30 V |
| Current | 0-30 A |
| Max power | 200 W |
| Voltage resolution | 1 mV |
| Current resolution | 1 mA |
| Voltage accuracy | 0.03% + 5 mV |
| Ripple & noise | < 2 mVrms / 20 mVpp |
| Load regulation | < 0.01% + 2 mV |
| Transient response | < 50 μs (50% load step) |
| Interface | LAN (VXI-11), USB (USBTMC), optional GPIB |

## Pro Tips

- **Remote sense**: use 4-wire sense to compensate lead drop at high currents. Connect S+/S- to the load point.
- **Series operation**: two E36231A can be stacked in series for 60V. Set identical current limits.
- **Parallel operation**: parallel two units for 60A. Use master-slave tracking.
- **Ripple measurement**: `MEAS:VOLT:AC?` gives RMS ripple. For peak-to-peak, use the ADP2230 scope on AC coupling across the output.
- **Output capacitance**: the PSU has ~100 μF output capacitance. For sensitive DUTs, add a series diode to prevent back-feeding.
- **Digital I/O**: the rear D-sub connector has digital I/O pins for trigger in/out and fault output — useful for automated test sequencing.
