"""Porcupine hotword detection engine."""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Callable

import numpy as np

from claude_talk.utils.logging import get_logger

logger = get_logger(__name__)


class PorcupineHotwordDetector:
    """Hotword detection using Picovoice Porcupine.

    Note: Porcupine requires an access key from Picovoice Console.
    Free tier allows personal use with limited wake words.
    """

    def __init__(
        self,
        access_key: str | None = None,
        keyword: str = "hey google",  # Built-in keyword (free)
        sensitivity: float = 0.5,
    ) -> None:
        """Initialize Porcupine hotword detector.

        Args:
            access_key: Picovoice access key. Get one at https://console.picovoice.ai/
            keyword: Keyword to detect. Built-in options include:
                     'alexa', 'hey google', 'hey siri', 'ok google', 'picovoice', etc.
            sensitivity: Detection sensitivity (0.0-1.0).
        """
        self.access_key = access_key
        self.keyword = keyword
        self.sensitivity = sensitivity

        self._porcupine = None
        self._sample_rate: int = 16000
        self._frame_length: int = 512

        self._initialize()

    def _initialize(self) -> None:
        """Initialize Porcupine engine."""
        if not self.access_key:
            logger.warning(
                "Porcupine access key not provided. "
                "Get a free key at https://console.picovoice.ai/"
            )
            return

        try:
            import pvporcupine

            # Get available keywords
            available_keywords = pvporcupine.KEYWORDS

            if self.keyword.lower() not in [k.lower() for k in available_keywords]:
                logger.warning(
                    "Keyword not available",
                    keyword=self.keyword,
                    available=available_keywords,
                )
                # Try to use first available keyword
                if available_keywords:
                    self.keyword = available_keywords[0]
                    logger.info("Using fallback keyword", keyword=self.keyword)

            self._porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=[self.keyword],
                sensitivities=[self.sensitivity],
            )

            self._sample_rate = self._porcupine.sample_rate
            self._frame_length = self._porcupine.frame_length

            logger.info(
                "Porcupine initialized",
                keyword=self.keyword,
                sample_rate=self._sample_rate,
                frame_length=self._frame_length,
            )

        except ImportError:
            logger.error("pvporcupine not installed. Run: pip install pvporcupine")
        except Exception as e:
            logger.error("Failed to initialize Porcupine", error=str(e))

    def process(self, audio_frame: np.ndarray) -> bool:
        """Process audio frame and detect hotword.

        Args:
            audio_frame: Audio frame as numpy array (int16, mono).
                        Must be exactly frame_length samples.

        Returns:
            True if hotword detected, False otherwise.
        """
        if not self.is_available:
            return False

        try:
            # Convert float32 to int16 if needed
            if audio_frame.dtype == np.float32:
                audio_frame = (audio_frame * 32767).astype(np.int16)

            # Ensure correct length
            if len(audio_frame) != self._frame_length:
                logger.warning(
                    "Invalid frame length",
                    expected=self._frame_length,
                    got=len(audio_frame),
                )
                return False

            # Process frame
            keyword_index = self._porcupine.process(audio_frame)

            if keyword_index >= 0:
                logger.info("Hotword detected", keyword=self.keyword)
                return True

            return False

        except Exception as e:
            logger.error("Porcupine processing failed", error=str(e))
            return False

    def process_audio(self, audio: np.ndarray) -> list[int]:
        """Process longer audio and find all hotword occurrences.

        Args:
            audio: Audio data as numpy array.

        Returns:
            List of sample indices where hotword was detected.
        """
        if not self.is_available:
            return []

        detections = []

        # Convert float32 to int16 if needed
        if audio.dtype == np.float32:
            audio = (audio * 32767).astype(np.int16)

        # Process in frames
        for i in range(0, len(audio) - self._frame_length, self._frame_length):
            frame = audio[i : i + self._frame_length]
            if self.process(frame):
                detections.append(i)

        return detections

    @property
    def sample_rate(self) -> int:
        """Get required sample rate."""
        return self._sample_rate

    @property
    def frame_length(self) -> int:
        """Get required frame length."""
        return self._frame_length

    @property
    def is_available(self) -> bool:
        """Check if detector is available."""
        return self._porcupine is not None

    def close(self) -> None:
        """Release Porcupine resources."""
        if self._porcupine:
            self._porcupine.delete()
            self._porcupine = None
            logger.info("Porcupine released")

    def __enter__(self) -> "PorcupineHotwordDetector":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


class SimpleHotwordDetector:
    """Simple hotword detection without external dependencies.

    Uses basic energy-based voice activity detection as a fallback.
    Not as accurate as Porcupine but works without API key.
    """

    def __init__(
        self,
        trigger_phrase: str = "hey claude",
        energy_threshold: float = 0.02,
    ) -> None:
        """Initialize simple hotword detector.

        Args:
            trigger_phrase: Phrase to detect (for logging only).
            energy_threshold: Energy threshold for voice activity.
        """
        self.trigger_phrase = trigger_phrase
        self.energy_threshold = energy_threshold
        self._sample_rate = 16000
        self._frame_length = 512

        logger.info(
            "Simple hotword detector initialized (energy-based)",
            trigger_phrase=trigger_phrase,
        )

    def process(self, audio_frame: np.ndarray) -> bool:
        """Process audio frame.

        Note: This only detects voice activity, not the actual hotword.
        Use Porcupine for real hotword detection.

        Args:
            audio_frame: Audio frame as numpy array.

        Returns:
            True if voice activity detected.
        """
        # Convert to float if needed
        if audio_frame.dtype == np.int16:
            audio_frame = audio_frame.astype(np.float32) / 32768.0

        # Calculate RMS energy
        energy = np.sqrt(np.mean(audio_frame**2))

        return energy > self.energy_threshold

    @property
    def sample_rate(self) -> int:
        """Get required sample rate."""
        return self._sample_rate

    @property
    def frame_length(self) -> int:
        """Get required frame length."""
        return self._frame_length

    @property
    def is_available(self) -> bool:
        """Always available."""
        return True

    def close(self) -> None:
        """No resources to release."""
        pass

    def __enter__(self) -> "SimpleHotwordDetector":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


def get_available_keywords() -> list[str]:
    """Get list of available Porcupine keywords.

    Returns:
        List of available keyword names.
    """
    try:
        import pvporcupine
        return list(pvporcupine.KEYWORDS)
    except ImportError:
        return []
    except Exception:
        return []
