"""Edge TTS engine (free, high-quality, Microsoft Edge voices)."""

from __future__ import annotations

import asyncio
import io
import tempfile
from pathlib import Path
from typing import Literal

from claude_talk.tts.base import SynthesisResult, TTSEngine
from claude_talk.utils.logging import get_logger

logger = get_logger(__name__)

# Popular Japanese voices
JAPANESE_VOICES = {
    "female": "ja-JP-NanamiNeural",
    "male": "ja-JP-KeitaNeural",
}

# Popular English voices
ENGLISH_VOICES = {
    "female": "en-US-JennyNeural",
    "male": "en-US-GuyNeural",
}


class EdgeTTSEngine(TTSEngine):
    """Edge TTS engine using Microsoft Edge's free TTS service."""

    def __init__(
        self,
        voice: str = "ja-JP-NanamiNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
    ) -> None:
        """Initialize Edge TTS engine.

        Args:
            voice: Voice name (e.g., ja-JP-NanamiNeural).
            rate: Speech rate adjustment (e.g., +20%, -10%).
            volume: Volume adjustment (e.g., +20%, -10%).
            pitch: Pitch adjustment (e.g., +10Hz, -5Hz).
        """
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.pitch = pitch
        self._available = True

        try:
            import edge_tts
            logger.info("Edge TTS engine initialized", voice=voice)
        except ImportError:
            logger.error("edge-tts not installed. Run: pip install edge-tts")
            self._available = False

    async def synthesize(self, text: str) -> SynthesisResult:
        """Synthesize text to speech.

        Args:
            text: Text to synthesize.

        Returns:
            SynthesisResult with MP3 audio data.
        """
        if not self.is_available:
            raise RuntimeError("Edge TTS engine not available")

        if not text or not text.strip():
            logger.warning("Empty text provided for synthesis")
            return SynthesisResult(audio_data=b"", sample_rate=24000)

        try:
            import edge_tts

            communicate = edge_tts.Communicate(
                text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume,
                pitch=self.pitch,
            )

            # Collect audio data
            audio_chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])

            audio_data = b"".join(audio_chunks)

            logger.info(
                "Edge TTS synthesis complete",
                text_length=len(text),
                audio_size=len(audio_data),
            )

            return SynthesisResult(
                audio_data=audio_data,
                sample_rate=24000,  # Edge TTS uses 24kHz
                format="mp3",
            )

        except Exception as e:
            logger.error("Edge TTS synthesis failed", error=str(e))
            raise

    async def synthesize_to_file(self, text: str, output_path: str | Path) -> Path:
        """Synthesize text to speech and save to file.

        Args:
            text: Text to synthesize.
            output_path: Path to save audio file.

        Returns:
            Path to saved audio file.
        """
        if not self.is_available:
            raise RuntimeError("Edge TTS engine not available")

        try:
            import edge_tts

            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            communicate = edge_tts.Communicate(
                text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume,
                pitch=self.pitch,
            )

            await communicate.save(str(path))

            logger.info("Edge TTS saved to file", path=str(path))
            return path

        except Exception as e:
            logger.error("Edge TTS save failed", error=str(e))
            raise

    async def speak(self, text: str) -> None:
        """Synthesize and play text immediately.

        Args:
            text: Text to speak.
        """
        if not text or not text.strip():
            return

        try:
            # Synthesize to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_path = Path(f.name)

            await self.synthesize_to_file(text, temp_path)

            # Play using system command or sounddevice
            await self._play_audio_file(temp_path)

            # Clean up
            temp_path.unlink(missing_ok=True)

        except Exception as e:
            logger.error("Edge TTS speak failed", error=str(e))
            raise

    async def _play_audio_file(self, path: Path) -> None:
        """Play audio file using available method."""
        import subprocess
        import sys

        # Try different playback methods
        if sys.platform == "linux":
            # Try mpv, then ffplay, then aplay
            for player in ["mpv", "ffplay", "aplay"]:
                try:
                    proc = await asyncio.create_subprocess_exec(
                        player,
                        str(path),
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL,
                    )
                    await proc.wait()
                    return
                except FileNotFoundError:
                    continue

            logger.warning("No audio player found. Install mpv or ffmpeg.")

        elif sys.platform == "win32":
            # Use Windows Media Player
            import os
            os.startfile(str(path))
            await asyncio.sleep(2)  # Wait for playback

    @property
    def name(self) -> str:
        """Get engine name."""
        return "edge-tts"

    @property
    def is_available(self) -> bool:
        """Check if engine is available and ready."""
        return self._available


class NotificationTTS:
    """TTS for short notification sounds."""

    def __init__(
        self,
        engine: EdgeTTSEngine | None = None,
        notifications: dict[str, str] | None = None,
    ) -> None:
        """Initialize notification TTS.

        Args:
            engine: TTS engine to use.
            notifications: Dict of notification type to text.
        """
        self.engine = engine or EdgeTTSEngine()
        self.notifications = notifications or {
            "completed": "完了しました",
            "ask": "確認があります",
            "error": "エラーが発生しました",
        }
        self._cache: dict[str, bytes] = {}

    async def notify(
        self,
        notification_type: Literal["completed", "ask", "error"] | str,
    ) -> None:
        """Play a notification sound.

        Args:
            notification_type: Type of notification.
        """
        text = self.notifications.get(notification_type, notification_type)
        await self.engine.speak(text)

    async def preload(self) -> None:
        """Preload all notification sounds into cache."""
        for notif_type, text in self.notifications.items():
            if notif_type not in self._cache:
                result = await self.engine.synthesize(text)
                self._cache[notif_type] = result.audio_data
                logger.info("Preloaded notification", type=notif_type)


async def list_voices(language: str | None = None) -> list[dict]:
    """List available Edge TTS voices.

    Args:
        language: Filter by language code (e.g., 'ja', 'en').

    Returns:
        List of voice information dicts.
    """
    try:
        import edge_tts

        voices = await edge_tts.list_voices()

        if language:
            voices = [v for v in voices if v["Locale"].startswith(language)]

        return voices

    except Exception as e:
        logger.error("Failed to list voices", error=str(e))
        return []
