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


# ─── main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
