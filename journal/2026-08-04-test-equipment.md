# 2026-08-04 — Test equipment: ADP2230, HackRF One, Red Pitaya

## What changed

Added software support for three lab instruments to the opencode-electronics stack.
The WSL toolchain now speaks to a mixed-signal scope, an SDR, and an FPGA-based measurement
platform — all through Python SDKs and SCPI.

## Instruments

| Instrument | Type | Access | SDK | Status |
|---|---|---|---|---|
| Digilent ADP2230 | Mixed-signal scope (100 MS/s, 55 MHz, 16-ch LA) | USB → usbipd → WSL | pydwf 1.1.19 | ✅ Working |
| HackRF One | SDR transceiver (1 MHz – 6 GHz, 20 MHz BW) | USB → usbipd → WSL | libhackrf 2023.01.1, python-hackrf 1.5.0.1 | ✅ Installed |
| Red Pitaya | FPGA platform (125 MS/s ADC, dual DAC) | TCP/IP (port 5025) | pyvisa 1.16.2, pyvisa-py 0.8.1, SoapySDR | ✅ Installed |

## Stack installed

### ADP2230
```bash
lsusb | grep Digilent      # 1443:6003 — already auto-attached via adp2230-attach
python3 -c "from pydwf import DwfLibrary; print(DwfLibrary().version)"
# → WaveForms SDK detected
```
- `pydwf` 1.1.19 ↔ WaveForms SDK
- Auto-attach script at `~/.local/bin/adp2230-attach`
- Capabilities: scope (2-ch, 100 MS/s), AWG (2-ch), logic analyzer (16-ch),
  pattern generator, network analyzer, impedance analyzer

### HackRF One
```bash
hackrf_info                   # lists firmware/serial when connected
SoapySDRUtil --find="hackrf"  # SoapySDR probe
```
- `hackrf` 2023.01.1 tools + `libhackrf0` + `libhackrf-dev`
- `python-hackrf` 1.5.0.1 from PyPI
- `SoapySDR` 0.8 with `libHackRFSupport.so` 0.3.4
- Also installed: `soapysdr0.8-module-rtlsdr`, `-airspy`, `-bladerf`, `-uhd`

### Red Pitaya
```bash
python3 -c "
import pyvisa
rm = pyvisa.ResourceManager('@py')
rp = rm.open_resource('TCPIP::192.168.1.100::5025::SOCKET')
print(rp.query('*IDN?'))
"
# → Red Pitaya,STEMlab 125-14,...
```
- `pyvisa` 1.16.2 + `pyvisa-py` 0.8.1 — pure Python SCPI (no NI-VISA required)
- `SoapySDR` 0.8 with `libRedPitaya.so` 0.1.1
- SCPI over TCP/IP port 5025

## Custom skills

Three new instrument skills created:

| Skill | Coverage |
|---|---|
| `adp2230-scope` | Scope capture, AWG, logic analyzer, pattern generator, Bode plots, protocol decode |
| `hackrf-sdr` | Spectrum analysis, IQ capture/replay, FM/GSM/GPS demod, SoapySDR access, gain tables |
| `redpitaya-scope` | SCPI oscilloscope, signal generator, spectrum analyzer, LCR meter, Bode via SoapySDR |

## SDR capabilities (bonus)

The `soapysdr-module-all` installation also brought in:
- **RTL-SDR** (rtlsdr) — cheap DVB-T dongle SDR, 24 MHz – 1.7 GHz
- **Airspy** — 24 MHz – 1.8 GHz, 10 MHz bandwidth
- **BladeRF** — 47 MHz – 6 GHz, full-duplex
- **UHD** (USRP) — Ettus Research, 70 MHz – 6 GHz
- **LimeSDR** — 100 kHz – 3.8 GHz, full-duplex

All accessible through the same SoapySDR Python API.

## Repo changes

- `skills/adp2230-scope/SKILL.md` — new
- `skills/hackrf-sdr/SKILL.md` — new
- `skills/redpitaya-scope/SKILL.md` — new
- `journal/2026-08-04-test-equipment.md` — this file

## Next steps

- [ ] Physical test: ADP2230 scope capture + AWG loopback
- [ ] Physical test: HackRF spectrum scan of FM band / 433 MHz ISM
- [ ] Physical test: Red Pitaya SCPI `*IDN?` over network
- [ ] MCP bridge candidates: `pydwf-mcp` (WaveForms), `hackrf-mcp` (SDR), `redpitaya-mcp` (SCPI)
