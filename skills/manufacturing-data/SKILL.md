---
name: manufacturing-data
description: "(oh-my-embedded) Automatically extract BOM, cavity tables, and wiring/harness data from a KiCad project using engineering context. Use for generating manufacturing-ready output files: BOM.csv, cavity_table.csv, wire_harness.csv. Triggers on BOM, cavity, connector, cable, wiring, harness, manufacturing data."
---

# Manufacturing Data Extraction Skill

Extract three manufacturing-ready outputs from a KiCad project:
1. **BOM** — bill of materials with sourcing metadata
2. **Cavity table** — connectors and their mechanical positions
3. **Wire harness** — netlist cross-referenced with connectors

---

## Workflow

### Step 1: Locate the project

Find the `.kicad_pro` file. Identify the root `.kicad_sch` and `.kicad_pcb`.

### Step 2: Export BOM

Run via kicad-cli or MCP tool:

```
kicad-mcp_export_bom → CSV format, grouped by value
```

Include custom fields: `MPN`, `Manufacturer`, `LCSC`, `DigiKey_PN`, `Voltage`, `Tolerance`, `Package`.

**Validation checks on the BOM:**
- Every component has a footprint (flag empty footprints)
- Every IC has decoupling caps within ~10mm (check against PCB layout)
- LCSC/DigiKey fields populated or flag as "needs sourcing"
- Voltage ratings of capacitors ≥ 2× the rail they sit on
- No duplicate references

### Step 3: Extract cavity table (connectors)

Connectors are identified by footprint pattern and reference prefix:
- **Footprint patterns:** `*Connector*`, `*PinHeader*`, `*PinSocket*`, `*USB*`, `*RJ45*`, `*TerminalBlock*`, `*FPC*`, `*FFC*`, `*JST*`, `*Molex*`
- **Reference prefixes:** `J*`, `P*`, `CONN*`

Use `kicad-mcp_get_component_list` to list all components, then filter.

For each connector, use `kicad-mcp_get_component_properties` to get:
- Position (x, y, rotation)
- Layer (F.Cu = top, B.Cu = bottom)
- Footprint name

Then use `kicad-mcp_get_component_pads` to get pin-to-net mapping.

**Output format (cavity_table.csv):**
```csv
Ref,Footprint,X_mm,Y_mm,Rotation,Side,PinCount,NetList,MatingSuggest
J1,Molex_43045-0400,5.0,0.0,0,Top,4,+5V/GND/SDA/SCL,43025-0400
J2,USB_C_Receptacle_USB2.0,50.0,12.0,90,Top,16,VBUS/DN/DP/GND,USB-C Plug
J3,PinHeader_2.54mm_1x06,80.0,0.0,180,Top,6,SWDIO/SWCLK/3V3/GND/RST/SWO,TAG-CONNECT-6
```

### Step 4: Extract netlist

```
kicad_extract_schematic_netlist
```

Build a `{net_name: [(ref, pin), ...]}` map.

### Step 5: Cross-reference → wire harness

Cross the cavity table (step 3) with the netlist (step 4):

For each connector pin that has a net assigned:
- Find the **other end** of that net (component + pin on the other connector)
- Group by signal type:
  - **Power:** `+5V`, `+3V3`, `VCC`, `VBUS`, `VBAT` → thicker gauge recommendation
  - **Differential:** nets ending in `_P`/`_N`, `DP`/`DN` → twisted pair
  - **Single-ended:** everything else
  - **GND:** `GND`, `DGND`, `AGND`

**Output format (wire_harness.csv):**
```csv
WireID,FromRef,FromPin,ToRef,ToPin,NetName,SignalType,GaugeAWG,LengthEst_mm,Notes
W1,J1,1,J2,1,+5V,Power,22,65,Twisted with GND
W2,J1,2,J2,8,GND,Power,22,65,Twisted with +5V
W3,J1,3,J2,5,SDA,Signal,28,65,I2C — keep away from power
W4,J1,4,J2,6,SCL,Signal,28,65,I2C — keep away from power
```

**Wire gauge defaults:**
| Signal type | AWG |
|---|---|
| Power > 1A | 18-20 |
| Power 0.5-1A | 22 |
| Power < 0.5A | 24 |
| Signal | 28 |
| Differential | 28 (twisted pair) |

### Step 6: Mechanical context

For each cavity, check:
- Is it on the board edge? (distance to Edge.Cuts < 5mm = accessible)
- Is there mechanical interference? (check courtyard overlap with other connectors)
- Are mounting holes nearby? (M2/M3 holes within 10mm = panel-mount candidate)

Tools: `kicad-mcp_get_board_extents`, `kicad-mcp_check_courtyard_overlaps`

### Step 7: Report

Produce a markdown report:

1. **Project info** (name, KiCad version, file inventory)
2. **BOM summary** (total components, unique parts, top categories, cost estimate if LCSC data available)
3. **Cavity table** (all connectors with positions, sides, pin counts)
4. **Wire harness** (all inter-connector nets, gauges, lengths)
5. **Manufacturing notes** (board edge connectors, mounting holes, keepouts)
6. **Files generated** (BOM.csv, cavity_table.csv, wire_harness.csv)
7. **Action items** (missing footprints, missing MPN, signals needing impedance control)

Save outputs to a `manufacturing/` subdirectory in the project root.

---

## Notes

- Connector mating suggestions are best-effort from footprint name parsing. Flag with `?` if uncertain.
- Wire lengths are Manhattan distance between connector centers × 1.3 (routing factor). Real harness lengths need mechanical CAD.
- For differential pairs, note the required impedance (typically 90Ω for USB, 100Ω for Ethernet).
- Power nets crossing analog sections: flag with warning.
