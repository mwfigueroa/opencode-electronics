---
name: prodigit-3310f
description: "(oh-my-embedded) Prodigit 3310F DC Electronic Load. 300W/60V/60A programmable load. Use for CC/CV/CR/CP modes, battery discharge testing, power supply load regulation. Access via RS-232 or USB-Serial (SCPI-like commands)."
---

# Prodigit 3310F DC Electronic Load

Programmable DC electronic load: 300W max, 60V/60A, 4 modes (CC/CV/CR/CP), dynamic loading, battery test.

---

## Setup

### Connection

The 3310F uses RS-232 (9-pin D-sub) or optional USB. On WSL via usbipd:

```python
import serial

# /dev/ttyUSB0 after usbipd attach
load = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

# Or via pyvisa with serial backend
import pyvisa
rm = pyvisa.ResourceManager('@py')
load = rm.open_resource('ASRL/dev/ttyUSB0::INSTR')
load.baud_rate = 9600
load.timeout = 3000
```

### Serial settings

```
Baud: 9600, 8N1, no flow control
DB9 pinout: 2=RX, 3=TX, 5=GND
```

---

## Operating Modes

### CC Mode (Constant Current)

```python
# Set 2.5A constant current
load.write('MODE CC')
load.write('CURR 2.5')
load.write('INP ON')

# Read actual current
actual_i = float(load.query('MEAS:CURR?'))
print(f"Actual current: {actual_i:.3f}A")
```

### CV Mode (Constant Voltage)

```python
# Clamp at 3.6V (battery discharge cutoff)
load.write('MODE CV')
load.write('VOLT 3.6')
load.write('INP ON')
```

### CR Mode (Constant Resistance)

```python
# Set 10 ohm load
load.write('MODE CR')
load.write('RES 10')
load.write('INP ON')
```

### CP Mode (Constant Power)

```python
# Set 50W constant power
load.write('MODE CP')
load.write('POW 50')
load.write('INP ON')
```

---

## Dynamic Load (Pulse)

```python
# Square wave load: 1A ↔ 3A at 100 Hz, 50% duty
load.write('MODE CC')
load.write('CURR:DYN:L1 1.0')    # level 1
load.write('CURR:DYN:L2 3.0')    # level 2
load.write('CURR:DYN:FREQ 100')  # frequency
load.write('CURR:DYN:DUTY 50')   # duty cycle %
load.write('CURR:DYN ON')
load.write('INP ON')
```

---

## Battery Discharge Test

```python
import time, csv

load.write('MODE CC')
load.write('CURR 1.0')           # 1A discharge
load.write('VOLT:CUT 3.0')       # cutoff at 3.0V
load.write('CAP:CLE')             # clear capacity counter
load.write('BATT:TEST ON')
load.write('INP ON')

results = []
start = time.time()
while True:
    v = float(load.query('MEAS:VOLT?'))
    i = float(load.query('MEAS:CURR?'))
    ah = float(load.query('MEAS:CAP?'))
    wh = float(load.query('MEAS:ENER?'))
    
    results.append([time.time() - start, v, i, ah, wh])
    print(f"t={results[-1][0]:.0f}s  V={v:.3f}  Ah={ah:.3f}  Wh={wh:.2f}")
    
    if v <= 3.0:
        load.write('INP OFF')
        break
    time.sleep(1)

# Save to CSV
with open('battery_discharge.csv', 'w') as f:
    w = csv.writer(f)
    w.writerow(['Time_s', 'Voltage_V', 'Current_A', 'Capacity_Ah', 'Energy_Wh'])
    w.writerows(results)

print(f"Total capacity: {results[-1][3]:.3f} Ah, Energy: {results[-1][4]:.2f} Wh")
```

---

## Power Supply Load Regulation

```python
import numpy as np

load.write('MODE CC')
loads_ma = [0, 100, 250, 500, 750, 1000]
voltages = []

for current_ma in loads_ma:
    load.write(f'CURR {current_ma/1000:.3f}')
    load.write('INP ON')
    time.sleep(0.5)
    v = float(load.query('MEAS:VOLT?'))
    voltages.append(v)
    load.write('INP OFF')
    time.sleep(0.1)

# Calculate load regulation
v_no_load = voltages[0]
v_full_load = voltages[-1]
regulation_pct = (v_no_load - v_full_load) / v_full_load * 100
print(f"Load regulation: {regulation_pct:.3f}% ({v_no_load:.3f}V → {v_full_load:.3f}V)")
```

---

## Transient Response

```python
# 0A → 1A step, measure voltage dip
load.write('MODE CC')
load.write('CURR:DYN:L1 0.0')
load.write('CURR:DYN:L2 1.0')
load.write('CURR:DYN:FREQ 10')
load.write('CURR:DYN:DUTY 50')
load.write('CURR:DYN ON')
load.write('INP ON')

# Read Vmin/Vmax during transient
v_min = float(load.query('MEAS:VOLT:MIN?'))
v_max = float(load.query('MEAS:VOLT:MAX?'))
print(f"Vmax: {v_max:.3f}V, Vmin: {v_min:.3f}V, Dip: {(v_max-v_min)*1000:.1f}mV")
```

---

## Protections

```python
# Set protection limits
load.write('PROT:OVP 30')        # over-voltage protection 30V
load.write('PROT:OCP 15')        # over-current protection 15A
load.write('PROT:OPP 250')       # over-power protection 250W
load.write('PROT:OTP ON')        # over-temperature (auto)

# Check protection status
status = load.query('PROT:STAT?')
if 'OVP' in status:
    print("⚠ Over-voltage trip!")
```

---

## Prodigit 3310F Command Reference

| Command | Description | Example |
|---|---|---|
| `MODE <mode>` | Set mode: CC, CV, CR, CP | `MODE CC` |
| `CURR <A>` | Set current (CC mode) | `CURR 2.5` |
| `VOLT <V>` | Set voltage (CV mode) | `VOLT 5.0` |
| `RES <ohm>` | Set resistance (CR mode) | `RES 10` |
| `POW <W>` | Set power (CP mode) | `POW 50` |
| `INP ON/OFF` | Load on/off | `INP ON` |
| `MEAS:VOLT?` | Measure voltage | → `12.345` |
| `MEAS:CURR?` | Measure current | → `2.500` |
| `MEAS:POW?` | Measure power | → `30.86` |
| `MEAS:CAP?` | Capacity (Ah) | → `1.234` |
| `MEAS:ENER?` | Energy (Wh) | → `4.567` |
| `CURR:DYN:L1 <A>` | Dynamic load level 1 | `CURR:DYN:L1 1.0` |
| `CURR:DYN:L2 <A>` | Dynamic load level 2 | `CURR:DYN:L2 5.0` |
| `CURR:DYN:FREQ <Hz>` | Dynamic frequency | `CURR:DYN:FREQ 1000` |
| `CURR:DYN:DUTY <%>` | Dynamic duty cycle | `CURR:DYN:DUTY 50` |
| `CURR:DYN ON/OFF` | Dynamic mode on/off | `CURR:DYN ON` |
| `VOLT:CUT <V>` | Battery cutoff voltage | `VOLT:CUT 3.0` |
| `CAP:CLE` | Clear capacity counter | `CAP:CLE` |
| `BATT:TEST ON` | Battery test mode | `BATT:TEST ON` |
| `PROT:OVP <V>` | OV protection limit | `PROT:OVP 30` |
| `PROT:OCP <A>` | OC protection limit | `PROT:OCP 15` |
| `PROT:OPP <W>` | OP protection limit | `PROT:OPP 250` |
| `PROT:STAT?` | Protection status | → `NONE` |
| `*IDN?` | Identity | → `PRODIGIT,3310F,...` |

## Specifications

| Parameter | Rating |
|---|---|
| Max power | 300 W |
| Max voltage | 60 V |
| Max current | 60 A |
| CC range | 0-6A / 0-60A |
| CC resolution | 0.1 mA / 1 mA |
| CV range | 0-6V / 0-60V |
| CR range | 0.01Ω-10Ω / 10Ω-10kΩ |
| Dynamic freq | 0.1 Hz - 10 kHz |
| Slew rate | 0.001-2.5 A/μs |
| Min operating V | 0.8V @ 60A |

## Pro Tips

- **Low voltage operation**: below ~0.8V, the load can't sink full current. For single-cell battery testing, use a boost converter before the load or work within the SOA.
- **Temperature**: the 3310F derates above 40°C ambient. For sustained 300W, ensure forced air cooling.
- **Sense wires**: use remote sense (4-wire Kelvin) for accurate voltage measurement, especially at high currents where lead drop is significant.
- **Parallel operation**: two 3310F units can be paralleled for 600W. Set both to identical CC/CR settings.
- **GPIB option**: the 3310F with GPIB can share the bus with the N9000A CXA for coordinated PSU testing (load sweep + spectrum capture).
