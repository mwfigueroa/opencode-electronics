# 2026-08-04 — Test equipment: full lab instrument stack

## What changed

Added software support for **six lab instruments** to the opencode-electronics stack.
The WSL toolchain now speaks to scopes, signal analyzers, power supplies, electronic loads,
SDRs, and FPGA platforms — all through Python SDKs and SCPI over TCP/IP, USB, and serial.

## Instruments

| Instrument | Type | Access | SDK | Status |
|---|---|---|---|---|
| Digilent ADP2230 | Mixed-signal scope (100 MS/s, 55 MHz, 16-ch LA) | USB → usbipd → WSL | pydwf 1.1.19 | ✅ Working |
| HackRF One | SDR transceiver (1 MHz – 6 GHz, 20 MHz BW) | USB → usbipd → WSL | libhackrf 2023.01.1, python-hackrf 1.5.0.1 | ✅ Installed |
| Red Pitaya | FPGA platform (125 MS/s ADC, dual DAC) | TCP/IP (port 5025) | pyvisa 1.16.2, pyvisa-py 0.8.1, SoapySDR | ✅ Installed |
| Keysight CXA N9000A | RF spectrum analyzer (9 kHz – 3/7.5 GHz) | LAN (VXI-11) / USB | pyvisa 1.16.2, pyvisa-py 0.8.1 | ✅ Installed |
| Prodigit 3310F | DC electronic load (300W/60V/60A) | RS-232 / USB-Serial | pyvisa + pyserial | ✅ Installed |
| Keysight E36231A | DC power supply (30V/30A/200W) | LAN (VXI-11) / USB | pyvisa 1.16.2, pyvisa-py 0.8.1 | ✅ Installed |

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

Six instrument skills created:

| Skill | Coverage |
|---|---|
| `adp2230-scope` | Scope capture, AWG, logic analyzer, pattern generator, Bode plots, protocol decode |
| `hackrf-sdr` | Spectrum analysis, IQ capture/replay, FM/GSM/GPS demod, SoapySDR access, gain tables |
| `redpitaya-scope` | SCPI oscilloscope, signal generator, spectrum analyzer, LCR meter, Bode via SoapySDR |
| `n9000a-cxa` | Phase noise, channel power, occupied BW, spurious mask, marker measurements, trace math |
| `prodigit-3310f` | CC/CV/CR/CP modes, dynamic load, battery discharge, load regulation, transient response |
| `e36231a-psu` | Precision sourcing, sequencing/arb waveform, battery simulation, OVP/OCP, remote sense |

## SCPI / pyvisa stack (shared by N9000A, Red Pitaya, E36231A, Prodigit)

```bash
python3 -c "
import pyvisa
rm = pyvisa.ResourceManager('@py')
print(rm.list_resources())
"
```
- `pyvisa` 1.16.2 + `pyvisa-py` 0.8.1 — pure Python VISA, no NI-VISA required
- Backends: TCPIP (VXI-11), USB (USBTMC), ASRL (serial)
- All instruments speak SCPI; same `pyvisa` code pattern across all four

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
- `skills/n9000a-cxa/SKILL.md` — new
- `skills/prodigit-3310f/SKILL.md` — new
- `skills/e36231a-psu/SKILL.md` — new
- `journal/2026-08-04-test-equipment.md` — this file

## Next steps

- [ ] Physical test: ADP2230 scope capture + AWG loopback
- [ ] Physical test: HackRF spectrum scan of FM band / 433 MHz ISM
- [ ] Physical test: Red Pitaya SCPI `*IDN?` over network
- [ ] Physical test: N9000A CXA spectrum capture + phase noise
- [ ] Physical test: Prodigit 3310F CC load sweep on E36231A
- [ ] Physical test: E36231A sequencing + OVP/OCP trip test
- [ ] MCP bridge candidates: `pydwf-mcp` (WaveForms), `hackrf-mcp` (SDR), `scpi-mcp` (generic SCPI for N9000A/E36231A/Red Pitaya/Prodigit)
