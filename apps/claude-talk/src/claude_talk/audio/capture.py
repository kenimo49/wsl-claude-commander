"""Audio capture from microphone."""

from __future__ import annotations

import queue
import threading
from typing import Callable

import numpy as np
import sounddevice as sd

from claude_talk.utils.logging import get_logger

logger = get_logger(__name__)


class AudioCapture:
    """Audio capture from microphone with callback support."""

    def __init__(
        self,
        device: int | None = None,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 1024,
    ) -> None:
        """Initialize audio capture.

        Args:
            device: Input device index, or None for default.
            sample_rate: Sample rate in Hz.
            channels: Number of audio channels.
            chunk_size: Samples per chunk.
        """
        self.device = device
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size

        self._stream: sd.InputStream | None = None
        self._queue: queue.Queue[np.ndarray] = queue.Queue()
        self._callback: Callable[[np.ndarray], None] | None = None
        self._running = False

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: dict,
        status: sd.CallbackFlags,
    ) -> None:
        """Internal callback for audio stream."""
        if status:
            logger.warning("Audio capture status", status=str(status))

        # Copy audio data
        audio_data = indata.copy().flatten()

        # Put in queue
        self._queue.put(audio_data)

        # Call user callback if set
        if self._callback:
            self._callback(audio_data)

    def start(self, callback: Callable[[np.ndarray], None] | None = None) -> None:
        """Start audio capture.

        Args:
            callback: Optional callback function for each audio chunk.
        """
        if self._running:
            logger.warning("Audio capture already running")
            return

        self._callback = callback
        self._running = True

        # Clear queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

        self._stream = sd.InputStream(
            device=self.device,
            samplerate=self.sample_rate,
            channels=self.channels,
            blocksize=self.chunk_size,
            dtype=np.float32,
            callback=self._audio_callback,
        )
        self._stream.start()

        logger.info(
            "Audio capture started",
            device=self.device,
            sample_rate=self.sample_rate,
        )

    def stop(self) -> None:
        """Stop audio capture."""
        if not self._running:
            return

        self._running = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        logger.info("Audio capture stopped")

    def read(self, timeout: float | None = None) -> np.ndarray | None:
        """Read audio data from queue.

        Args:
            timeout: Timeout in seconds, or None to block.

        Returns:
            Audio data as numpy array, or None if timeout.
        """
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def read_all(self) -> np.ndarray:
        """Read all available audio data from queue.

        Returns:
            Concatenated audio data as numpy array.
        """
        chunks = []
        while not self._queue.empty():
            try:
                chunks.append(self._queue.get_nowait())
            except queue.Empty:
                break

        if not chunks:
            return np.array([], dtype=np.float32)

        return np.concatenate(chunks)

    @property
    def is_running(self) -> bool:
        """Check if capture is running."""
        return self._running

    def __enter__(self) -> "AudioCapture":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


class AudioRecorder:
    """Record audio with automatic silence detection."""

    def __init__(
        self,
        device: int | None = None,
        sample_rate: int = 16000,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.5,
        min_duration: float = 0.5,
        max_duration: float = 30.0,
    ) -> None:
        """Initialize audio recorder.

        Args:
            device: Input device index.
            sample_rate: Sample rate in Hz.
            silence_threshold: RMS threshold for silence detection.
            silence_duration: Silence duration to stop recording (seconds).
            min_duration: Minimum recording duration (seconds).
            max_duration: Maximum recording duration (seconds).
        """
        self.device = device
        self.sample_rate = sample_rate
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.min_duration = min_duration
        self.max_duration = max_duration

        self._capture: AudioCapture | None = None
        self._recording = False
        self._audio_chunks: list[np.ndarray] = []

    def _calculate_rms(self, audio: np.ndarray) -> float:
        """Calculate RMS (Root Mean Square) of audio."""
        return float(np.sqrt(np.mean(audio**2)))

    def record(self) -> np.ndarray | None:
        """Record audio until silence is detected.

        Returns:
            Recorded audio as numpy array, or None if too short.
        """
        self._audio_chunks = []
        self._recording = True

        silence_samples = 0
        silence_threshold_samples = int(self.silence_duration * self.sample_rate)
        min_samples = int(self.min_duration * self.sample_rate)
        max_samples = int(self.max_duration * self.sample_rate)
        total_samples = 0

        self._capture = AudioCapture(
            device=self.device,
            sample_rate=self.sample_rate,
        )

        logger.info("Recording started")

        with self._capture:
            while self._recording:
                audio = self._capture.read(timeout=0.1)
                if audio is None:
                    continue

                self._audio_chunks.append(audio)
                total_samples += len(audio)

                # Check for silence
                rms = self._calculate_rms(audio)
                if rms < self.silence_threshold:
                    silence_samples += len(audio)
                else:
                    silence_samples = 0

                # Stop conditions
                if total_samples >= max_samples:
                    logger.info("Max duration reached")
                    break

                if (
                    silence_samples >= silence_threshold_samples
                    and total_samples >= min_samples
                ):
                    logger.info("Silence detected, stopping")
                    break

        self._recording = False

        if not self._audio_chunks:
            return None

        audio = np.concatenate(self._audio_chunks)

        if len(audio) < min_samples:
            logger.warning("Recording too short, discarding")
            return None

        logger.info("Recording finished", duration=len(audio) / self.sample_rate)
        return audio

    def stop(self) -> None:
        """Stop recording."""
        self._recording = False
        if self._capture:
            self._capture.stop()
