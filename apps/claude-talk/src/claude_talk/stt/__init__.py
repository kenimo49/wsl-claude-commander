"""Speech-to-Text (STT) modules."""

from claude_talk.stt.base import STTEngine, TranscriptionResult
from claude_talk.stt.openai_engine import OpenAIWhisperEngine
from claude_talk.stt.vosk_engine import VoskEngine, download_vosk_model

__all__ = [
    "STTEngine",
    "TranscriptionResult",
    "VoskEngine",
    "OpenAIWhisperEngine",
    "download_vosk_model",
]
