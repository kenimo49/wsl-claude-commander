"""Hotword detection modules."""

from claude_talk.hotword.porcupine import (
    PorcupineHotwordDetector,
    SimpleHotwordDetector,
    get_available_keywords,
)

__all__ = [
    "PorcupineHotwordDetector",
    "SimpleHotwordDetector",
    "get_available_keywords",
]
