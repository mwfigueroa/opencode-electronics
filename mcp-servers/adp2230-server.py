#!/usr/bin/env python3
"""
MCP Server for Digilent Analog Discovery Pro ADP2230.
Exposes oscilloscope, AWG, logic analyzer, pattern generator, and FFT tools.
Uses pydwf (WaveForms SDK wrapper). Requires WaveForms 3.x installed.
"""

import time
import json
import numpy as np
from typing import Optional

from pydwf import (
    DwfLibrary,
    DwfAcquisitionMode,
    DwfTriggerSource,
    DwfTriggerSlope,
    DwfState,
    DwfAnalogOutFunction,
    DwfAnalogOutNode,
    DwfAnalogOutIdle,
    DwfAnalogImpedance,
    DwfAnalogIO,
    DwfDigitalInSampleMode,
    DwfDigitalInClockSource,
    DwfDigitalOutOutput,
    DwfDigitalOutType,
    DwfDigitalOutIdle,
)
from pydwf.utilities import openDwfDevice

from fastmcp import FastMCP

mcp = FastMCP("ADP2230")

# ─── helpers ────────────────────────────────────────────────────────────────

import threading

_dwf = DwfLibrary()
_device = None
_device_lock = threading.Lock()


class _PersistentDevice:
    """Wraps a DwfDevice in a context manager that never closes it.
    
    This keeps the device alive across tool calls, so AWG and
    pattern generator outputs persist after the tool returns.
    """
    def __init__(self, device):
        self._device = device
    
    def __enter__(self):
        return self._device
    
    def __exit__(self, *args):
        pass  # Never close — device stays alive for MCP lifetime


def _get_device():
    """Get or create a persistent ADP2230 device connection.
    
    Returns a context manager that provides the device but never
    closes it, so AWG/pattern generator keep running.
    """
    global _device
    if _device is None:
        with _device_lock:
            if _device is None:
                ctx = openDwfDevice(_dwf)
                _device = ctx.__enter__()
    return _PersistentDevice(_device)


def _wait_acquisition(ain, timeout_s: float = 5.0) -> bool:
    """Poll until acquisition is done or timeout."""
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        st = ain.status(True)
        if st == DwfState.Done:           # pydwf 1.1.x returns enum, not int
            return True
        time.sleep(0.005)
    return False


def _linear_spectrum(samples, fs: float):
    """Compute linear magnitude spectrum (V RMS) and frequency axis."""
    n = len(samples)
    window = np.hanning(n)
    fft = np.fft.rfft(samples * window)
    mag = np.abs(fft) / n * 2  # single-sided amplitude
    mag[0] /= 2  # DC bin
    freqs = np.fft.rfftfreq(n, 1.0 / fs)
    return freqs, mag


# ─── device info ────────────────────────────────────────────────────────────

@mcp.tool()
def adp2230_info() -> dict:
    """Get ADP2230 device information: name, serial number, and WaveForms version."""
    de = _dwf.deviceEnum
    de.enumerateDevices()
    name = de.deviceName(0)
    try:
        sn = de.serialNumber(0)
    except Exception:
        sn = "N/A"
    return {
        "device_name": name,
        "serial": sn,
        "connected": True,
    }


# ─── oscilloscope ───────────────────────────────────────────────────────────

@mcp.tool()
def oscilloscope_capture(
    channel: int = 1,
    sample_rate_hz: float = 1_000_000.0,
    buffer_size: int = 4096,
    voltage_range_v: float = 5.0,
    offset_v: float = 0.0,
    trigger_source: str = "none",
    trigger_channel: int = 1,
    trigger_level_v: float = 0.0,
    trigger_slope: str = "rise",
    timeout_s: float = 5.0,
) -> dict:
    """Capture a single acquisition from the ADP2230 oscilloscope.

    Args:
        channel: Scope channel (1 or 2).
        sample_rate_hz: Sample rate in Hz (max ~100 MHz for single channel).
        buffer_size: Number of samples to capture (power of 2 recommended).
        voltage_range_v: Vertical range in volts peak-to-peak (e.g. 5.0 = ±5V).
        offset_v: Vertical offset in volts.
        trigger_source: 'none', 'analog', 'digital', or 'external'.
        trigger_channel: Which channel to trigger on (1 or 2, analog trigger).
        trigger_level_v: Trigger threshold voltage.
        trigger_slope: 'rise', 'fall', or 'either'.
        timeout_s: Maximum wait time for trigger.

    Returns:
        dict with keys: channel, sample_rate_hz, buffer_size, num_samples,
        v_min, v_max, v_pp, v_mean, v_rms, samples (list of first 500 values),
        and time_axis_us (first 20 values).
    """
    ch = channel - 1  # 0-indexed
    trig_ch = trigger_channel - 1

    trigger_map = {
        "none": DwfTriggerSource.None_,
        "analog": DwfTriggerSource.DetectorAnalogIn,
        "digital": DwfTriggerSource.DetectorDigitalIn,
        "external": DwfTriggerSource.External1,
    }
    slope_map = {
        "rise": DwfTriggerSlope.Rise,
        "fall": DwfTriggerSlope.Fall,
        "either": DwfTriggerSlope.Either,
    }

    with _get_device() as dev:
        ain = dev.analogIn

        # Channels
        ain.channelEnableSet(ch, True)
        if ch != 0:
            ain.channelEnableSet(0, False)
        ain.channelRangeSet(ch, voltage_range_v)
        ain.channelOffsetSet(ch, offset_v)

        # Acquisition
        ain.acquisitionModeSet(DwfAcquisitionMode.Single)
        ain.frequencySet(sample_rate_hz)
        ain.bufferSizeSet(buffer_size)

        # Trigger
        trig_src = trigger_map.get(trigger_source, DwfTriggerSource.None_)
        trig_slp = slope_map.get(trigger_slope, DwfTriggerSlope.Rise)
        ain.triggerSourceSet(trig_src)
        ain.triggerChannelSet(trig_ch)
        ain.triggerLevelSet(trigger_level_v)
        ain.triggerConditionSet(trig_slp)
        ain.triggerPositionSet(0.0)

        ain.configure(False, True)

        if not _wait_acquisition(ain, timeout_s):
            return {"error": "Acquisition timed out", "timeout_s": timeout_s}

        samples = ain.statusData(ch, buffer_size)
        arr = np.array(samples, dtype=np.float64)

        # Trim first 500 samples for response; keep full stats
        preview = arr[:500].tolist()
        t_us = (np.arange(20) / sample_rate_hz * 1e6).tolist()

    return {
        "channel": channel,
        "sample_rate_hz": sample_rate_hz,
        "buffer_size": buffer_size,
        "num_samples": len(arr),
        "v_min_v": float(arr.min()),
        "v_max_v": float(arr.max()),
        "v_pp_v": float(np.ptp(arr)),
        "v_mean_v": float(arr.mean()),
        "v_rms_v": float(np.sqrt(np.mean(np.square(arr)))),
        "samples_preview_500": preview,
        "time_axis_us_preview_20": t_us,
    }


# ─── dual channel capture ───────────────────────────────────────────────────

@mcp.tool()
def oscilloscope_dual_capture(
    sample_rate_hz: float = 1_000_000.0,
    buffer_size: int = 4096,
    voltage_range_v: float = 5.0,
    timeout_s: float = 5.0,
) -> dict:
    """Capture both oscilloscope channels simultaneously (no trigger).

    Args:
        sample_rate_hz: Sample rate in Hz.
        buffer_size: Samples per channel.
        voltage_range_v: Vertical range for both channels.
        timeout_s: Timeout in seconds.

    Returns:
        dict with ch1 and ch2 each containing stats and preview samples.
    """
    with _get_device() as dev:
        ain = dev.analogIn

        ain.channelEnableSet(0, True)
        ain.channelEnableSet(1, True)
        ain.channelRangeSet(0, voltage_range_v)
        ain.channelRangeSet(1, voltage_range_v)
        ain.channelOffsetSet(0, 0.0)
        ain.channelOffsetSet(1, 0.0)

        ain.acquisitionModeSet(DwfAcquisitionMode.Single)
        ain.frequencySet(sample_rate_hz)
        ain.bufferSizeSet(buffer_size)
        ain.triggerSourceSet(DwfTriggerSource.None_)

        ain.configure(False, True)

        if not _wait_acquisition(ain, timeout_s):
            return {"error": "Acquisition timed out"}

        result = {}
        for ch in (0, 1):
            arr = np.array(ain.statusData(ch, buffer_size), dtype=np.float64)
            result[f"ch{ch+1}"] = {
                "num_samples": len(arr),
                "v_min_v": float(arr.min()),
                "v_max_v": float(arr.max()),
                "v_pp_v": float(np.ptp(arr)),
                "v_mean_v": float(arr.mean()),
                "v_rms_v": float(np.sqrt(np.mean(np.square(arr)))),
                "samples_preview_200": arr[:200].tolist(),
            }
    return result


# ─── AWG / signal generator ─────────────────────────────────────────────────

@mcp.tool()
def awg_generate(
    channel: int = 1,
    waveform: str = "sine",
    frequency_hz: float = 1000.0,
    amplitude_vpp: float = 2.0,
    offset_v: float = 0.0,
    duty_cycle_pct: float = 50.0,
    enable: bool = True,
) -> dict:
    """Configure the ADP2230 Arbitrary Waveform Generator (AWG).

    Args:
        channel: AWG channel (1 or 2).
        waveform: 'sine', 'square', 'triangle', 'ramp_up', 'ramp_down', 'noise', 'dc'.
        frequency_hz: Output frequency in Hz.
        amplitude_vpp: Peak-to-peak amplitude in volts.
        offset_v: DC offset in volts.
        duty_cycle_pct: Duty cycle for square wave (0-100). Ignored for other waveforms.
        enable: Enable or disable the output.

    Returns:
        Current AWG configuration.
    """
    wf_map = {
        "sine": DwfAnalogOutFunction.Sine,
        "square": DwfAnalogOutFunction.Square,
        "triangle": DwfAnalogOutFunction.Triangle,
        "ramp_up": DwfAnalogOutFunction.RampUp,
        "ramp_down": DwfAnalogOutFunction.RampDown,
        "noise": DwfAnalogOutFunction.Noise,
        "dc": DwfAnalogOutFunction.DC,
    }

    wf = wf_map.get(waveform, DwfAnalogOutFunction.Sine)
    ch = channel - 1

    with _get_device() as dev:
        awg = dev.analogOut
        awg.nodeEnableSet(ch, DwfAnalogOutNode.Carrier, enable)
        awg.nodeFunctionSet(ch, DwfAnalogOutNode.Carrier, wf)
        awg.nodeFrequencySet(ch, DwfAnalogOutNode.Carrier, frequency_hz)
        awg.nodeAmplitudeSet(ch, DwfAnalogOutNode.Carrier, amplitude_vpp)
        awg.nodeOffsetSet(ch, DwfAnalogOutNode.Carrier, offset_v)

        if waveform == "square":
            awg.nodeSymmetrySet(ch, DwfAnalogOutNode.Carrier, duty_cycle_pct)

        awg.idleSet(ch, DwfAnalogOutIdle.Offset)
        awg.configure(ch, enable)

    return {
        "channel": channel,
        "waveform": waveform,
        "frequency_hz": frequency_hz,
        "amplitude_vpp": amplitude_vpp,
        "offset_v": offset_v,
        "duty_cycle_pct": duty_cycle_pct if waveform == "square" else None,
        "enabled": enable,
    }


# ─── logic analyzer ──────────────────────────────────────────────────────────

@mcp.tool()
def logic_analyzer_capture(
    sample_rate_hz: float = 10_000_000.0,
    buffer_size: int = 4096,
    timeout_s: float = 5.0,
) -> dict:
    """Capture from the ADP2230 16-channel logic analyzer.

    Args:
        sample_rate_hz: Sample rate in Hz (max 100 MHz).
        buffer_size: Number of samples to capture.
        timeout_s: Timeout in seconds.

    Returns:
        dict with num_samples, sample_rate, and pin_data: mapping of
        DIO_0 through DIO_15 to lists of sample values (0 or 1), preview 200 samples.
    """
    with _get_device() as dev:
        din = dev.digitalIn

        # Calculate divider from base clock (100 MHz)
        base_clock = 100_000_000.0
        divider = max(1, int(base_clock / sample_rate_hz))
        actual_rate = base_clock / divider

        din.internalClockInfo()
        din.dividerSet(divider)
        din.sampleFormatSet(16)  # 16-bit wide
        din.bufferSizeSet(buffer_size)

        din.triggerSourceSet(DwfTriggerSource.None_)
        din.configure(False, True)

        if not _wait_acquisition(din, timeout_s):
            return {"error": "Acquisition timed out"}

        raw = din.statusData(buffer_size, return_bytearray=True)

        # Parse 16 bits into per-pin arrays
        pin_data = {}
        for pin in range(16):
            pin_data[f"DIO_{pin}"] = [
                (raw[i // 2] >> (pin if i % 2 == 0 else pin - 8)) & 1
                if i % 2 == 0
                else (raw[i // 2] >> (pin - 8)) & 1
                for i in range(min(buffer_size * 2, 200))
            ]

    return {
        "num_samples": buffer_size,
        "sample_rate_hz": actual_rate,
        "channels": 16,
        "pin_data_preview": pin_data,
    }


# ─── pattern generator ──────────────────────────────────────────────────────

@mcp.tool()
def pattern_generator(
    frequency_hz: float = 1000.0,
    pattern: str = "0xAA,0x55",
    enable: bool = True,
) -> dict:
    """Configure the ADP2230 16-channel pattern generator.

    Args:
        frequency_hz: Pattern repeat frequency in Hz.
        pattern: Comma-separated hex bytes, e.g. '0xAA,0x55'.
        enable: Enable or disable the output.

    Returns:
        Current pattern generator configuration.
    """
    # Parse pattern
    try:
        values = [int(x.strip(), 16) for x in pattern.split(",")]
    except ValueError:
        return {"error": f"Invalid pattern '{pattern}'. Use hex bytes like '0xAA,0x55'."}

    with _get_device() as dev:
        dout = dev.digitalOut

        base_clock = 100_000_000.0
        divider = max(1, int(base_clock / (frequency_hz * len(values))))
        actual_freq = base_clock / (divider * len(values))

        dout.enableSet(0, enable)
        dout.dividerSet(0, divider)
        dout.outputSet(0, DwfDigitalOutOutput.PushPull)
        dout.typeSet(0, DwfDigitalOutType.Custom)
        dout.idleSet(0, DwfDigitalOutIdle.Init)
        dout.dataSet(0, values)
        dout.configure(True)

    return {
        "enabled": enable,
        "requested_frequency_hz": frequency_hz,
        "actual_frequency_hz": actual_freq,
        "pattern_bytes": len(values),
        "pattern_hex": [f"0x{v:02X}" for v in values],
    }


# ─── FFT / spectrum ─────────────────────────────────────────────────────────

@mcp.tool()
def spectrum_analyzer(
    channel: int = 1,
    sample_rate_hz: float = 10_000_000.0,
    buffer_size: int = 16384,
    voltage_range_v: float = 5.0,
) -> dict:
    """Capture and compute FFT spectrum on a scope channel.

    Args:
        channel: Scope channel (1 or 2).
        sample_rate_hz: Sample rate in Hz.
        buffer_size: Number of samples (power of 2 gives cleanest FFT).
        voltage_range_v: Vertical range in volts.

    Returns:
        dict with frequency bins (Hz), magnitude (dBV), and peak info.
    """
    ch = channel - 1

    with _get_device() as dev:
        ain = dev.analogIn
        ain.channelEnableSet(ch, True)
        ain.channelRangeSet(ch, voltage_range_v)
        ain.channelOffsetSet(ch, 0.0)
        ain.acquisitionModeSet(DwfAcquisitionMode.Single)
        ain.frequencySet(sample_rate_hz)
        ain.bufferSizeSet(buffer_size)
        ain.triggerSourceSet(DwfTriggerSource.None_)

        ain.configure(False, True)

        if not _wait_acquisition(ain, 5.0):
            return {"error": "Acquisition timed out"}

        samples = np.array(ain.statusData(ch, buffer_size), dtype=np.float64)

    freqs, mag_v = _linear_spectrum(samples, sample_rate_hz)

    # Convert to dBV (ref 1 V RMS)
    mag_dbv = 20 * np.log10(mag_v + 1e-12)

    peak_idx = np.argmax(mag_dbv)
    peak_freq = float(freqs[peak_idx])
    peak_dbv = float(mag_dbv[peak_idx])

    # Decimate for response: return ~200 points log-spaced
    num_preview = min(200, len(freqs))
    if num_preview < len(freqs):
        idx = np.round(np.logspace(0, np.log10(len(freqs) - 1), num_preview)).astype(int)
        idx = np.unique(idx)
    else:
        idx = np.arange(len(freqs))

    return {
        "channel": channel,
        "sample_rate_hz": sample_rate_hz,
        "buffer_size": buffer_size,
        "frequency_resolution_hz": sample_rate_hz / buffer_size,
        "peak_frequency_hz": peak_freq,
        "peak_magnitude_dBV": peak_dbv,
        "frequencies_hz_preview": freqs[idx].tolist(),
        "magnitudes_dBV_preview": mag_dbv[idx].tolist(),
    }


# ─── GPIO ───────────────────────────────────────────────────────────────────

@mcp.tool()
def gpio_control(pin: int, direction: str = "input", value: Optional[int] = None) -> dict:
    """Control a single digital I/O pin on the ADP2230.

    Args:
        pin: DIO pin number (0-15).
        direction: 'input' or 'output'.
        value: If output, set to 0 or 1.

    Returns:
        Current pin state.
    """
    from pydwf import DwfAnalogIO

    with _get_device() as dev:
        dio = dev.analogIO
        if direction == "output":
            dio.channelNodeSet(pin, 1, float(value or 0))  # node 1 = output enable
            dio.channelNodeSet(pin, 0, float(value or 0))  # node 0 = value
            dio.enableSet(True)
        volt = dio.channelNodeStatus(pin, 0)
        out_en = dio.channelNodeStatus(pin, 2)  # output enable

    return {
        "pin": pin,
        "direction": direction,
        "voltage_v": float(volt),
        "output_enabled": bool(out_en > 0.5),
    }


# ─── digital I/O (static) ────────────────────────────────────────────────────

@mcp.tool()
def digital_io(
    output_enable_mask: int = 0,
    output_value_mask: int = 0,
) -> dict:
    """Read/write all 16 DIO pins as a static bitmask (no timing/trigger).

    Use this for low-speed static I/O: read input states, set output
    enables, and drive pins high/low.  Conflicts with pattern_generator
    and logic_analyzer when active on the same pins.

    Args:
        output_enable_mask: Bitmask of pins to drive as outputs (0=HiZ, 1=output).
        output_value_mask: Bitmask of output values (1=high). Only applies
            to pins where output_enable_mask has the bit set.

    Returns:
        dict with input_status (bitmask of pins reading high),
        output_enable, output_value, and per-pin list.
    """
    with _get_device() as dev:
        dio = dev.digitalIO
        dio.reset()
        dio.outputEnableSet(output_enable_mask)
        dio.outputSet(output_value_mask)
        dio.configure()
        time.sleep(0.01)
        dio.status()
        inputs = dio.inputStatus()
        out_en = dio.outputEnableGet()
        out_val = dio.outputGet()

    pins = []
    for p in range(16):
        pins.append({
            "pin": p,
            "input_state": (inputs >> p) & 1,
            "output_enabled": (out_en >> p) & 1,
            "output_value": (out_val >> p) & 1,
        })

    return {
        "input_status_mask": inputs,
        "output_enable_mask": out_en,
        "output_value_mask": out_val,
        "pins": pins,
    }


# ─── analog I/O (power supplies / sensors) ───────────────────────────────────

@mcp.tool()
def analog_io(
    channel_name: str = "",
    node_name: str = "",
    value: Optional[float] = None,
    master_enable: Optional[bool] = None,
) -> dict:
    """Read or control the ADP2230 analog I/O channels (power supplies, sensors).

    The ADP2230 exposes channels for digital voltage (DVCC), Zynq temperature,
    Zynq internal voltages, etc.  Pass channel_name='' to enumerate all
    channels and nodes.

    Args:
        channel_name: Channel label (e.g. 'DVCC', 'Zynq'). Empty = enumerate all.
        node_name: Node name (e.g. 'Voltage', 'Temperature'). Empty = all nodes.
        value: If set, write this value to the specified channel node.
        master_enable: If set, enable/disable the master power switch.

    Returns:
        dict with channels list or the written/read value.
    """
    with _get_device() as dev:
        aio = dev.analogIO

        if master_enable is not None:
            aio.enableSet(master_enable)
        aio.configure()
        aio.status()

        channels = []
        for c in range(aio.channelCount()):
            ch_name, ch_label = aio.channelName(c)
            if channel_name and ch_label != channel_name:
                continue
            ch_info = {"index": c, "name": ch_name, "label": ch_label, "nodes": []}
            for n in range(aio.channelInfo(c)):
                n_name, n_unit = aio.channelNodeName(c, n)
                if node_name and n_name != node_name:
                    continue
                node_type = str(aio.channelNodeInfo(c, n))
                status_val = aio.channelNodeStatus(c, n)
                set_val = aio.channelNodeGet(c, n)

                if value is not None and n_name == node_name and ch_label == channel_name:
                    aio.channelNodeSet(c, n, value)
                    aio.configure()
                    set_val = value

                ch_info["nodes"].append({
                    "index": n, "name": n_name, "unit": n_unit,
                    "type": node_type, "status": status_val, "set_value": set_val,
                })
            channels.append(ch_info)

        aio.status()
        master = aio.enableGet() if aio.enableInfo()[0] else None
        master_status = aio.enableStatus() if aio.enableInfo()[1] else None

    return {
        "master_enable": master,
        "master_enable_status": master_status,
        "channels": channels,
    }


# ─── UART protocol ───────────────────────────────────────────────────────────

@mcp.tool()
def uart(
    baud_rate: int = 115200,
    tx_pin: int = 0,
    rx_pin: int = 1,
    data_bits: int = 8,
    parity: str = "none",
    stop_bits: float = 1.0,
    tx_data: Optional[str] = None,
    rx_count: int = 0,
) -> dict:
    """UART transmitter/receiver using two DIO pins.

    Configure baud rate, data bits, parity, and stop bits. Send tx_data
    (string, encoded as UTF-8 bytes) and optionally receive rx_count bytes.

    Args:
        baud_rate: Baud rate (300, 9600, 115200, etc.).
        tx_pin: DIO pin for TX (transmit).
        rx_pin: DIO pin for RX (receive).
        data_bits: Data bits (7 or 8).
        parity: 'none', 'odd', or 'even'.
        stop_bits: Stop bits (1, 1.5, or 2).
        tx_data: String to transmit (leave empty to skip TX).
        rx_count: Number of bytes to receive (0 = skip RX).

    Returns:
        dict with tx_bytes_sent and rx_data/received bytes.
    """
    parity_map = {"none": 0, "odd": 1, "even": 2}

    with _get_device() as dev:
        u = dev.protocol.uart
        u.reset()
        u.rateSet(float(baud_rate))
        u.bitsSet(data_bits)
        u.paritySet(parity_map.get(parity, 0))
        u.stopSet(stop_bits)
        u.txSet(tx_pin)
        u.rxSet(rx_pin)

        result = {"baud_rate": baud_rate, "tx_pin": tx_pin, "rx_pin": rx_pin}

        if tx_data is not None:
            tx_bytes = tx_data.encode("utf-8")
            u.tx(tx_bytes)
            result["tx_bytes_sent"] = len(tx_bytes)

        if rx_count > 0:
            u.rx(0)  # initialize receiver
            rx_bytes, parity_err = u.rx(rx_count)
            result["rx_data"] = list(rx_bytes)
            result["rx_parity_error"] = parity_err

    return result


# ─── SPI protocol ────────────────────────────────────────────────────────────

@mcp.tool()
def spi(
    clock_freq_hz: float = 1_000_000.0,
    mode: int = 0,
    cs_pin: int = 0,
    sck_pin: int = 1,
    mosi_pin: int = 2,
    miso_pin: int = 3,
    tx_data: Optional[str] = None,
    rx_count: int = 0,
    bits_per_word: int = 8,
) -> dict:
    """SPI master using four DIO pins.

    Transmit tx_data (hex string, e.g. '0xA5,0x5A') and optionally
    read back rx_count bytes from the slave device.

    Args:
        clock_freq_hz: SPI clock frequency in Hz.
        mode: SPI mode 0-3 (CPOL/CPHA).
        cs_pin: DIO pin for Chip Select.
        sck_pin: DIO pin for Clock.
        mosi_pin: DIO pin for MOSI (Master Out).
        miso_pin: DIO pin for MISO (Master In).
        tx_data: Comma-separated hex bytes to transmit (e.g. '0x9F').
        rx_count: Number of bytes to read from MISO (0 = skip).
        bits_per_word: Bits per word (default 8).

    Returns:
        dict with tx_bytes and rx_data.
    """
    with _get_device() as dev:
        s = dev.protocol.spi
        s.reset()
        s.frequencySet(clock_freq_hz)
        s.modeSet(mode)
        s.orderSet(0)  # MSB first
        s.select(cs_pin, 1)  # enable CS
        s.ioSet(sck_pin, mosi_pin, miso_pin, 0)  # SCK, MOSI, MISO, unused

        result = {"clock_freq_hz": clock_freq_hz, "mode": mode, "cs_pin": cs_pin}

        tx_bytes = b""
        if tx_data is not None:
            parts = [x.strip() for x in tx_data.split(",")]
            tx_bytes = bytes(int(p, 16) for p in parts if p)

        total_to_exchange = max(len(tx_bytes), rx_count)
        if total_to_exchange > 0:
            mosi = list(tx_bytes) + [0] * max(0, total_to_exchange - len(tx_bytes))
            rx, count = s.writeRead(bits_per_word, mosi, total_to_exchange)
            result["tx_bytes"] = mosi[:total_to_exchange]
            result["rx_data"] = rx if rx_count > 0 else []

        s.select(cs_pin, 0)  # disable CS

    return result


# ─── I²C protocol ────────────────────────────────────────────────────────────

@mcp.tool()
def i2c(
    sda_pin: int = 0,
    scl_pin: int = 1,
    clock_freq_hz: float = 100_000.0,
    address: int = 0x50,
    tx_data: Optional[str] = None,
    rx_count: int = 0,
) -> dict:
    """I²C master using two DIO pins (SDA, SCL).

    Transmit tx_data (hex string) and/or read rx_count bytes from the
    specified 7-bit I²C address.  Uses internal pull-ups; add external
    2.2k-4.7k pull-ups to VCC for reliable operation above 100 kHz.

    Args:
        sda_pin: DIO pin for SDA (data).
        scl_pin: DIO pin for SCL (clock).
        clock_freq_hz: I²C clock frequency (100 kHz standard, 400 kHz fast).
        address: 7-bit I²C slave address.
        tx_data: Comma-separated hex bytes to write (e.g. '0x00,0x42').
        rx_count: Number of bytes to read after write (0 = skip).

    Returns:
        dict with tx_bytes_sent and rx_data.
    """
    with _get_device() as dev:
        i = dev.protocol.i2c
        i.reset()
        i.rateSet(clock_freq_hz)
        i.sdaSet(sda_pin)
        i.sclSet(scl_pin)
        i.stretchSet(True)  # clock stretching

        result = {"address": address, "sda_pin": sda_pin, "scl_pin": scl_pin}

        tx_bytes = b""
        if tx_data is not None:
            parts = [x.strip() for x in tx_data.split(",")]
            tx_bytes = bytes(int(p, 16) for p in parts if p)

        if tx_bytes or rx_count > 0:
            nak = i.writeRead(address, list(tx_bytes), rx_count)
            result["tx_bytes_sent"] = len(tx_bytes)
            if rx_count > 0:
                result["rx_data"] = nak if isinstance(nak, (list, bytes)) else []
                result["nak"] = nak if isinstance(nak, int) else None
            else:
                result["nak"] = nak

    return result


# ─── network analyzer (Bode plot) ────────────────────────────────────────────

@mcp.tool()
def network_analyzer(
    start_freq_hz: float = 100.0,
    stop_freq_hz: float = 100_000.0,
    points: int = 50,
    amplitude_v: float = 1.0,
    offset_v: float = 0.0,
    reference_ohms: float = 0.0,
    timeout_s: float = 30.0,
) -> dict:
    """Frequency response (Bode plot) using AWG1 as stimulus and scope CH1/CH2.

    Sweeps frequency from start_freq_hz to stop_freq_hz (logarithmic),
    measuring gain (CH2/CH1 in dB) and phase difference at each step.
    This is the Network Analyzer instrument (analogImpedance mode 0).

    Requires: AWG W1 → DUT input, CH1 → DUT input (reference), CH2 → DUT output.

    Args:
        start_freq_hz: Start frequency in Hz.
        stop_freq_hz: Stop frequency in Hz.
        points: Number of frequency steps (max ~200).
        amplitude_v: AWG amplitude in volts.
        offset_v: AWG DC offset in volts.
        reference_ohms: Reference resistor for impedance mode (0 = Bode mode).
        timeout_s: Maximum sweep time in seconds.

    Returns:
        dict with frequencies, gains_db, phases_deg arrays.
    """
    with _get_device() as dev:
        imp = dev.analogImpedance
        imp.reset()

        if reference_ohms > 0:
            imp.modeSet(8)  # impedance analyzer
            imp.referenceSet(reference_ohms)
        else:
            imp.modeSet(0)  # W1-C1-DUT-C2-R-GND (network analyzer)
            imp.referenceSet(1.0)

        imp.amplitudeSet(amplitude_v)
        imp.offsetSet(offset_v)

        frequencies = np.logspace(np.log10(start_freq_hz), np.log10(stop_freq_hz), points)
        gains_db = []
        phases_deg = []
        impedances = []

        t0 = time.monotonic()

        for freq in frequencies:
            if time.monotonic() - t0 > timeout_s:
                break

            imp.frequencySet(float(freq))
            imp.configure(True)

            while True:
                st = imp.status()
                if st == DwfState.Done:
                    break
                if time.monotonic() - t0 > timeout_s:
                    break
                time.sleep(0.002)

            if time.monotonic() - t0 > timeout_s:
                break

            gain_ch1, phase_ch1 = imp.statusInput(0)  # reference
            gain_ch2, phase_ch2 = imp.statusInput(1)  # DUT output

            gain_db = 20.0 * np.log10(max(gain_ch2 / max(gain_ch1, 1e-9), 1e-9))
            phase_deg = (phase_ch2 - phase_ch1) * 180.0 / np.pi
            while phase_deg > 180:
                phase_deg -= 360
            while phase_deg < -180:
                phase_deg += 360

            gains_db.append(round(gain_db, 3))
            phases_deg.append(round(phase_deg, 3))

            if reference_ohms > 0:
                imp_mag = imp.statusMeasure(DwfAnalogImpedance.Impedance)
                imp_phase = imp.statusMeasure(DwfAnalogImpedance.ImpedancePhase)
                impedances.append({
                    "freq_hz": round(freq, 1),
                    "impedance_ohm": round(imp_mag, 3),
                    "phase_deg": round(imp_phase, 3),
                })

    result = {
        "start_freq_hz": start_freq_hz,
        "stop_freq_hz": stop_freq_hz,
        "points_measured": len(gains_db),
        "amplitude_v": amplitude_v,
        "mode": "impedance" if reference_ohms > 0 else "network",
        "frequencies_hz": [round(f, 1) for f in frequencies[:len(gains_db)]],
        "gains_db": gains_db,
        "phases_deg": phases_deg,
    }

    if impedances:
        result["impedances"] = impedances

    return result


# ─── impedance analyzer (single-point) ───────────────────────────────────────

@mcp.tool()
def impedance_analyzer(
    frequency_hz: float = 1000.0,
    reference_ohms: float = 1000.0,
    amplitude_v: float = 1.0,
    offset_v: float = 0.0,
) -> dict:
    """Measure impedance of a DUT at a single frequency.

    Uses the ADP2230 Impedance Analyzer (mode 8) with an external reference
    resistor.  Requires: AWG W1 → Rref → DUT → GND, CH1 across DUT,
    CH2 across Rref.

    Args:
        frequency_hz: Test frequency in Hz.
        reference_ohms: Reference resistor value in ohms.
        amplitude_v: Stimulus amplitude in volts.
        offset_v: Stimulus DC offset in volts.

    Returns:
        dict with impedance magnitude, phase, resistance, reactance,
        and derived R/L/C at the test frequency.
    """
    with _get_device() as dev:
        imp = dev.analogImpedance
        imp.reset()
        imp.modeSet(8)
        imp.referenceSet(reference_ohms)
        imp.amplitudeSet(amplitude_v)
        imp.offsetSet(offset_v)
        imp.frequencySet(frequency_hz)

        imp.configure(True)
        t0 = time.monotonic()
        while imp.status() != DwfState.Done:
            if time.monotonic() - t0 > 5.0:
                return {"error": "Impedance measurement timed out"}
            time.sleep(0.002)

        imp_mag = imp.statusMeasure(DwfAnalogImpedance.Impedance)
        imp_phase = imp.statusMeasure(DwfAnalogImpedance.ImpedancePhase)
        resistance = imp.statusMeasure(DwfAnalogImpedance.Resistance)
        reactance = imp.statusMeasure(DwfAnalogImpedance.Reactance)

    omega = 2.0 * np.pi * frequency_hz
    inductance = None
    capacitance = None
    if reactance > 0 and omega > 0:
        inductance = reactance / omega
    elif reactance < 0 and omega > 0:
        capacitance = -1.0 / (omega * reactance)

    return {
        "frequency_hz": frequency_hz,
        "reference_ohms": reference_ohms,
        "impedance_ohm": round(imp_mag, 3),
        "phase_deg": round(imp_phase, 3),
        "resistance_ohm": round(resistance, 3),
        "reactance_ohm": round(reactance, 3),
        "inductance_H": round(inductance, 9) if inductance else None,
        "capacitance_F": round(capacitance, 12) if capacitance else None,
    }


# ─── CAN protocol ────────────────────────────────────────────────────────────

@mcp.tool()
def can(
    bit_rate: int = 500_000,
    tx_pin: int = 0,
    rx_pin: int = 1,
    tx_id: int = 0x100,
    tx_data: Optional[str] = None,
    is_extended: bool = False,
    is_remote: bool = False,
    rx_count: int = 0,
) -> dict:
    """CAN bus transmitter/receiver using two DIO pins.

    NOTE: Requires an external CAN transceiver (e.g. MCP2551, SN65HVD230)
    to convert the 3.3V DIO signals to CAN bus differential levels.

    Args:
        bit_rate: CAN bit rate (125000, 250000, 500000, 1000000).
        tx_pin: DIO pin for TX (connect to transceiver TXD).
        rx_pin: DIO pin for RX (connect to transceiver RXD).
        tx_id: CAN message ID (11-bit standard or 29-bit extended).
        tx_data: Comma-separated hex bytes (max 8 for CAN).
        is_extended: Use 29-bit extended ID.
        is_remote: Send a remote frame.
        rx_count: Number of frames to receive (0 = skip RX).

    Returns:
        dict with tx_status and rx_frames.
    """
    with _get_device() as dev:
        c = dev.protocol.can
        c.reset()
        c.rateSet(float(bit_rate))
        c.txSet(tx_pin)
        c.rxSet(rx_pin)

        result = {"bit_rate": bit_rate, "tx_pin": tx_pin, "rx_pin": rx_pin}

        if tx_data is not None:
            parts = [x.strip() for x in tx_data.split(",")]
            tx_bytes = [int(p, 16) for p in parts if p]
            flags = 0
            if is_extended:
                flags |= 1
            if is_remote:
                flags |= 2
            c.tx(tx_id, tx_bytes[:8], flags)
            result["tx_id"] = tx_id
            result["tx_data"] = tx_bytes[:8]
            result["tx_extended"] = is_extended
            result["tx_remote"] = is_remote

        if rx_count > 0:
            c.rx(0)  # initialize receiver
            frames = []
            import struct
            for _ in range(rx_count):
                try:
                    rx_id, rx_data, rx_flags, rx_status = c.rx(1)
                    if rx_status == 3:  # DwfStateDone = 3
                        pass
                    if rx_data:
                        frames.append({
                            "id": rx_id,
                            "data": list(rx_data) if rx_data else [],
                            "extended": bool(rx_flags & 1),
                            "remote": bool(rx_flags & 2),
                            "status": rx_status,
                        })
                except Exception:
                    break
            result["rx_frames"] = frames

    return result


# ─── SWD protocol ────────────────────────────────────────────────────────────

@mcp.tool()
def swd(
    clock_freq_hz: float = 1_000_000.0,
    dio_pin: int = 0,
    clk_pin: int = 1,
    command: Optional[str] = None,
) -> dict:
    """ARM Serial Wire Debug (SWD) interface using two DIO pins.

    Low-level SWD bus interface.  Connect DIO pin → SWDIO, CLK pin → SWCLK
    on an ARM Cortex-M target.  Use for reading IDCODE, accessing DP/AP
    registers, or flashing targets that speak SWD.

    WARNING: This is a raw SWD interface.  Incorrect commands can lock up
    the target or corrupt firmware.  Prefer using OpenOCD + JTAG/SWD probe
    for production debugging.

    Args:
        clock_freq_hz: SWD clock frequency in Hz.
        dio_pin: DIO pin for SWDIO (bidirectional data).
        clk_pin: DIO pin for SWCLK (clock).
        command: Comma-separated hex bytes to write. If empty, reads back
            a response (performs turnaround).

    Returns:
        dict with tx_bytes, rx_data, and bus status.
    """
    with _get_device() as dev:
        s = dev.protocol.swd
        s.reset()
        s.rateSet(clock_freq_hz)
        s.ioSet(dio_pin)
        s.clkSet(clk_pin)

        result = {"clock_freq_hz": clock_freq_hz, "dio_pin": dio_pin, "clk_pin": clk_pin}

        if command is not None:
            parts = [x.strip() for x in command.split(",")]
            tx = [int(p, 16) for p in parts if p]
            s.write(tx)
            result["tx_bytes"] = tx

        if command is None or len(parts) > 0:
            time.sleep(0.001)
            rx, parity = s.read(4)  # read back 4 bytes
            result["rx_data"] = rx if rx else []
            result["parity"] = parity

    return result


# ─── main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
