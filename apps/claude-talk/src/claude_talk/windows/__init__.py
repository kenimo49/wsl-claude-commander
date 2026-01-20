"""Windows integration modules (PowerShell, clipboard, window operations)."""

from claude_talk.windows.clipboard import get_clipboard, set_clipboard
from claude_talk.windows.input_sender import ClaudeInputSender, send_keys, send_to_claude
from claude_talk.windows.window_ops import (
    WindowInfo,
    activate_window,
    find_claude_window,
    find_window,
    get_foreground_window,
    get_windows,
)

__all__ = [
    "ClaudeInputSender",
    "WindowInfo",
    "activate_window",
    "find_claude_window",
    "find_window",
    "get_clipboard",
    "get_foreground_window",
    "get_windows",
    "send_keys",
    "send_to_claude",
    "set_clipboard",
]
