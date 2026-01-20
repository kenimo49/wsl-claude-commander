"""Path utilities."""

from __future__ import annotations

import os
import re
from pathlib import Path


def expand_env_vars(value: str) -> str:
    """Expand environment variables in string (${VAR} format).

    Args:
        value: String potentially containing ${VAR} patterns.

    Returns:
        String with environment variables expanded.
    """
    pattern = r"\$\{([^}]+)\}"

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        return os.environ.get(var_name, "")

    return re.sub(pattern, replacer, value)


def expand_path(path: str | Path) -> Path:
    """Expand ~ and environment variables in path.

    Args:
        path: Path string or Path object.

    Returns:
        Expanded Path object.
    """
    if isinstance(path, Path):
        path = str(path)
    expanded = expand_env_vars(path)
    return Path(expanded).expanduser().resolve()


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists, creating it if necessary.

    Args:
        path: Directory path.

    Returns:
        The same path after ensuring it exists.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_data_dir() -> Path:
    """Get claude-talk data directory.

    Returns:
        Path to data directory (~/.claude-talk/).
    """
    return expand_path("~/.claude-talk")


def get_models_dir() -> Path:
    """Get models directory.

    Returns:
        Path to models directory (~/.claude-talk/models/).
    """
    return get_data_dir() / "models"
