"""Clipboard operations via PowerShell (WSL2 -> Windows)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from claude_talk.utils.logging import get_logger

logger = get_logger(__name__)

# Path to scripts directory
SCRIPTS_DIR = Path(__file__).parent.parent.parent.parent / "scripts"


def set_clipboard(text: str) -> bool:
    """Set Windows clipboard text.

    Args:
        text: Text to copy to clipboard.

    Returns:
        True if successful.
    """
    script_path = SCRIPTS_DIR / "set-clipboard.ps1"

    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    try:
        # Use stdin to pass text to avoid escaping issues
        result = subprocess.run(
            [
                "powershell.exe",
                "-ExecutionPolicy", "Bypass",
                "-Command",
                f'Set-Clipboard -Value "{text}"',
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            logger.error("Failed to set clipboard", stderr=result.stderr)
            return False

        logger.info("Clipboard set", length=len(text))
        return True

    except subprocess.TimeoutExpired:
        logger.error("Clipboard operation timeout")
        return False
    except Exception as e:
        logger.error("Clipboard operation failed", error=str(e))
        return False


def get_clipboard() -> str | None:
    """Get Windows clipboard text.

    Returns:
        Clipboard text, or None if failed.
    """
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-ExecutionPolicy", "Bypass",
                "-Command",
                "Get-Clipboard",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            logger.error("Failed to get clipboard", stderr=result.stderr)
            return None

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        logger.error("Clipboard operation timeout")
        return None
    except Exception as e:
        logger.error("Clipboard operation failed", error=str(e))
        return None
