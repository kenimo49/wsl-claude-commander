"""Base class for Text-to-Speech engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SynthesisResult:
    """Result of text-to-speech synthesis."""

    audio_data: bytes
    sample_rate: int
    duration: float | None = None
    format: str = "mp3"


class TTSEngine(ABC):
    """Abstract base class for TTS engines."""

    @abstractmethod
    async def synthesize(self, text: str) -> SynthesisResult:
        """Synthesize text to speech.

        Args:
            text: Text to synthesize.

        Returns:
            SynthesisResult with audio data.
        """
        pass

    @abstractmethod
    async def synthesize_to_file(self, text: str, output_path: str | Path) -> Path:
        """Synthesize text to speech and save to file.

        Args:
            text: Text to synthesize.
            output_path: Path to save audio file.

        Returns:
            Path to saved audio file.
        """
        pass

    @abstractmethod
    async def speak(self, text: str) -> None:
        """Synthesize and play text immediately.

        Args:
            text: Text to speak.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get engine name."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if engine is available and ready."""
        pass
