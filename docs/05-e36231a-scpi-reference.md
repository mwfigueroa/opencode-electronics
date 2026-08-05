# Keysight E36231A — Referencia Rápida SCPI

> Programmable DC Power Supply | 0-30V / 0-30A / 200W | LAN VXI-11 + USB USBTMC

---

## Identificación y Sistema

| Comando | Descripción |
|---|---|
| `*IDN?` | Identificación: fabricante, modelo, serial, firmware |
| `*RST` | Reset a valores de fábrica (salida OFF, V=0, I=min) |
| `*TST?` | Auto-test (0 = OK) |
| `*OPC` | Operation Complete (setea bit en ESR) |
| `*OPC?` | Devuelve 1 cuando operación pendiente termina |
| `*WAI` | Espera a que terminen comandos previos |
| `*CLS` | Limpia registros de status |
| `*ESE <n>` | Programa Event Status Enable register |
| `*ESE?` | Lee Event Status Enable register |
| `*ESR?` | Lee Event Status Register |
| `*SRE <n>` | Programa Service Request Enable register |
| `*SRE?` | Lee Service Request Enable register |
| `*STB?` | Lee Status Byte |
| `SYST:ERR?` | Lee y limpia un error de la cola (0 = sin errores) |
| `SYST:VERS?` | Versión SCPI (YYYY.V) |
| `SYST:BEEP` | Emite un beep |
| `SYST:KLOC ON\|OFF` | Bloquea/desbloquea panel frontal |

---

## Salida (Output)

| Comando | Descripción |
|---|---|
| `OUTP ON\|OFF` | Enciende/apaga la salida |
| `OUTP?` | Estado de la salida (0=OFF, 1=ON) |
| `OUTP:PROT:CLE` | Limpia protección de salida disparada |
| `OUTP:PROT:TRIP?` | ¿Saltó la protección? (0=no, 1=sí) |
| `OUTP:RES <ohm>` | Resistencia de salida programable (simulación batería) |
| `OUTP:RES?` | Lee resistencia de salida configurada |
| `OUTP:RES:STAT ON\|OFF` | Activa/desactiva resistencia de salida |
| `OUTP:REL ON\|OFF` | Modo relé: ON = relé cerrado (bajo ruido) |
| `OUTP:REL:POL NORM\|REV` | Polaridad del relé |

---

## Voltaje y Corriente (SOURCE)

| Comando | Descripción |
|---|---|
| `VOLT <V>` | Setea voltaje de salida (0-30V, resolución 1mV) |
| `VOLT?` | Lee setpoint de voltaje |
| `VOLT:TRIG <V>` | Voltaje para modo triggered |
| `CURR <A>` | Setea límite de corriente (0-30A, resolución 1mA) |
| `CURR?` | Lee setpoint de corriente |
| `CURR:TRIG <A>` | Corriente para modo triggered |
| `VOLT:RANG <V>` | Rango de voltaje (30V o 15V para mejor resolución) |
| `CURR:RANG <A>` | Rango de corriente (30A o 15A) |

---

## Mediciones (MEASure)

| Comando | Descripción |
|---|---|
| `MEAS:VOLT?` | Medición de voltaje (precisión 0.03% + 5mV) |
| `MEAS:VOLT? <rango>` | Medición con rango específico (ej: `MEAS:VOLT? 1.0V`) |
| `MEAS:CURR?` | Medición de corriente |
| `MEAS:CURR? <rango>` | Medición con rango específico |
| `MEAS:POW?` | ✅ Medición de potencia (V × I) |
| `MEAS:VOLT:AC?` | ❌ No soportado en firmware 1.0.6 |

---

## Protecciones

| Comando | Descripción |
|---|---|
| `VOLT:PROT <V>` | Setea nivel de OVP (Over-Voltage Protection) |
| `VOLT:PROT?` | Lee nivel OVP configurado |
| `VOLT:PROT:STAT ON\|OFF` | Activa/desactiva OVP |
| `VOLT:PROT:TRIP?` | ¿Disparó OVP? (0=no, 1=sí) |
| `VOLT:PROT:CLE` | Limpia disparo de OVP |
| `CURR:PROT <A>` | Setea nivel de OCP (Over-Current Protection) |
| `CURR:PROT?` | Lee nivel OCP configurado |
| `CURR:PROT:STAT ON\|OFF` | Activa/desactiva OCP |
| `CURR:PROT:TRIP?` | ¿Disparó OCP? |
| `CURR:PROT:CLE` | Limpia disparo de OCP |
| `CURR:PROT:DEL <s>` | Retardo de OCP (0-60s) |

---

## Trigger

| Comando | Descripción |
|---|---|
| `TRIG:SOUR BUS\|IMM` | Fuente de disparo: BUS (*TRG) o IMMediate |
| `TRIG:SOUR?` | Lee fuente de trigger actual |
| `*TRG` | Disparo manual (cuando TRIG:SOUR = BUS) |
| `INIT` | Inicia sistema de trigger |
| `INIT:CONT ON\|OFF` | Trigger continuo (ON) o single (OFF) |
| `ABOR` | Aborta operación en curso |

---

## Modo LIST (Secuencias Arbitrarias)

| Comando | Descripción |
|---|---|
| `LIST:VOLT <v1,v2,...>` | Define lista de voltajes (separados por coma) |
| `LIST:VOLT?` | Lee lista de voltajes actual |
| `LIST:VOLT:POIN?` | Número de puntos en la lista |
| `LIST:CURR <i1,i2,...>` | Define lista de corrientes |
| `LIST:DWEL <t>` | Tiempo por paso en segundos (ej: 0.01 = 10ms) |
| `LIST:DWEL?` | Lee dwell time |
| `LIST:STEP <t>` | Alternativa a DWEL (en algunos modelos AUTO por defecto) |
| `LIST:COUN <n>` | Repeticiones (1-65535, o INF) |
| `LIST:COUN?` | Lee contador de repeticiones |
| `LIST:TERM:LAST OFF` | Al terminar lista, mantiene último valor |

**Ejemplo**:
```python
psu.write('LIST:VOLT 5.0,10.0,0.0')   # 3 pasos
psu.write('LIST:DWEL 0.01')            # 10ms por paso
psu.write('LIST:COUN 3')               # repetir 3 veces
psu.write('TRIG:SOUR IMM')
psu.write('OUTP ON')
psu.write('INIT')
```

---

## Barrido / Data Logging (SENSe)

| Comando | Descripción |
|---|---|
| `SENS:SWE:POIN <n>` | Puntos de muestreo para barrido |
| `SENS:SWE:TINT <t>` | Intervalo entre muestras (segundos) |
| `SENS:SWE:OFFS:POIN <n>` | Puntos de offset antes de empezar |
| `INIT` | Inicia el barrido |
| `FETC:VOLT?` | Recupera array de voltajes medidos |
| `FETC:CURR?` | Recupera array de corrientes medidas |

---

## Display y Panel Frontal

| Comando | Descripción |
|---|---|
| `DISP ON\|OFF` | Enciende/apaga display |
| `DISP:VIEW METER\|TEXT` | Modo de display: numérico o texto |
| `DISP:TEXT "<msg>"` | Muestra mensaje en el display |

---

## Conexión (pyvisa)

```python
import pyvisa
rm = pyvisa.ResourceManager('@py')

# VXI-11 sobre LAN (recomendado)
psu = rm.open_resource('TCPIP::192.168.1.43::inst0::INSTR')

# Raw socket (puerto 5025)
psu = rm.open_resource('TCPIP::192.168.1.43::5025::SOCKET')

# USB USBTMC (requiere usbipd)
psu = rm.open_resource('USB0::0x2A8D::0x2202::MY59001234::INSTR')

psu.timeout = 5000
```

---

## Ejemplos Probados

### Setpoint y medición
```python
psu.write('VOLT 5.0')
psu.write('CURR 0.1')
psu.write('OUTP ON')
v = float(psu.query('MEAS:VOLT?'))  # 5.0006V
```

### Glitching entre 8.2V y 11.7V
```python
import random, time
V_MIN, V_MAX = 8.2, 11.7
while True:
    v = round(random.uniform(V_MIN, V_MAX), 3)
    psu.write(f'VOLT {v}')
    time.sleep(1.0)
```

### OVP y OCP
```python
psu.write('VOLT:PROT 5.5')
psu.write('VOLT:PROT:STAT ON')
psu.write('CURR:PROT 2.5')
psu.write('CURR:PROT:STAT ON')
if int(psu.query('VOLT:PROT:TRIP?')):
    psu.write('VOLT:PROT:CLE')
```

---

## Especificaciones

| Parámetro | Valor |
|---|---|
| Voltaje | 0-30 V, 1 mV resolución |
| Corriente | 0-30 A, 1 mA resolución |
| Potencia máxima | 200 W |
| Precisión V | 0.03% + 5 mV |
| Ripple & ruido | < 2 mVrms / 20 mVpp |
| Regulación de carga | < 0.01% + 2 mV |
| Respuesta transitoria | < 50 µs (50% load step) |
| Interfaces | LAN (VXI-11), USB (USBTMC) |
| IP actual | 192.168.1.43 |

---

> **Nota**: `MEAS:VOLT:AC?` (medición de ripple) no está implementado en firmware 1.0.6. Usar ADP2230 scope en AC coupling.
> **Nota**: El modo LIST requiere `LIST:STEP` o `LIST:DWEL` explícito; si queda en AUTO no ejecuta la secuencia.
