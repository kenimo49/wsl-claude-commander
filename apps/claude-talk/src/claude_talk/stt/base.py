"""Base class for Speech-to-Text engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class TranscriptionResult:
    """Result of speech-to-text transcription."""

    text: str
    confidence: float | None = None
    language: str | None = None
    duration: float | None = None

    @property
    def is_empty(self) -> bool:
        """Check if transcription is empty."""
        return not self.text or not self.text.strip()


class STTEngine(ABC):
    """Abstract base class for STT engines."""

    @abstractmethod
    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> TranscriptionResult:
        """Transcribe audio to text.

        Args:
            audio: Audio data as numpy array (float32, mono).
            sample_rate: Sample rate of audio in Hz.

        Returns:
            TranscriptionResult with transcribed text.
        """
        pass

    @abstractmethod
    def transcribe_file(self, file_path: str) -> TranscriptionResult:
        """Transcribe audio file to text.

        Args:
            file_path: Path to audio file.

        Returns:
            TranscriptionResult with transcribed text.
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
