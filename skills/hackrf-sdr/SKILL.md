---
name: hackrf-sdr
description: "(oh-my-embedded) HackRF One SDR transceiver (1 MHz - 6 GHz). Use for spectrum analysis, signal capture, replay attacks, GPS/GNSS, GSM/LTE analysis. Requires hackrf-tools + python-hackrf."
---

# HackRF One SDR Skill

HackRF One — half-duplex SDR transceiver, 1 MHz to 6 GHz, up to 20 MHz bandwidth, 8-bit ADC.

---

## Setup

### Prerequisites (installed)

- `hackrf` package (libhackrf 2023.01.1, hackrf-tools)
- `python-hackrf` 1.5.0.1
- `SoapySDR` 0.8 with `libHackRFSupport.so` 0.3.4
- `soapysdr0.8-module-hackrf`

### Verify

```bash
hackrf_info                    # lists serial, firmware, part
SoapySDRUtil --find="hackrf"   # SoapySDR probe
```

### Connect via usbipd

```bash
# Windows side:
usbipd list                          # find BUSID for HackRF (VID:1d50 PID:6089/604b)
usbipd bind --busid <X-Y>
usbipd attach --wsl --busid <X-Y>
```

---

## Spectrum Analysis

### Quick CLI sweep

```bash
# Sweep 88-108 MHz (FM band), 2 MHz bandwidth, 1M FFT bins, 100ms integration
hackrf_sweep -f 88:108 -w 2000000 -N 1048576 -l 32 -g 40
```

### Python spectrum analyzer

```python
from hackrf import HackRF
import numpy as np

hackrf = HackRF()
hackrf.sample_rate = 20e6
hackrf.center_freq = 100e6      # 100 MHz
hackrf.lna_gain = 32
hackrf.vga_gain = 30

samples = hackrf.read_samples(2**20)  # ~52 ms at 20 MS/s

# FFT
spectrum = np.abs(np.fft.fft(samples[:1024*1024]))**2
freqs = np.fft.fftfreq(len(spectrum), 1/20e6)
peak_freq = freqs[np.argmax(spectrum[1:])+1]
print(f"Peak at {peak_freq/1e6:.3f} MHz")
```

### SoapySDR spectrum analyzer (supports HackRF + Red Pitaya)

```python
import numpy as np
import SoapySDR
from SoapySDR import SOAPY_SDR_RX, SOAPY_SDR_CF32

sdr = SoapySDR.Device(dict(driver="hackrf"))
sdr.setSampleRate(SOAPY_SDR_RX, 0, 8e6)
sdr.setFrequency(SOAPY_SDR_RX, 0, 433.92e6)
sdr.setGain(SOAPY_SDR_RX, 0, 40)

rx_stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(rx_stream)

buff = np.zeros(2**18, np.complex64)
sr = sdr.readStream(rx_stream, [buff], len(buff))
sdr.deactivateStream(rx_stream)

spectrum = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(buff))))
```

---

## Signal Capture / Record

```bash
# Record 10s of IQ data at 10 MS/s centered at 433.92 MHz
hackrf_transfer -r capture.iq -f 433920000 -s 10000000 -n 100000000 -g 40 -l 32

# Replay captured IQ data
hackrf_transfer -t capture.iq -f 433920000 -s 10000000 -a 1 -x 47
```

---

## Common Use Cases

### FM radio demod
```bash
hackrf_transfer -r - -f 100100000 -s 2000000 -g 40 -l 32 | \
  csdr convert_u8_f | csdr fmdemod_quadri | csdr convert_f_s16 | \
  aplay -r 32000 -f S16_LE -t raw -c 1
```

### GPS L1 capture (1575.42 MHz)
```bash
hackrf_transfer -r gps_l1.iq -f 1575420000 -s 4000000 -n 40000000 -g 40
```

### GSM 900 downlink scan
```python
for freq in range(935_200_000, 960_000_000, 200_000):
    hackrf.center_freq = freq
    samples = hackrf.read_samples(2**18)
    rssi = 10 * np.log10(np.mean(np.abs(samples)**2))
    if rssi > -60:
        print(f"GSM ARFCN {freq//200e3:.0f}: RSSI {rssi:.1f} dB")
```

---

## Key Parameters

| Parameter | Range | Notes |
|---|---|---|
| Frequency | 1 MHz - 6 GHz | TX limited to 10 MHz - 6 GHz for some revs |
| Sample rate | 2 - 20 MS/s | Higher = more BW, more USB bandwidth |
| LNA gain | 0 - 40 dB | 8 dB steps |
| VGA gain | 0 - 62 dB | 2 dB steps |
| TX VGA gain | 0 - 47 dB | 1 dB steps |
| Bandwidth | 1.75 - 28 MHz | Baseband filter |

### Gain recommendations
| Use case | LNA | VGA |
|---|---|---|
| Strong signal (< -40 dBm) | 0-8 dB | 20-30 dB |
| Medium signal (-60 to -40 dBm) | 16-24 dB | 30-40 dB |
| Weak signal (< -60 dBm) | 32-40 dB | 40-50 dB |

---

## Pro Tips

- **USB bandwidth**: 20 MS/s × 8 bits × 2 (IQ) = 40 MB/s. Use USB 3.0 ports.
- **DC offset**: HackRF has a noticeable DC spike at center frequency. Use offset tuning or post-process with DC removal.
- **TX amplifier**: TX power is ~10 dBm max. For longer range, use an external PA.
- **Antenna**: stock ANT500 covers 75 MHz - 1 GHz. For 2.4 GHz ISM use a dedicated antenna.
- **Clock sync**: for coherent multi-device operation, use the CLKIN/CLKOUT SMA ports.
