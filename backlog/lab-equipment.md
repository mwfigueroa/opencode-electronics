# Lab equipment — purchase candidates & status

Tracked gear for the electronics lab, with the integration angle (how OpenCode drives it).

## Status

| Instrument | State | Integration |
|---|---|---|
| Rigol DS1054Z (50 MHz, 4ch) | ✅ owned — software plumbing done, pending first physical connection | PyVISA/pyvisa-py (USBTMC via usbipd+libusb) or LAN SCPI `:5555`; sigrok `rigol-ds`. See journal 2026-08-02-rigol-ds1054z |
| Programmable DC PSU 30V/5A (×2?) | 🛒 evaluating — table below | sigrok `scpi-pps` / PyVISA / serial-mcp-server |

## PSU candidates (verified against sigrok supported-hardware list, 2026-08-02)

Requirement: 30V/5A, USB or Ethernet, agent-drivable from day one. Possibly two units.

| PSU | Output | Interface | ~USD | sigrok | Notes |
|---|---|---|---|---|---|
| **Korad KA3005P** | 30V/5A | USB + RS232 | 80–100 | ✅ `Korad KAxxxxP series` | Linear (low noise — good for analog/RF). No LAN. USB = embedded serial → also drivable by serial-mcp-server. Must be the **P** version. |
| **Rigol DP832A** | 3ch: 2× 30V/3A + 5V/3A | USB + LAN (LXI) + GPIB | 450–500 | ✅ `Rigol DP800 series` | Same ecosystem as the DS1054Z, best SCPI, native LAN (no usbipd). CH1+CH2 parallel ≈ 6A. 3 rails can replace two supplies. |
| **Riden RD6006** (RDTech RD) | 60V/6A | USB (+WiFi opt.) | 70–90 w/case | ✅ `RDTech RD series` | Switching — fine for digital/power, not for ripple-sensitive analog. Best power/$. |
| **Manson HCS-3202** | 32V/5A | USB | 150–180 | ✅ `Manson HCS-3xxx series` | Solid build quality. |
| **Hanmatek HM305P** | 30V/5A | USB | 60–70 | ✅ `Hanmatek HM305P` | Cheapest option; switching. |

### Recommendation summary

- **Budget path:** 2× Korad KA3005P (~USD 200) → symmetric ±15 V or redundancy; linear = quiet.
- **Automation path:** 1× Rigol DP832A → 3 independent rails, LAN-native LXI, same brand as the scope.
- **Power/$ path:** Riden RD6006 for digital/power work.

Argentina notes: all importable via courier; Korad also sold rebadged (Velleman/Tenma; RockSeed RS310P is the 30V/10A sibling). Decide → then wire it like the scope (journal procedure) and log a new entry.
