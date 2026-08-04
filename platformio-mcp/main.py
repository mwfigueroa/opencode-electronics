import asyncio
import json
import os
import time
from typing import Tuple

from mcp.server.fastmcp import FastMCP

PLATFORMIO_BIN = os.path.expanduser("~/.platformio/penv/bin/platformio")

mcp = FastMCP("platformio-mcp")


async def _run_pio(cmd: str, cwd: str | None = None, timeout_s: int = 300) -> Tuple[str, str]:
    start = time.time()
    env = os.environ.copy()
    env["PLATFORMIO_CORE_DIR"] = os.path.expanduser("~/.platformio")
    proc = await asyncio.create_subprocess_shell(
        f"{PLATFORMIO_BIN} {cmd}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        env=env,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        elapsed = time.time() - start
        return "", f"Command timed out after {elapsed:.1f}s"

    elapsed = time.time() - start
    out = stdout.decode("utf-8", errors="replace")
    err = stderr.decode("utf-8", errors="replace")
    timing = f"\n\n[Completed in {elapsed:.1f}s]\n"
    return out + timing, err


# ─── project / build / upload ────────────────────────────────────────────

@mcp.tool()
async def pio_project_init(
    project_path: str,
    board: str,
    platform: str | None = None,
    project_name: str | None = None,
) -> Tuple[str, str]:
    """Create a new PlatformIO project.

    Args:
        project_path: Directory path for the new project.
        board: Board ID (e.g. 'bluepill_f103c8', 'nodemcuv2', 'uno').
        platform: Optional platform name (e.g. 'ststm32', 'espressif32').
        project_name: Optional project name. Defaults to directory basename.

    Returns:
        tuple: (stdout, stderr)
    """
    os.makedirs(project_path, exist_ok=True)
    cmd = f"project init --project-dir {project_path} --board {board}"
    if platform:
        cmd += f" --ide {platform}"
    return await _run_pio(cmd, cwd=project_path)


@mcp.tool()
async def pio_run(
    project_path: str,
    target: str | None = None,
    environment: str | None = None,
    verbose: bool = False,
) -> Tuple[str, str]:
    """Build / compile a PlatformIO project.

    Args:
        project_path: Path to the project directory.
        target: Optional build target (e.g. 'upload', 'clean', 'program').
        environment: Optional environment name from platformio.ini.
        verbose: Enable verbose output if True.

    Returns:
        tuple: (stdout, stderr)
    """
    cmd = "run"
    if target:
        cmd += f" --target {target}"
    if environment:
        cmd += f" --environment {environment}"
    if verbose:
        cmd += " --verbose"
    return await _run_pio(cmd, cwd=project_path, timeout_s=600)


@mcp.tool()
async def pio_upload(
    project_path: str,
    port: str | None = None,
    environment: str | None = None,
) -> Tuple[str, str]:
    """Flash firmware to a connected device.

    Args:
        project_path: Path to the project directory.
        port: Serial port (e.g. '/dev/ttyUSB0', 'COM3'). Auto-detect if omitted.
        environment: Optional environment name from platformio.ini.

    Returns:
        tuple: (stdout, stderr)
    """
    cmd = "run --target upload"
    if port:
        cmd += f" --upload-port {port}"
    if environment:
        cmd += f" --environment {environment}"
    return await _run_pio(cmd, cwd=project_path, timeout_s=600)


@mcp.tool()
async def pio_clean(project_path: str) -> Tuple[str, str]:
    """Clean build artifacts for a PlatformIO project.

    Args:
        project_path: Path to the project directory.

    Returns:
        tuple: (stdout, stderr)
    """
    return await _run_pio("run --target clean", cwd=project_path)


# ─── device / monitor ────────────────────────────────────────────────────

@mcp.tool()
async def pio_device_list() -> Tuple[str, str]:
    """List connected serial devices detected by PlatformIO.

    Returns:
        tuple: (stdout, stderr)
    """
    return await _run_pio("device list")


@mcp.tool()
async def pio_device_monitor(
    port: str | None = None,
    baud: int = 115200,
    timeout_s: int = 60,
) -> Tuple[str, str]:
    """Capture serial output from a device (timed, max 60s by default).

    Args:
        port: Serial port. Auto-detect if omitted.
        baud: Baud rate (default 115200).
        timeout_s: Maximum capture time in seconds (default 60).

    Returns:
        tuple: (stdout, stderr)
    """
    cmd = f"device monitor --baud {baud} --quiet"
    if port:
        cmd += f" --port {port}"
    return await _run_pio(cmd, timeout_s=timeout_s)


# ─── boards ───────────────────────────────────────────────────────────────

@mcp.tool()
async def pio_boards(query: str = "") -> Tuple[str, str]:
    """Search available PlatformIO boards.

    Args:
        query: Search string (e.g. 'stm32', 'esp32', 'teensy'). Empty returns all.

    Returns:
        tuple: (stdout, stderr) — JSON-formatted board list.
    """
    cmd = "boards --json-output"
    if query:
        cmd += f" {query}"
    return await _run_pio(cmd)


# ─── testing / analysis ───────────────────────────────────────────────────

@mcp.tool()
async def pio_test(project_path: str, environment: str | None = None) -> Tuple[str, str]:
    """Run unit tests in a PlatformIO project.

    Args:
        project_path: Path to the project directory.
        environment: Optional environment name.

    Returns:
        tuple: (stdout, stderr)
    """
    cmd = "test"
    if environment:
        cmd += f" --environment {environment}"
    return await _run_pio(cmd, cwd=project_path, timeout_s=600)


@mcp.tool()
async def pio_check(project_path: str) -> Tuple[str, str]:
    """Run static analysis (cppcheck) on a PlatformIO project.

    Args:
        project_path: Path to the project directory.

    Returns:
        tuple: (stdout, stderr)
    """
    return await _run_pio("check", cwd=project_path, timeout_s=600)


# ─── libraries ────────────────────────────────────────────────────────────

@mcp.tool()
async def pio_lib_install(
    project_path: str,
    library: str,
    lib_id: int | None = None,
) -> Tuple[str, str]:
    """Install a library by name, ID, or URL.

    Args:
        project_path: Path to the project directory.
        library: Library name, ID number, or URL.
        lib_id: Optional numeric library ID from registry.

    Returns:
        tuple: (stdout, stderr)
    """
    if lib_id:
        cmd = f"lib --global install {lib_id}"
    else:
        cmd = f"lib install {library}"
    return await _run_pio(cmd, cwd=project_path)


@mcp.tool()
async def pio_lib_list(project_path: str, json_output: bool = True) -> Tuple[str, str]:
    """List installed libraries for a project.

    Args:
        project_path: Path to the project directory.
        json_output: Output as JSON if True (default).

    Returns:
        tuple: (stdout, stderr)
    """
    cmd = "lib list"
    if json_output:
        cmd += " --json-output"
    return await _run_pio(cmd, cwd=project_path)


@mcp.tool()
async def pio_lib_search(query: str, json_output: bool = True) -> Tuple[str, str]:
    """Search the PlatformIO library registry.

    Args:
        query: Search string (e.g. 'DallasTemperature', 'neopixel').
        json_output: Output as JSON if True (default).

    Returns:
        tuple: (stdout, stderr)
    """
    cmd = f"lib search {query}"
    if json_output:
        cmd += " --json-output"
    return await _run_pio(cmd)


# ─── debug ────────────────────────────────────────────────────────────────

@mcp.tool()
async def pio_debug_start(
    project_path: str,
    environment: str | None = None,
) -> Tuple[str, str]:
    """Start a GDB debug server for the project.

    Args:
        project_path: Path to the project directory.
        environment: Optional environment name.

    Returns:
        tuple: (stdout, stderr)
    """
    cmd = "debug"
    if environment:
        cmd += f" --environment {environment}"
    return await _run_pio(cmd, cwd=project_path, timeout_s=30)


# ─── maintenance ──────────────────────────────────────────────────────────

@mcp.tool()
async def pio_update(what: str = "all") -> Tuple[str, str]:
    """Update PlatformIO Core, platforms, and/or libraries.

    Args:
        what: What to update: 'all' (default), 'core', 'platforms', 'libraries'.

    Returns:
        tuple: (stdout, stderr)
    """
    valid = {"all", "core", "platforms", "libraries"}
    if what not in valid:
        return "", f"Invalid target '{what}'. Choose from: {', '.join(sorted(valid))}"
    if what == "all":
        cmd = "update"
    else:
        cmd = f"update --only-{what}"
    return await _run_pio(cmd, timeout_s=300)


@mcp.tool()
async def pio_system_info() -> Tuple[str, str]:
    """Show PlatformIO version, paths, and installed platforms.

    Returns:
        tuple: (stdout, stderr)
    """
    stdout, stderr = await _run_pio("system info")
    return stdout, stderr


if __name__ == "__main__":
    mcp.run()
