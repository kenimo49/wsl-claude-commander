"""Window operations via PowerShell (WSL2 -> Windows)."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from claude_talk.utils.logging import get_logger

logger = get_logger(__name__)

# Path to scripts directory
SCRIPTS_DIR = Path(__file__).parent.parent.parent.parent / "scripts"


@dataclass
class WindowInfo:
    """Information about a window."""

    handle: int
    title: str


def _run_powershell(script_name: str, **params: str | int) -> dict:
    """Run a PowerShell script and return JSON result.

    Args:
        script_name: Name of script in scripts directory.
        **params: Parameters to pass to script.

    Returns:
        Parsed JSON result from script.
    """
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    # Build command
    cmd = ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]

    for key, value in params.items():
        cmd.extend([f"-{key}", str(value)])

    logger.debug("Running PowerShell", cmd=" ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            logger.error(
                "PowerShell error",
                stderr=result.stderr,
                returncode=result.returncode,
            )
            return {"success": False, "error": result.stderr}

        return json.loads(result.stdout)

    except subprocess.TimeoutExpired:
        logger.error("PowerShell timeout")
        return {"success": False, "error": "Timeout"}
    except json.JSONDecodeError as e:
        logger.error("Failed to parse PowerShell output", error=str(e))
        return {"success": False, "error": f"JSON parse error: {e}"}
    except Exception as e:
        logger.error("PowerShell execution failed", error=str(e))
        return {"success": False, "error": str(e)}


def get_windows(title_pattern: str = "") -> list[WindowInfo]:
    """Get list of windows matching a title pattern.

    Args:
        title_pattern: Pattern to match in window titles.

    Returns:
        List of WindowInfo objects.
    """
    result = _run_powershell("get-windows.ps1", TitlePattern=title_pattern)

    windows = []
    for win in result.get("windows", []):
        windows.append(WindowInfo(
            handle=win["handle"],
            title=win["title"],
        ))

    return windows


def get_foreground_window() -> int | None:
    """Get handle of currently focused window.

    Returns:
        Window handle, or None if failed.
    """
    result = _run_powershell("get-windows.ps1", TitlePattern="")
    return result.get("foreground")


def find_window(title_pattern: str) -> WindowInfo | None:
    """Find first window matching title pattern.

    Args:
        title_pattern: Pattern to match in window title.

    Returns:
        WindowInfo if found, None otherwise.
    """
    windows = get_windows(title_pattern)
    return windows[0] if windows else None


def activate_window(handle: int | None = None, title: str | None = None) -> bool:
    """Activate (focus) a window.

    Args:
        handle: Window handle to activate.
        title: Window title pattern to find and activate.

    Returns:
        True if successful.
    """
    if handle:
        result = _run_powershell("activate-window.ps1", Handle=handle)
    elif title:
        result = _run_powershell("activate-window.ps1", Title=title)
    else:
        logger.error("Either handle or title must be provided")
        return False

    return result.get("success", False)


def find_claude_window(title_pattern: str = "claude") -> WindowInfo | None:
    """Find Claude Code window.

    Args:
        title_pattern: Pattern to match Claude window.

    Returns:
        WindowInfo if found.
    """
    return find_window(title_pattern)
