"""Configuration loading and validation."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator


class STTFreeConfig(BaseModel):
    """Free STT engine (Vosk) configuration."""

    engine: Literal["vosk"] = "vosk"
    language: str = "ja"
    model_path: str = "~/.claude-talk/models/vosk-model-small-ja-0.22"


class STTPaidConfig(BaseModel):
    """Paid STT engine (OpenAI) configuration."""

    engine: Literal["openai"] = "openai"
    api_key: str = "${OPENAI_API_KEY}"
    language: str = "ja"
    model: str = "whisper-1"


class STTConfig(BaseModel):
    """Speech-to-Text configuration."""

    mode: Literal["free", "paid"] = "free"
    free: STTFreeConfig = Field(default_factory=STTFreeConfig)
    paid: STTPaidConfig = Field(default_factory=STTPaidConfig)


class TTSNotifyConfig(BaseModel):
    """TTS notify mode configuration."""

    speaker: int | None = None
    sounds: dict[str, str] = Field(
        default_factory=lambda: {
            "completed": "完了しました",
            "ask": "確認があります",
            "error": "エラーが発生しました",
        }
    )


class TTSConfig(BaseModel):
    """Text-to-Speech configuration."""

    engine: Literal["edge-tts"] = "edge-tts"
    voice: str = "ja-JP-NanamiNeural"
    mode: Literal["full", "notify"] = "full"
    rate: str = "+0%"
    volume: str = "+0%"
    notify: TTSNotifyConfig = Field(default_factory=TTSNotifyConfig)


class HotwordConfig(BaseModel):
    """Hotword detection configuration."""

    engine: Literal["porcupine", "simple"] = "simple"
    word: str = "hey google"  # Built-in Porcupine keyword
    threshold: float = 0.5
    # Porcupine access key (get free key at https://console.picovoice.ai/)
    access_key: str = "${PICOVOICE_ACCESS_KEY}"

    @field_validator("threshold")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("threshold must be between 0.0 and 1.0")
        return v


class ClaudeConfig(BaseModel):
    """Claude integration configuration."""

    window_title: str = "claude"
    restore_window: bool = True
    monitor_method: Literal["log", "terminal"] = "log"
    log_path: str | None = None
    # Prefix to add to voice input (e.g., "[音声入力] ")
    voice_input_prefix: str | None = "[音声入力] "


class VADConfig(BaseModel):
    """Voice Activity Detection configuration."""

    enabled: bool = True
    aggressiveness: int = 2
    silence_duration: int = 1500
    min_speech_duration: int = 500

    @field_validator("aggressiveness")
    @classmethod
    def validate_aggressiveness(cls, v: int) -> int:
        if not 0 <= v <= 3:
            raise ValueError("aggressiveness must be between 0 and 3")
        return v


class AudioConfig(BaseModel):
    """Audio device configuration."""

    # Device can be: int (index), str (name/partial match), or None (default)
    input_device: int | str | None = None
    output_device: int | str | None = None
    sample_rate: int = 16000
    chunk_size: int = 1024
    vad: VADConfig = Field(default_factory=VADConfig)


class DaemonConfig(BaseModel):
    """Daemon configuration."""

    pid_file: str = "~/.claude-talk/claude-talk.pid"
    log_file: str = "~/.claude-talk/claude-talk.log"
    log_level: Literal["debug", "info", "warning", "error"] = "info"


class Config(BaseModel):
    """Main configuration."""

    stt: STTConfig = Field(default_factory=STTConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    hotword: HotwordConfig = Field(default_factory=HotwordConfig)
    claude: ClaudeConfig = Field(default_factory=ClaudeConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    daemon: DaemonConfig = Field(default_factory=DaemonConfig)


def expand_env_vars(value: str) -> str:
    """Expand environment variables in string (${VAR} format)."""
    pattern = r"\$\{([^}]+)\}"

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        return os.environ.get(var_name, "")

    return re.sub(pattern, replacer, value)


def expand_path(path: str) -> Path:
    """Expand ~ and environment variables in path."""
    expanded = expand_env_vars(path)
    return Path(expanded).expanduser()


def load_config(config_path: str | Path) -> Config:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration file.

    Returns:
        Loaded configuration.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config file is invalid.
    """
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Config file '{path}' not found.\n\n"
            "Hint: Run 'claude-talk init' to create a new config file."
        )

    with open(path, encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)

    if raw_config is None:
        raw_config = {}

    # Expand environment variables in API key
    if "stt" in raw_config and "paid" in raw_config["stt"]:
        if "api_key" in raw_config["stt"]["paid"]:
            raw_config["stt"]["paid"]["api_key"] = expand_env_vars(
                raw_config["stt"]["paid"]["api_key"]
            )

    try:
        return Config.model_validate(raw_config)
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}") from e


def create_default_config(config_path: str | Path, force: bool = False) -> Path:
    """Create default configuration file.

    Args:
        config_path: Path to create configuration file.
        force: Overwrite existing file if True.

    Returns:
        Path to created configuration file.

    Raises:
        FileExistsError: If file exists and force is False.
    """
    path = Path(config_path)

    if path.exists() and not force:
        raise FileExistsError(
            f"Config file '{path}' already exists.\n\n"
            "Hint: Use --force to overwrite."
        )

    # Read example config
    example_path = Path(__file__).parent.parent.parent / "config.example.yaml"

    if example_path.exists():
        content = example_path.read_text(encoding="utf-8")
    else:
        # Fallback to minimal config
        content = """\
# claude-talk configuration

stt:
  mode: "free"

tts:
  mode: "full"
  voice: "ja-JP-NanamiNeural"

hotword:
  word: "hey_claude"
  threshold: 0.5

claude:
  window_title: "claude"

audio:
  input_device: null
  output_device: null
"""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    return path
