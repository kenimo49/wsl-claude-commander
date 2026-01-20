"""Text-to-Speech (TTS) modules."""

from claude_talk.tts.base import SynthesisResult, TTSEngine
from claude_talk.tts.edge_tts_engine import (
    EdgeTTSEngine,
    NotificationTTS,
    list_voices,
)

__all__ = [
    "EdgeTTSEngine",
    "NotificationTTS",
    "SynthesisResult",
    "TTSEngine",
    "list_voices",
]
