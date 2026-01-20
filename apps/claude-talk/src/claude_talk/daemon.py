"""Daemon management for claude-talk."""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from pathlib import Path
from typing import Callable

import numpy as np

from claude_talk.config import Config
from claude_talk.utils.logging import get_logger, setup_logging
from claude_talk.utils.paths import expand_path

logger = get_logger(__name__)


class VoiceDaemon:
    """Main daemon for voice input/output processing."""

    def __init__(self, config: Config) -> None:
        """Initialize voice daemon.

        Args:
            config: Application configuration.
        """
        self.config = config
        self._running = False
        self._stt_engine = None
        self._tts_engine = None
        self._hotword_detector = None
        self._input_sender = None

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""

        def handle_signal(signum: int, frame) -> None:
            logger.info("Received signal, shutting down", signal=signum)
            self._running = False

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

    def _initialize_components(self) -> None:
        """Initialize all components based on config."""
        # Initialize STT engine
        if self.config.stt.mode == "free":
            from claude_talk.stt import VoskEngine

            self._stt_engine = VoskEngine(
                model_path=self.config.stt.free.model_path,
                language=self.config.stt.free.language,
            )
        else:
            from claude_talk.stt import OpenAIWhisperEngine

            self._stt_engine = OpenAIWhisperEngine(
                api_key=self.config.stt.paid.api_key,
                language=self.config.stt.paid.language,
            )

        # Initialize TTS engine
        from claude_talk.tts import EdgeTTSEngine

        self._tts_engine = EdgeTTSEngine(
            voice=self.config.tts.voice,
            rate=self.config.tts.rate,
            volume=self.config.tts.volume,
        )

        # Initialize hotword detector
        from claude_talk.hotword import SimpleHotwordDetector

        self._hotword_detector = SimpleHotwordDetector(
            trigger_phrase=self.config.hotword.word,
        )

        # Initialize input sender
        from claude_talk.windows import ClaudeInputSender

        self._input_sender = ClaudeInputSender(
            window_title=self.config.claude.window_title,
            restore_window=self.config.claude.restore_window,
        )

        logger.info("All components initialized")

    async def _process_voice_input(self) -> str | None:
        """Record and transcribe voice input.

        Returns:
            Transcribed text, or None if failed.
        """
        try:
            from claude_talk.audio import AudioRecorder

            recorder = AudioRecorder(
                device=self.config.audio.input_device,
                sample_rate=self.config.audio.sample_rate,
                silence_threshold=0.03,  # Higher threshold for noisy environments
                silence_duration=self.config.audio.vad.silence_duration / 1000.0,
                max_duration=10.0,  # Limit to 10 seconds for better recognition
            )

            logger.info("Recording voice input...")
            audio = recorder.record()

            if audio is None or len(audio) == 0:
                logger.warning("No audio recorded")
                return None

            logger.info("Transcribing...")
            result = self._stt_engine.transcribe(audio, self.config.audio.sample_rate)

            if result.is_empty:
                logger.info("No speech detected")
                return None

            logger.info("Transcribed", text=result.text[:50])
            return result.text

        except Exception as e:
            logger.error("Voice input processing failed", error=str(e))
            return None

    async def _speak(self, text: str) -> None:
        """Speak text using TTS.

        Args:
            text: Text to speak.
        """
        try:
            await self._tts_engine.speak(text)
        except Exception as e:
            logger.error("TTS failed", error=str(e))

    async def _main_loop(self) -> None:
        """Main processing loop."""
        logger.info("Starting main loop")
        logger.info("Listening for voice activity...")

        # Notify start (temporarily disabled for testing)
        # if self.config.tts.mode == "full":
        #     await self._speak("claude-talk を開始しました")
        logger.info("TTS notification skipped for testing")

        # Import audio capture
        from claude_talk.audio import AudioCapture

        # Create audio capture for continuous monitoring
        capture = AudioCapture(
            device=self.config.audio.input_device,
            sample_rate=self.config.audio.sample_rate,
            chunk_size=self.config.audio.chunk_size,
        )

        # Voice activity detection parameters
        energy_threshold = 0.02  # RMS threshold for voice activity
        activation_chunks = 3  # Number of chunks above threshold to start recording
        active_count = 0

        logger.info("Starting audio monitoring", threshold=energy_threshold)

        try:
            capture.start()

            while self._running:
                try:
                    # Read audio chunk (non-blocking with timeout)
                    audio_chunk = capture.read(timeout=0.1)
                    if audio_chunk is None:
                        await asyncio.sleep(0.01)
                        continue

                    # Calculate energy (RMS)
                    energy = float(np.sqrt(np.mean(audio_chunk**2)))

                    # Check for voice activity
                    if energy > energy_threshold:
                        active_count += 1
                        if active_count >= activation_chunks:
                            logger.info("Voice activity detected", energy=f"{energy:.4f}")

                            # Stop monitoring capture
                            capture.stop()

                            # Record full utterance
                            text = await self._process_voice_input()

                            if text:
                                logger.info("=== Recognized ===", text=text)

                                # TODO: Send to Claude
                                # For now, just speak back the recognized text
                                if self.config.tts.mode == "full":
                                    await self._speak(f"認識しました: {text[:50]}")

                            # Reset and restart monitoring
                            active_count = 0
                            capture.start()
                            logger.info("Resuming audio monitoring...")
                    else:
                        active_count = 0

                    # Small delay to prevent CPU spinning
                    await asyncio.sleep(0.01)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("Error in main loop iteration", error=str(e))
                    await asyncio.sleep(0.5)

        finally:
            capture.stop()

    def run_foreground(self) -> None:
        """Run daemon in foreground mode."""
        self._setup_signal_handlers()
        self._running = True

        # Set up logging
        setup_logging(level=self.config.daemon.log_level)

        logger.info("Starting claude-talk in foreground mode")

        try:
            self._initialize_components()
            asyncio.run(self._main_loop())
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self._cleanup()

        logger.info("claude-talk stopped")

    def _cleanup(self) -> None:
        """Clean up resources."""
        if self._hotword_detector:
            self._hotword_detector.close()

        logger.info("Cleanup complete")


class PidFile:
    """PID file management for daemon mode."""

    def __init__(self, path: str | Path) -> None:
        """Initialize PID file manager.

        Args:
            path: Path to PID file.
        """
        self.path = expand_path(path)

    def write(self) -> None:
        """Write current process PID to file."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(str(os.getpid()))
        logger.info("PID file written", path=str(self.path), pid=os.getpid())

    def read(self) -> int | None:
        """Read PID from file.

        Returns:
            PID if file exists and is valid, None otherwise.
        """
        if not self.path.exists():
            return None

        try:
            return int(self.path.read_text().strip())
        except ValueError:
            return None

    def remove(self) -> None:
        """Remove PID file."""
        if self.path.exists():
            self.path.unlink()
            logger.info("PID file removed", path=str(self.path))

    def is_running(self) -> bool:
        """Check if process with PID is running.

        Returns:
            True if process is running.
        """
        pid = self.read()
        if pid is None:
            return False

        try:
            os.kill(pid, 0)  # Signal 0 = check if process exists
            return True
        except OSError:
            return False


def start_daemon(config: Config, foreground: bool = False) -> None:
    """Start the voice daemon.

    Args:
        config: Application configuration.
        foreground: Run in foreground mode.
    """
    pid_file = PidFile(config.daemon.pid_file)

    if pid_file.is_running():
        logger.error("Daemon is already running", pid=pid_file.read())
        sys.exit(1)

    daemon = VoiceDaemon(config)

    if foreground:
        daemon.run_foreground()
    else:
        # TODO: Implement proper daemonization
        # For now, just run in foreground
        logger.warning("Background mode not yet implemented, running in foreground")
        daemon.run_foreground()


def stop_daemon(config: Config) -> None:
    """Stop the voice daemon.

    Args:
        config: Application configuration.
    """
    pid_file = PidFile(config.daemon.pid_file)

    pid = pid_file.read()
    if pid is None:
        logger.info("Daemon is not running (no PID file)")
        return

    if not pid_file.is_running():
        logger.info("Daemon is not running (process not found)")
        pid_file.remove()
        return

    try:
        os.kill(pid, signal.SIGTERM)
        logger.info("Sent SIGTERM to daemon", pid=pid)
    except OSError as e:
        logger.error("Failed to stop daemon", error=str(e))


def get_daemon_status(config: Config) -> dict:
    """Get daemon status.

    Args:
        config: Application configuration.

    Returns:
        Status dictionary.
    """
    pid_file = PidFile(config.daemon.pid_file)

    pid = pid_file.read()
    running = pid_file.is_running()

    return {
        "running": running,
        "pid": pid if running else None,
        "pid_file": str(pid_file.path),
    }
