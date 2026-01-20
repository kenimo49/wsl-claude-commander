"""OpenAI Whisper API-based Speech-to-Text engine (paid, cloud)."""

from __future__ import annotations

import io
import tempfile
import wave
from pathlib import Path

import numpy as np

from claude_talk.stt.base import STTEngine, TranscriptionResult
from claude_talk.utils.logging import get_logger

logger = get_logger(__name__)


class OpenAIWhisperEngine(STTEngine):
    """OpenAI Whisper API-based STT engine."""

    def __init__(
        self,
        api_key: str | None = None,
        language: str = "ja",
        model: str = "whisper-1",
    ) -> None:
        """Initialize OpenAI Whisper engine.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            language: Language code for transcription.
            model: Whisper model name.
        """
        self.language = language
        self.model = model
        self._client = None

        self._initialize(api_key)

    def _initialize(self, api_key: str | None) -> None:
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI

            if api_key:
                self._client = OpenAI(api_key=api_key)
            else:
                # Will use OPENAI_API_KEY env var
                self._client = OpenAI()

            logger.info("OpenAI Whisper engine initialized")

        except ImportError:
            logger.error("OpenAI not installed. Run: pip install openai")
        except Exception as e:
            logger.error("Failed to initialize OpenAI client", error=str(e))

    def _audio_to_wav_bytes(self, audio: np.ndarray, sample_rate: int) -> bytes:
        """Convert numpy audio to WAV bytes."""
        # Convert to int16
        audio_int16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)

        # Create WAV file in memory
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())

        buffer.seek(0)
        return buffer.read()

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> TranscriptionResult:
        """Transcribe audio to text using OpenAI Whisper API.

        Args:
            audio: Audio data as numpy array (float32, mono).
            sample_rate: Sample rate of audio in Hz.

        Returns:
            TranscriptionResult with transcribed text.
        """
        if not self.is_available:
            logger.error("OpenAI Whisper engine not available")
            return TranscriptionResult(text="", confidence=0.0)

        try:
            # Convert audio to WAV bytes
            wav_bytes = self._audio_to_wav_bytes(audio, sample_rate)

            # Create a file-like object with a name attribute
            audio_file = io.BytesIO(wav_bytes)
            audio_file.name = "audio.wav"

            # Call OpenAI Whisper API
            logger.info("Calling OpenAI Whisper API")
            response = self._client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=self.language,
            )

            text = response.text
            duration = len(audio) / sample_rate

            logger.info(
                "OpenAI Whisper transcription complete",
                text=text[:50] if text else "(empty)",
            )

            return TranscriptionResult(
                text=text,
                confidence=None,
                language=self.language,
                duration=duration,
            )

        except Exception as e:
            logger.error("OpenAI Whisper transcription failed", error=str(e))
            return TranscriptionResult(text="", confidence=0.0)

    def transcribe_file(self, file_path: str) -> TranscriptionResult:
        """Transcribe audio file to text.

        Args:
            file_path: Path to audio file.

        Returns:
            TranscriptionResult with transcribed text.
        """
        if not self.is_available:
            logger.error("OpenAI Whisper engine not available")
            return TranscriptionResult(text="", confidence=0.0)

        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Audio file not found: {path}")

            with open(path, "rb") as audio_file:
                logger.info("Calling OpenAI Whisper API", file=str(path))
                response = self._client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language=self.language,
                )

            text = response.text

            logger.info(
                "OpenAI Whisper transcription complete",
                text=text[:50] if text else "(empty)",
            )

            return TranscriptionResult(
                text=text,
                confidence=None,
                language=self.language,
            )

        except Exception as e:
            logger.error("Failed to transcribe file", error=str(e))
            return TranscriptionResult(text="", confidence=0.0)

    @property
    def name(self) -> str:
        """Get engine name."""
        return "openai-whisper"

    @property
    def is_available(self) -> bool:
        """Check if engine is available and ready."""
        return self._client is not None
