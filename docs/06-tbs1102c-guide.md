# Tektronix TBS1102C — Guía de Capacidades

> Osciloscopio digital 2 canales | 100 MHz BW | 1 GS/s | USB USBTMC

---

## Especificaciones

| Parámetro | Valor |
|---|---|
| **Ancho de banda** | 100 MHz |
| **Sample rate** | 1 GS/s (1 canal), 500 MS/s (2 canales) |
| **Canales** | 2 (CH1, CH2) |
| **Resolución vertical** | 8 bits |
| **Memoria** | 20 kpts por canal |
| **Timebase** | 2 ns/div a 100 s/div |
| **Rangos verticales** | 2 mV/div a 10 V/div |
| **Acoplamiento** | DC, AC, GND |
| **Impedancia entrada** | 1 MΩ ∥ 20 pF |
| **Pantalla** | 7" TFT color (800×480) |
| **Interfaces** | USB device (USBTMC), USB host (flash drive) |
| **Peso** | ~2 kg |
| **Alimentación** | 100-240V AC, 50/60 Hz |

---

## 1. Control Remoto (SCPI vía USBTMC)

### Conexión desde OpenCode

```python
import usbtmc

dev = usbtmc.list_devices()[0]
scope = usbtmc.Instrument(dev)
scope.timeout = 5.0

# Identificación
scope.ask('*IDN?')
# -> TEKTRONIX,TBS1102C,C025730,CF:91.1CT FV:v1.29.30; FPGA:v20.78;
```

### Stack completo

```
TBS1102C → USB-B → WinUSB (Zadig) → usbipd → WSL → python-usbtmc → SCPI
```

---

## 2. Comandos SCPI Probados

### Sistema

| Comando | Función | Estado |
|---|---|---|
| `*IDN?` | Identificación | ✅ |
| `*RST` | Reset | ✅ |
| `*OPC?` | Operation complete | ✅ |

### Horizontal (timebase)

| Comando | Función | Estado |
|---|---|---|
| `HORizontal:SCAle <s>` | Setear timebase (s/div) | ✅ |
| `HORizontal:SCAle?` | Leer timebase actual | ✅ |
| `HORizontal:MAIn:SAMPLERate?` | Leer sample rate | ❌ No implementado |
| `HORizontal:RECOrdlength?` | Leer longitud de registro | ❌ No implementado |
| `HORizontal:POSition <s>` | Posición horizontal | ✅ |
| `HORizontal:POSition?` | Leer posición | ✅ |

### Vertical (CH1/CH2)

| Comando | Función | Estado |
|---|---|---|
| `CH1:SCAle <V>` | Setear escala (V/div) | ✅ |
| `CH1:SCAle?` | Leer escala | ✅ |
| `CH1:POSition <div>` | Posición vertical | ✅ |
| `CH1:COUPling DC\|AC\|GND` | Acoplamiento | ✅ |
| `CH1:COUPling?` | Leer acoplamiento | ✅ |
| `CH1:BANdwidth?` | BW limit | ❌ |
| `CH1:PRObe?` | Factor de sonda | ❌ (string por defecto) |
| `CH1:PRObe <N>` | Setear factor sonda | ✅ |
| `SELect:CH1 ON\|OFF` | Activar/desactivar canal | ✅ |

### Trigger

| Comando | Función | Estado |
|---|---|---|
| `TRIGger:A:EDGE:SOUrce CH1` | Fuente de trigger | ✅ |
| `TRIGger:A:EDGE:SLOpe RISe\|FALL` | Flanco | ✅ |
| `TRIGger:A:LEVel <V>` | Nivel de trigger | ✅ |
| `TRIGger:A:LEVel?` | Leer nivel | ✅ |

### Adquisición

| Comando | Función | Estado |
|---|---|---|
| `ACQuire:MODe SAMple\|PEAKdetect\|AVErage` | Modo adquisición | ✅ |
| `ACQuire:NUMAVg <N>` | Promediado (2,4,8,16,32,64,128) | ✅ |
| `ACQuire:STOPAfter SEQuence\|RUNSTop` | Modo parada | ✅ |

### Mediciones Automáticas

| Comando | Función | Valor Probado |
|---|---|---|
| `MEASUrement:IMMed:SOUrce CH1` | Seleccionar fuente | ✅ |
| `MEASUrement:IMMed:TYPe FREQuency` | Frecuencia | ✅ 10.016 kHz |
| `MEASUrement:IMMed:TYPe PERIod` | Período | ✅ 100.16 µs |
| `MEASUrement:IMMed:TYPe PK2pk` | Pico a pico | ✅ 2.0 V |
| `MEASUrement:IMMed:TYPe CRMs` | RMS cíclico | ✅ 1.397 V |
| `MEASUrement:IMMed:TYPe MINImum` | Mínimo | ✅ -1.0 V |
| `MEASUrement:IMMed:TYPe MAXImum` | Máximo | ✅ +1.0 V |
| `MEASUrement:IMMed:TYPe MEAN` | Media | ✅ +33 mV |
| `MEASUrement:IMMed:VALue?` | Leer valor | ✅ |

### Tipos de medición disponibles

| Tipo | Descripción |
|---|---|
| `FREQuency` | Frecuencia de la señal |
| `PERIod` | Período |
| `PK2pk` | Pico a pico |
| `CRMs` | RMS cíclico (true RMS sobre un ciclo entero) |
| `MINImum` | Valor mínimo |
| `MAXImum` | Valor máximo |
| `MEAN` | Valor medio |
| `AMPlitude` | Amplitud |
| `RISe` | Tiempo de subida (10%-90%) |
| `FALL` | Tiempo de bajada (90%-10%) |
| `PWIDth` | Ancho de pulso positivo |
| `NWIDth` | Ancho de pulso negativo |
| `PDUTy` | Duty cycle positivo |
| `NDUTy` | Duty cycle negativo |
| `OVERshoot` | Overshoot positivo |
| `PREShoot` | Preshoot |

### Forma de Onda

| Comando | Función | Estado |
|---|---|---|
| `DATa:SOUrce CH1` | Seleccionar fuente de datos | ✅ |
| `DATa:ENCdg ASCii\|RIBINARY` | Formato de datos | ✅ |
| `DATa:WIDth 1\|2` | Bytes por muestra (1=8bit, 2=16bit) | ✅ |
| `DATa:STARt <N>` | Primera muestra | ✅ |
| `DATa:STOP <N>` | Última muestra | ✅ |
| `WFMOutpre:YZEro?` | Offset vertical | ✅ |
| `WFMOutpre:YMUlt?` | Escala vertical (V/div a V/cuenta) | ✅ |
| `WFMOutpre:XINcr?` | Intervalo entre muestras (s) | ✅ |
| `CURVe?` | Capturar forma de onda | ⬜ Pendiente probar |

### Display

| Comando | Función |
|---|---|
| `DISplay:PERSistence <s>` | Persistencia (0=solo trigger) |
| `DISPlay:FORMat YT\|XY` | Modo display (YT normal, XY para Lissajous) |

### Autoset

| Comando | Función |
|---|---|
| `AUTOSet EXECute` | ✅ Auto-ajuste de escalas, timebase y trigger |

---

## 3. Modos de Operación

### Modo YT (normal)

Visualización clásica: voltaje vs tiempo. Usado para:
- Señales periódicas (senoidales, cuadradas, pulsos)
- Eventos transitorios
- Análisis de timing, glitches, runt pulses

### Modo XY (Lissajous)

CH1 = eje X, CH2 = eje Y. Usado para:
- Curvas de Lissajous (comparación de fase/frecuencia)
- Curvas I-V de componentes (con sonda de corriente)
- Diagramas de ojo con persistencia

### Modos de adquisición

| Modo | Uso |
|---|---|
| **Sample** | Muestreo normal, máxima fidelidad para señales > sample rate |
| **Peak Detect** | Detecta glitches estrechos (hasta 1 ns) incluso con timebase lento |
| **Average** | Reduce ruido aleatorio promediando múltiples capturas (2-128) |

---

## 4. Capacidades de Medición

### Mediciones automáticas (hasta 6 simultáneas)

El TBS1102C muestra hasta 6 mediciones en pantalla simultáneamente, actualizadas en tiempo real. Desde SCPI se puede leer cualquier medición bajo demanda.

### Cursores

Dos cursores (horizontal y vertical) para mediciones manuales:
- ΔV entre cursores
- Δt entre cursores  
- 1/Δt (frecuencia)

### FFT (Math)

La serie TBS1000C incluye FFT básico:
- CH1 o CH2 como fuente
- Ventanas: Hanning, Hamming, Blackman-Harris, Rectangular
- Escalas: dBV RMS, lineal RMS

### Límites / Máscaras (Pass/Fail)

- Definir máscaras de tolerancia
- Comparar señal adquirida contra máscara
- Contador de fallos
- Acción al fallar: stop, beep, pulso de salida, guardar pantalla

---

## 5. Almacenamiento y Exportación

### USB Host (pendrive)

- Guardar capturas de pantalla (PNG, BMP, JPG)
- Guardar formas de onda (CSV, ISF interno)
- Guardar/recuperar configuraciones (SET)
- Actualizar firmware desde USB

### Control Remoto (USBTMC)

- Captura de formas de onda vía `CURVe?`
- Lectura de mediciones automáticas
- Configuración completa del instrumento
- Automatización de tests

---

## 6. Casos de Uso desde OpenCode

### Verificación de señales (cross-instrument)

```
ADP2230 (genera) → TBS1102C (mide y verifica)
```

Ya probado: generar senoidal 10 kHz / 2 Vpp y verificar frecuencia, Vpp, Vrms, Vmin, Vmax.

### Barrido de frecuencia manual

```python
for freq in [1000, 5000, 10000, 50000, 100000]:
    awg_generate(freq, 1.0)        # ADP2230
    tbs.write('AUTOSet EXECute')
    time.sleep(1)
    vpp = tbs.ask('MEASUrement:IMMed:VALue?')
    print(f'{freq} Hz -> {vpp} Vpp')
```

### Test de respuesta en frecuencia de un DUT

```
ADP2230 → DUT → TBS1102C
```

Generar barrido con ADP2230, medir amplitud de salida con TBS a cada frecuencia. Resultado: respuesta en frecuencia (similar a Bode plot pero con mediciones Vpp en vez de fase).

### Power sequence timing

```
E36231A (rampa de voltaje) → TBS1102C (trigger + medición de rise time)
```

### Glitch detection

Modo Peak Detect a timebase lento para capturar pulsos estrechos.

---

## 7. Limitaciones vs Modelos Superiores

| Característica | TBS1102C | MSO/DPO 2000+ |
|---|---|---|
| Memoria | 20 kpts | 1 Mpts+ |
| Sample rate | 1 GS/s | 2 GS/s+ |
| Canales | 2 | 2-4 |
| Decodificación serial | ❌ No | ✅ I2C, SPI, UART, CAN, LIN |
| Trigger avanzado | Solo edge | Edge, pulse width, runt, logic, setup/hold, video |
| FFT | Básico | Avanzado (más puntos, mejor resolución) |
| SCPI completo | Subset limitado | Completo |
| Ethernet/LAN | ❌ No | ✅ Sí (en algunos modelos) |
| Bode plot integrado | ❌ No | ✅ (con AWG interno) |

---

## 8. Conexión Física

| Conector | Panel | Función |
|---|---|---|
| **CH1, CH2** | Frontal | Entradas BNC (1 MΩ) |
| **EXT TRIG** | Frontal | Trigger externo (BNC) |
| **USB Device** | Trasero | Control remoto USBTMC (tipo B) |
| **USB Host** | Frontal | Pendrive para screenshots/CSV |
| **Probe Comp** | Frontal | Salida calibración 1 kHz / 5V |

---

## 9. Soporte en OpenCode

| Capa | Estado |
|---|---|
| **Driver Windows** | ✅ WinUSB vía Zadig |
| **Forwarding WSL** | ✅ usbipd |
| **Librería Python** | ✅ python-usbtmc 0.8 |
| **SCPI básico** | ✅ *IDN?, *RST, configuración |
| **Mediciones automáticas** | ✅ 15 tipos |
| **AUTOSET** | ✅ |
| **Captura forma de onda** | ⬜ Pendiente testear CURVe? |
| **FFT remoto** | ⬜ Pendiente |
| **Pass/Fail remoto** | ⬜ Pendiente |
| **Actualizar README** | ✅ |
