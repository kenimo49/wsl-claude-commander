"""Send text input to Claude window via clipboard and keyboard simulation."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from claude_talk.utils.logging import get_logger
from claude_talk.windows.clipboard import set_clipboard
from claude_talk.windows.window_ops import (
    WindowInfo,
    activate_window,
    find_claude_window,
    get_foreground_window,
)

logger = get_logger(__name__)

# Path to scripts directory
SCRIPTS_DIR = Path(__file__).parent.parent.parent.parent / "scripts"


def send_keys(keys: str) -> bool:
    """Send keyboard input to active window.

    Args:
        keys: Keys to send in SendKeys format.
              ^v = Ctrl+V, {ENTER} = Enter, etc.

    Returns:
        True if successful.
    """
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-ExecutionPolicy", "Bypass",
                "-Command",
                f"""
                Add-Type -AssemblyName System.Windows.Forms
                Start-Sleep -Milliseconds 100
                [System.Windows.Forms.SendKeys]::SendWait('{keys}')
                """,
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            logger.error("Failed to send keys", stderr=result.stderr)
            return False

        logger.debug("Keys sent", keys=keys)
        return True

    except subprocess.TimeoutExpired:
        logger.error("SendKeys timeout")
        return False
    except Exception as e:
        logger.error("SendKeys failed", error=str(e))
        return False


class ClaudeInputSender:
    """Send text input to Claude Code window."""

    def __init__(
        self,
        window_title: str = "claude",
        restore_window: bool = True,
        send_delay: float = 0.1,
    ) -> None:
        """Initialize Claude input sender.

        Args:
            window_title: Pattern to match Claude window title.
            restore_window: Whether to restore original window after sending.
            send_delay: Delay in seconds before sending input.
        """
        self.window_title = window_title
        self.restore_window = restore_window
        self.send_delay = send_delay

    def send(self, text: str, auto_submit: bool = True) -> bool:
        """Send text to Claude Code window.

        Args:
            text: Text to send.
            auto_submit: Whether to press Enter after pasting.

        Returns:
            True if successful.
        """
        if not text or not text.strip():
            logger.warning("Empty text, nothing to send")
            return False

        # Save current foreground window
        original_window = get_foreground_window() if self.restore_window else None

        # Find Claude window
        claude_window = find_claude_window(self.window_title)
        if not claude_window:
            logger.error("Claude window not found", pattern=self.window_title)
            return False

        logger.info(
            "Sending to Claude",
            window=claude_window.title,
            text_length=len(text),
        )

        try:
            # Set clipboard
            if not set_clipboard(text):
                logger.error("Failed to set clipboard")
                return False

            # Activate Claude window
            if not activate_window(handle=claude_window.handle):
                logger.error("Failed to activate Claude window")
                return False

            # Wait for window to activate
            time.sleep(self.send_delay)

            # Paste (Ctrl+V)
            if not send_keys("^v"):
                logger.error("Failed to paste")
                return False

            # Submit (Enter) if requested
            if auto_submit:
                time.sleep(0.05)  # Small delay before Enter
                if not send_keys("{ENTER}"):
                    logger.error("Failed to send Enter")
                    return False

            logger.info("Text sent to Claude successfully")

            # Restore original window
            if self.restore_window and original_window:
                time.sleep(0.1)
                activate_window(handle=original_window)

            return True

        except Exception as e:
            logger.error("Failed to send to Claude", error=str(e))

            # Try to restore original window on error
            if self.restore_window and original_window:
                try:
                    activate_window(handle=original_window)
                except Exception:
                    pass

            return False


def send_to_claude(
    text: str,
    window_title: str = "claude",
    auto_submit: bool = True,
    restore_window: bool = True,
) -> bool:
    """Convenience function to send text to Claude Code window.

    Args:
        text: Text to send.
        window_title: Pattern to match Claude window title.
        auto_submit: Whether to press Enter after pasting.
        restore_window: Whether to restore original window after sending.

    Returns:
        True if successful.
    """
    sender = ClaudeInputSender(
        window_title=window_title,
        restore_window=restore_window,
    )
    return sender.send(text, auto_submit=auto_submit)
