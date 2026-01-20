"""Vosk-based Speech-to-Text engine (free, local, CPU-optimized)."""

from __future__ import annotations

import json
import tempfile
import wave
from pathlib import Path

import numpy as np

from claude_talk.stt.base import STTEngine, TranscriptionResult
from claude_talk.utils.logging import get_logger
from claude_talk.utils.paths import ensure_dir, expand_path

logger = get_logger(__name__)

# Vosk model URLs for different languages
VOSK_MODELS = {
    "ja": {
        "small": "vosk-model-small-ja-0.22",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-ja-0.22.zip",
    },
    "en": {
        "small": "vosk-model-small-en-us-0.15",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
    },
}


class VoskEngine(STTEngine):
    """Vosk-based STT engine for local, CPU-optimized transcription."""

    def __init__(
        self,
        model_path: str | None = None,
        language: str = "ja",
        sample_rate: int = 16000,
    ) -> None:
        """Initialize Vosk engine.

        Args:
            model_path: Path to Vosk model directory.
            language: Language code (ja, en, etc.).
            sample_rate: Expected sample rate of audio.
        """
        self.language = language
        self.sample_rate = sample_rate
        self._model = None
        self._recognizer = None

        # Determine model path
        if model_path:
            self._model_path = expand_path(model_path)
        else:
            # Default model path
            model_name = VOSK_MODELS.get(language, VOSK_MODELS["en"])["small"]
            self._model_path = expand_path(f"~/.claude-talk/models/{model_name}")

        self._initialize()

    def _initialize(self) -> None:
        """Initialize Vosk model and recognizer."""
        try:
            from vosk import Model, KaldiRecognizer, SetLogLevel

            # Suppress Vosk logs
            SetLogLevel(-1)

            if not self._model_path.exists():
                logger.warning(
                    "Vosk model not found",
                    path=str(self._model_path),
                    hint="Run 'claude-talk download-model' to download",
                )
                return

            logger.info("Loading Vosk model", path=str(self._model_path))
            self._model = Model(str(self._model_path))
            self._recognizer = KaldiRecognizer(self._model, self.sample_rate)
            logger.info("Vosk model loaded successfully")

        except ImportError:
            logger.error("Vosk not installed. Run: pip install vosk")
        except Exception as e:
            logger.error("Failed to initialize Vosk", error=str(e))

    def _audio_to_pcm16(self, audio: np.ndarray) -> bytes:
        """Convert float32 audio to PCM16 bytes."""
        # Ensure audio is float32 and in range [-1, 1]
        audio = np.clip(audio, -1.0, 1.0)
        # Convert to int16
        audio_int16 = (audio * 32767).astype(np.int16)
        return audio_int16.tobytes()

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> TranscriptionResult:
        """Transcribe audio to text using Vosk.

        Args:
            audio: Audio data as numpy array (float32, mono).
            sample_rate: Sample rate of audio in Hz.

        Returns:
            TranscriptionResult with transcribed text.
        """
        if not self.is_available:
            logger.error("Vosk engine not available")
            return TranscriptionResult(text="", confidence=0.0)

        try:
            from vosk import KaldiRecognizer

            # Create new recognizer for each transcription
            recognizer = KaldiRecognizer(self._model, sample_rate)

            # Convert audio to PCM16 bytes
            audio_bytes = self._audio_to_pcm16(audio)

            # Process audio
            recognizer.AcceptWaveform(audio_bytes)
            result = json.loads(recognizer.FinalResult())

            text = result.get("text", "")
            duration = len(audio) / sample_rate

            logger.info("Vosk transcription complete", text=text[:50] if text else "(empty)")

            return TranscriptionResult(
                text=text,
                confidence=None,  # Vosk doesn't provide confidence
                language=self.language,
                duration=duration,
            )

        except Exception as e:
            logger.error("Vosk transcription failed", error=str(e))
            return TranscriptionResult(text="", confidence=0.0)

    def transcribe_file(self, file_path: str) -> TranscriptionResult:
        """Transcribe audio file to text.

        Args:
            file_path: Path to audio file (WAV format).

        Returns:
            TranscriptionResult with transcribed text.
        """
        if not self.is_available:
            logger.error("Vosk engine not available")
            return TranscriptionResult(text="", confidence=0.0)

        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Audio file not found: {path}")

            with wave.open(str(path), "rb") as wf:
                if wf.getnchannels() != 1:
                    raise ValueError("Audio must be mono")

                sample_rate = wf.getframerate()
                audio_bytes = wf.readframes(wf.getnframes())

                # Convert to numpy array
                audio = np.frombuffer(audio_bytes, dtype=np.int16)
                audio = audio.astype(np.float32) / 32768.0

            return self.transcribe(audio, sample_rate)

        except Exception as e:
            logger.error("Failed to transcribe file", error=str(e))
            return TranscriptionResult(text="", confidence=0.0)

    @property
    def name(self) -> str:
        """Get engine name."""
        return "vosk"

    @property
    def is_available(self) -> bool:
        """Check if engine is available and ready."""
        return self._model is not None

    @property
    def model_path(self) -> Path:
        """Get model path."""
        return self._model_path


def download_vosk_model(language: str = "ja", target_dir: str | None = None) -> Path:
    """Download Vosk model for specified language.

    Args:
        language: Language code.
        target_dir: Target directory for model.

    Returns:
        Path to downloaded model directory.
    """
    import io
    import zipfile

    import requests

    if language not in VOSK_MODELS:
        raise ValueError(f"Unsupported language: {language}")

    model_info = VOSK_MODELS[language]
    model_name = model_info["small"]
    url = model_info["url"]

    if target_dir:
        base_dir = expand_path(target_dir)
    else:
        base_dir = expand_path("~/.claude-talk/models")

    ensure_dir(base_dir)
    model_path = base_dir / model_name

    if model_path.exists():
        logger.info("Model already exists", path=str(model_path))
        return model_path

    logger.info("Downloading Vosk model", url=url)

    response = requests.get(url, stream=True)
    response.raise_for_status()

    # Extract zip file
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        zf.extractall(base_dir)

    logger.info("Model downloaded", path=str(model_path))
    return model_path
