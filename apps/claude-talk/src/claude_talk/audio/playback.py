"""Audio playback to speaker."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

import numpy as np
import sounddevice as sd

from claude_talk.utils.logging import get_logger

logger = get_logger(__name__)


class AudioPlayer:
    """Audio playback to speaker."""

    def __init__(
        self,
        device: int | None = None,
        sample_rate: int = 24000,
    ) -> None:
        """Initialize audio player.

        Args:
            device: Output device index, or None for default.
            sample_rate: Sample rate in Hz.
        """
        self.device = device
        self.sample_rate = sample_rate

    def play(self, audio: np.ndarray, blocking: bool = True) -> None:
        """Play audio data.

        Args:
            audio: Audio data as numpy array.
            blocking: Whether to block until playback is complete.
        """
        if len(audio) == 0:
            logger.warning("Empty audio data, nothing to play")
            return

        logger.info(
            "Playing audio",
            duration=len(audio) / self.sample_rate,
            device=self.device,
        )

        sd.play(
            audio,
            samplerate=self.sample_rate,
            device=self.device,
            blocking=blocking,
        )

    def play_file(self, file_path: str | Path, blocking: bool = True) -> None:
        """Play audio from file.

        Args:
            file_path: Path to audio file (WAV, MP3, etc.).
            blocking: Whether to block until playback is complete.
        """
        # Import here to avoid dependency if not used
        try:
            import wave

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Audio file not found: {path}")

            with wave.open(str(path), "rb") as wf:
                sample_rate = wf.getframerate()
                n_channels = wf.getnchannels()
                n_frames = wf.getnframes()
                audio_bytes = wf.readframes(n_frames)

                # Convert to numpy array
                audio = np.frombuffer(audio_bytes, dtype=np.int16)
                audio = audio.astype(np.float32) / 32768.0

                # Reshape for stereo
                if n_channels > 1:
                    audio = audio.reshape(-1, n_channels)

            logger.info("Playing file", path=str(path), sample_rate=sample_rate)

            sd.play(
                audio,
                samplerate=sample_rate,
                device=self.device,
                blocking=blocking,
            )

        except Exception as e:
            logger.error("Failed to play file", error=str(e))
            raise

    def play_bytes(
        self,
        audio_bytes: bytes,
        sample_rate: int | None = None,
        blocking: bool = True,
    ) -> None:
        """Play audio from bytes (PCM16 format).

        Args:
            audio_bytes: Audio data as bytes (PCM16 format).
            sample_rate: Sample rate, or None to use default.
            blocking: Whether to block until playback is complete.
        """
        if not audio_bytes:
            logger.warning("Empty audio bytes, nothing to play")
            return

        # Convert bytes to numpy array (assuming PCM16)
        audio = np.frombuffer(audio_bytes, dtype=np.int16)
        audio = audio.astype(np.float32) / 32768.0

        sr = sample_rate or self.sample_rate

        logger.info("Playing bytes", length=len(audio_bytes), sample_rate=sr)

        sd.play(
            audio,
            samplerate=sr,
            device=self.device,
            blocking=blocking,
        )

    def stop(self) -> None:
        """Stop current playback."""
        sd.stop()
        logger.info("Playback stopped")

    def wait(self) -> None:
        """Wait for current playback to finish."""
        sd.wait()


async def play_audio_async(
    audio: np.ndarray,
    sample_rate: int = 24000,
    device: int | None = None,
) -> None:
    """Play audio asynchronously.

    Args:
        audio: Audio data as numpy array.
        sample_rate: Sample rate in Hz.
        device: Output device index.
    """
    import asyncio

    loop = asyncio.get_event_loop()
    player = AudioPlayer(device=device, sample_rate=sample_rate)

    await loop.run_in_executor(None, lambda: player.play(audio, blocking=True))
