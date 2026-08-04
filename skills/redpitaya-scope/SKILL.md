---
name: redpitaya-scope
description: "(oh-my-embedded) Red Pitaya FPGA-based measurement platform. Use for oscilloscope, signal generator, spectrum analyzer, SCPI instruments, PID controller. Access via SCPI over TCP/IP (pyvisa-py) or SoapySDR."
---

# Red Pitaya Instrument Skill

Red Pitaya — FPGA-based measurement platform. Dual 125 MS/s ADC (14-bit), dual 125 MS/s DAC, Linux on Zynq-7010/7020.

---

## Setup

### Prerequisites (installed)

- `pyvisa` 1.16.2 + `pyvisa-py` 0.8.1 — SCPI over TCP/IP (no NI-VISA needed)
- `SoapySDR` 0.8 with `libRedPitaya.so` 0.1.1 — SDR access
- `scipy`, `numpy` — signal processing

### Default network

- Red Pitaya IP: `192.168.1.100` (default) or check DHCP lease
- SCPI port: `5025` (standard), `5026` for second app
- SSH: port 22 (user: `root`, pass: `changeme`)

### Verify connection

```bash
# Ping test
ping -c 3 192.168.1.100

# SCPI test
python3 -c "
import pyvisa
rm = pyvisa.ResourceManager('@py')
rp = rm.open_resource('TCPIP::192.168.1.100::5025::SOCKET')
print(rp.query('*IDN?'))
"
# → Red Pitaya,STEMlab 125-14,...
```

---

## Oscilloscope (SCPI)

```python
import pyvisa
import numpy as np

rm = pyvisa.ResourceManager('@py')
rp = rm.open_resource('TCPIP::192.168.1.100::5025::SOCKET')
rp.timeout = 5000

# Configure channel 1
rp.write('ACQ:RST')
rp.write('ACQ:DEC 1')             # decimation 1 = 125 MS/s

# Set trigger
rp.write('ACQ:TRig:LEV 0.5')
rp.write('ACQ:TRig:DLY 8192')     # pre-trigger samples

# Start acquisition
rp.write('ACQ:START')
rp.write('ACQ:TRig NOW')          # force trigger

# Wait for trigger
while True:
    rp.write('ACQ:TRig:STAT?')
    if rp.read().strip() == 'TD':
        break

# Read data
rp.write('ACQ:SOURce:DATA:units VOLTS')
rp.write('ACQ:SOURce:DATA:SIZE?')
size = int(rp.read().strip())

rp.write('ACQ:SOURce 1')          # channel 1
rp.write('ACQ:SOURce:DATA:STA:END? 0,' + str(size-1))
raw = rp.read_raw()

data = np.frombuffer(raw, dtype=np.float32)
print(f"Channel 1: {len(data)} samples, {data.min():.3f}V to {data.max():.3f}V, P-P: {np.ptp(data):.3f}V")
```

---

## Signal Generator (SCPI)

```python
# Channel 1: 1 kHz sine, 1Vpp, 0V offset
rp.write('SOURce1:FUNCtion SINE')
rp.write('SOURce1:FREQuency:FIXed 1000')
rp.write('SOURce1:VOLTage 1.0')
rp.write('SOURce1:VOLTage:OFFset 0.0')
rp.write('OUTPUT1:STATe ON')
```

### Waveform types
```
SINE, SQUARE, TRIANGLE, SAWU (ramp up), SAWD (ramp down),
PWM, ARBITRARY, DC, NOISE, SWEEP
```

### Sweep mode
```python
rp.write('SOURce1:FUNCtion SWEEP')
rp.write('SOURce1:SWEep:STARt 1000')     # 1 kHz start
rp.write('SOURce1:SWEep:STOP 10000000')   # 10 MHz stop
rp.write('SOURce1:SWEep:TIME 5')          # 5 second sweep
```

---

## Spectrum Analyzer

```python
rp.write('SPECT:RST')
rp.write('SPECT:SPAN 10000000')            # 10 MHz span
rp.write('SPECT:CFREQ 50000000')           # center at 50 MHz
rp.write('SPECT:BANDWIDTH 30000')          # 30 kHz RBW

rp.write('SPECT:START')
while True:
    rp.write('SPECT:STATUS?')
    if rp.read().strip() == 'Done':
        break

rp.write('SPECT:DATA:SIZE?')
size = int(rp.read().strip())

rp.write('SPECT:DATA:UNITS dBm')
rp.write(f'SPECT:DATA:STA:END? 0,{size-1}')
raw = rp.read_raw()
spectrum = np.frombuffer(raw, dtype=np.float32)
freqs = np.linspace(50e6 - 5e6, 50e6 + 5e6, len(spectrum))
peak_idx = np.argmax(spectrum)
print(f"Peak: {spectrum[peak_idx]:.1f} dBm at {freqs[peak_idx]/1e6:.3f} MHz")
```

---

## LCR / Impedance Meter

```python
# Uses the LCR meter app (app #5 on the Red Pitaya marketplace)
# SCPI port: 5025 (if LCR app is active)

rp.write('LCR:RST')
rp.write('LCR:FUNCtion CsRs')        # Capacitance (series model)
rp.write('LCR:FREQuency 10000')      # 10 kHz test frequency
rp.write('LCR:MEASure')
rp.write('LCR:DATA?')
data = rp.read().strip()
# Format: "Cs,Rs" in farads and ohms
```

---

## Bode Analyzer (SoapySDR approach)

```python
import SoapySDR
from SoapySDR import SOAPY_SDR_RX, SOAPY_SDR_TX, SOAPY_SDR_CF32
import numpy as np

sdr = SoapySDR.Device(dict(driver="redpitaya"))

freqs = np.logspace(3, 7, 50)  # 1 kHz to 10 MHz, 50 points
gains = []
phases = []

for f in freqs:
    # Set TX to generate tone
    sdr.setFrequency(SOAPY_SDR_TX, 0, f)
    
    # Read RX
    rx_stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
    sdr.activateStream(rx_stream)
    buff = np.zeros(8192, np.complex64)
    sdr.readStream(rx_stream, [buff], len(buff))
    sdr.deactivateStream(rx_stream)
    
    # Measure amplitude and phase at f
    fft = np.fft.fft(buff)
    idx = int(f / (125e6/8192))
    gains.append(20 * np.log10(np.abs(fft[idx])))
    phases.append(np.angle(fft[idx], deg=True))

# Plot: frequency vs gain+phase
```

---

## SoapySDR Access (Red Pitaya as SDR)

```python
import SoapySDR
from SoapySDR import SOAPY_SDR_RX

sdr = SoapySDR.Device({
    "driver": "redpitaya",
    "addr": "192.168.1.100:1001"
})

# Available rates: depends on SCPI server
rates = sdr.getSampleRateRange(SOAPY_SDR_RX, 0)
print(f"Sample rates: {rates.minimum()} to {rates.maximum()} Hz")
print(f"Freq range: {sdr.getFrequencyRange(SOAPY_SDR_RX, 0)[0]} to {sdr.getFrequencyRange(SOAPY_SDR_RX, 0)[1]}")

sdr.setSampleRate(SOAPY_SDR_RX, 0, 1.5625e6)
sdr.setFrequency(SOAPY_SDR_RX, 0, 10e6)
sdr.setGain(SOAPY_SDR_RX, 0, 10)

rx = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(rx)
buff = np.zeros(4096, np.complex64)
sdr.readStream(rx, [buff], len(buff))
sdr.deactivateStream(rx)
```

---

## SCPI Command Quick Reference

| Command | Action |
|---|---|
| `*IDN?` | Device identification |
| `ACQ:RST` | Reset acquisition |
| `ACQ:DEC <n>` | Decimation (1 = 125 MS/s, 8 = 15.6 MS/s, ...) |
| `ACQ:AVG <on/off>` | Averaging |
| `ACQ:TRig:LEV <V>` | Trigger level |
| `SOUR<n>:FUNCtion <type>` | Generator waveform |
| `SOUR<n>:FREQuency:FIXed <Hz>` | Generator frequency |
| `SOUR<n>:VOLTage <Vpp>` | Generator amplitude |
| `OUTPUT<n>:STATe <ON/OFF>` | Generator output enable |
| `DIG:PIN <pin>,<dir>` | GPIO pin direction |
| `DIG:PIN? <pin>` | GPIO pin read |

---

## Pro Tips

- **SPI/I2C decoding**: Red Pitaya has dedicated digital I/O — use `DIG:PIN` commands + Python for protocol decoding
- **PID controller**: the FPGA implements a hardware PID loop. Use the SCPI API to set P/I/D gains and read feedback
- **Multiple apps**: different apps run on different ports. Web UI shows which app is active
- **External clock**: use the REF input for 10 MHz reference from a GPSDO for precision frequency measurements
- **Streaming**: for continuous data, use the SoapySDR interface instead of SCPI — it handles buffering automatically
- **Default apps**: `rp-scpi` (default on port 5025), `rp-scpi-lab` (full lab, port 5025), `rp-scpi-lcr` (port 5025 when LCR loaded)
