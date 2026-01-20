"""CLI entry point for claude-talk."""

from __future__ import annotations

from pathlib import Path

import click

from claude_talk import __version__
from claude_talk.config import Config, create_default_config, load_config


def get_config_path(ctx: click.Context) -> Path:
    """Get configuration file path from context."""
    return Path(ctx.obj.get("config_path", "config.yaml"))


def load_config_from_ctx(ctx: click.Context) -> Config:
    """Load configuration from context."""
    config_path = get_config_path(ctx)
    return load_config(config_path)


@click.group()
@click.option(
    "-c",
    "--config",
    "config_path",
    default="config.yaml",
    help="Path to config file",
    type=click.Path(),
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
@click.version_option(version=__version__)
@click.pass_context
def main(ctx: click.Context, config_path: str, verbose: bool) -> None:
    """claude-talk: Voice interface for Claude Code.

    Speak to Claude and hear responses.
    """
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config_path
    ctx.obj["verbose"] = verbose


@main.command()
@click.option(
    "--mode",
    type=click.Choice(["free", "paid"]),
    default="free",
    help="STT mode",
)
@click.option("--force", is_flag=True, help="Overwrite existing config")
@click.pass_context
def init(ctx: click.Context, mode: str, force: bool) -> None:
    """Initialize a new configuration file."""
    config_path = get_config_path(ctx)

    try:
        created_path = create_default_config(config_path, force=force)
        click.echo(f"Created configuration file: {created_path}")
        click.echo("\nNext steps:")
        click.echo("  1. Edit the config file to customize settings")
        click.echo("  2. Run 'claude-talk devices' to see available audio devices")
        click.echo("  3. Run 'claude-talk start' to start the daemon")
    except FileExistsError as e:
        raise click.ClickException(str(e)) from e


@main.command()
@click.pass_context
def config(ctx: click.Context) -> None:
    """Show current configuration."""
    try:
        cfg = load_config_from_ctx(ctx)
        click.echo("Current configuration:\n")
        click.echo(f"STT Mode: {cfg.stt.mode}")
        if cfg.stt.mode == "free":
            click.echo(f"  Engine: {cfg.stt.free.engine}")
            click.echo(f"  Language: {cfg.stt.free.language}")
        else:
            click.echo(f"  Engine: {cfg.stt.paid.engine}")
            click.echo(f"  Language: {cfg.stt.paid.language}")
            api_key = cfg.stt.paid.api_key
            if api_key:
                click.echo(f"  API Key: {api_key[:8]}...")
            else:
                click.echo("  API Key: (not set)")

        click.echo(f"\nTTS Mode: {cfg.tts.mode}")
        click.echo(f"  Engine: {cfg.tts.engine}")
        click.echo(f"  Voice: {cfg.tts.voice}")

        click.echo(f"\nHotword: {cfg.hotword.word}")
        click.echo(f"  Threshold: {cfg.hotword.threshold}")

        click.echo(f"\nClaude Window: {cfg.claude.window_title}")
        click.echo(f"  Monitor: {cfg.claude.monitor_method}")

        click.echo(f"\nAudio:")
        click.echo(f"  Input Device: {cfg.audio.input_device or 'default'}")
        click.echo(f"  Output Device: {cfg.audio.output_device or 'default'}")
    except FileNotFoundError as e:
        raise click.ClickException(str(e)) from e
    except ValueError as e:
        raise click.ClickException(str(e)) from e


@main.command()
@click.pass_context
def validate(ctx: click.Context) -> None:
    """Validate configuration file."""
    config_path = get_config_path(ctx)

    try:
        cfg = load_config(config_path)
        click.echo(f"Configuration file '{config_path}' is valid.")

        # Check for potential issues
        warnings = []

        if cfg.stt.mode == "paid" and not cfg.stt.paid.api_key:
            warnings.append("Paid STT mode is enabled but OPENAI_API_KEY is not set")

        if warnings:
            click.echo("\nWarnings:")
            for w in warnings:
                click.echo(f"  - {w}")
    except FileNotFoundError as e:
        raise click.ClickException(str(e)) from e
    except ValueError as e:
        raise click.ClickException(f"Validation failed: {e}") from e


@main.command()
@click.pass_context
def devices(ctx: click.Context) -> None:
    """List available audio devices."""
    try:
        import sounddevice as sd

        click.echo("Available Audio Devices:\n")

        devices = sd.query_devices()
        default_input = sd.default.device[0]
        default_output = sd.default.device[1]

        click.echo("Input Devices (Microphones):")
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0:
                default_mark = " [default]" if i == default_input else ""
                click.echo(f"  {i}. {dev['name']}{default_mark}")

        click.echo("\nOutput Devices (Speakers):")
        for i, dev in enumerate(devices):
            if dev["max_output_channels"] > 0:
                default_mark = " [default]" if i == default_output else ""
                click.echo(f"  {i}. {dev['name']}{default_mark}")

        click.echo("\nUse 'audio.input_device' in config to select a microphone.")
        click.echo("Use 'audio.output_device' in config to select a speaker.")
        click.echo("  Value can be: index (0, 1, ...), name (\"pulse\"), or null (default)")
    except Exception as e:
        raise click.ClickException(f"Failed to list devices: {e}") from e


@main.command()
@click.option("--foreground", is_flag=True, help="Run in foreground")
@click.pass_context
def start(ctx: click.Context, foreground: bool) -> None:
    """Start the voice input daemon."""
    try:
        cfg = load_config_from_ctx(ctx)

        from claude_talk.daemon import start_daemon

        if foreground:
            click.echo("Starting claude-talk in foreground mode...")
            click.echo("Press Ctrl+C to stop.\n")
        else:
            click.echo("Starting claude-talk daemon...")

        start_daemon(cfg, foreground=foreground)

    except FileNotFoundError as e:
        raise click.ClickException(str(e)) from e
    except ValueError as e:
        raise click.ClickException(str(e)) from e


@main.command()
@click.pass_context
def stop(ctx: click.Context) -> None:
    """Stop the voice input daemon."""
    try:
        cfg = load_config_from_ctx(ctx)

        from claude_talk.daemon import stop_daemon

        stop_daemon(cfg)
        click.echo("Stop signal sent.")

    except FileNotFoundError as e:
        raise click.ClickException(str(e)) from e


@main.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show daemon status."""
    try:
        cfg = load_config_from_ctx(ctx)

        from claude_talk.daemon import get_daemon_status

        status_info = get_daemon_status(cfg)

        if status_info["running"]:
            click.echo(f"Daemon Status: Running (PID: {status_info['pid']})")
        else:
            click.echo("Daemon Status: Not running")

        click.echo(f"PID File: {status_info['pid_file']}")

    except FileNotFoundError as e:
        raise click.ClickException(str(e)) from e


@main.command("test-stt")
@click.option("--duration", default=10, help="Test duration in seconds")
@click.option("--file", "audio_file", type=click.Path(exists=True), help="Audio file to transcribe")
@click.pass_context
def test_stt(ctx: click.Context, duration: int, audio_file: str | None) -> None:
    """Test speech-to-text recognition."""
    try:
        cfg = load_config_from_ctx(ctx)

        # Create STT engine based on config
        if cfg.stt.mode == "free":
            from claude_talk.stt import VoskEngine
            engine = VoskEngine(
                model_path=cfg.stt.free.model_path,
                language=cfg.stt.free.language,
            )
            if not engine.is_available:
                click.echo("Vosk model not found.")
                click.echo(f"Expected at: {engine.model_path}")
                click.echo("\nTo download the model, run:")
                click.echo("  claude-talk download-model")
                return
        else:
            from claude_talk.stt import OpenAIWhisperEngine
            engine = OpenAIWhisperEngine(
                api_key=cfg.stt.paid.api_key,
                language=cfg.stt.paid.language,
            )
            if not engine.is_available:
                click.echo("OpenAI client not available. Check your API key.")
                return

        click.echo(f"Using STT engine: {engine.name}")

        if audio_file:
            # Transcribe from file
            click.echo(f"Transcribing file: {audio_file}")
            result = engine.transcribe_file(audio_file)
        else:
            # Record and transcribe
            click.echo(f"Recording for {duration} seconds...")
            click.echo("Speak into the microphone.\n")

            try:
                from claude_talk.audio import AudioRecorder, resolve_device_index
                import numpy as np

                device_index = resolve_device_index(cfg.audio.input_device, is_input=True)
                recorder = AudioRecorder(
                    device=device_index,
                    sample_rate=cfg.audio.sample_rate,
                    silence_duration=cfg.audio.vad.silence_duration / 1000.0,
                    max_duration=float(duration),
                )

                audio = recorder.record()

                if audio is None or len(audio) == 0:
                    click.echo("No audio recorded.")
                    return

                click.echo(f"Recorded {len(audio) / cfg.audio.sample_rate:.1f} seconds")
                result = engine.transcribe(audio, cfg.audio.sample_rate)

            except Exception as e:
                click.echo(f"Audio recording failed: {e}")
                click.echo("\nNote: Audio recording requires PortAudio.")
                click.echo("On Ubuntu: sudo apt-get install libportaudio2")
                return

        click.echo("\n--- Transcription Result ---")
        if result.is_empty:
            click.echo("(No speech detected)")
        else:
            click.echo(f"Text: {result.text}")
            if result.confidence:
                click.echo(f"Confidence: {result.confidence:.2f}")
            if result.duration:
                click.echo(f"Duration: {result.duration:.1f}s")

    except FileNotFoundError as e:
        raise click.ClickException(str(e)) from e
    except ValueError as e:
        raise click.ClickException(str(e)) from e


@main.command("test-tts")
@click.argument("text", required=False)
@click.option(
    "--mode",
    type=click.Choice(["full", "notify"]),
    default="full",
    help="TTS mode to test",
)
@click.option(
    "--type",
    "notify_type",
    type=click.Choice(["completed", "ask", "error"]),
    default="completed",
    help="Notification type (for notify mode)",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Save audio to file instead of playing",
)
@click.pass_context
def test_tts(
    ctx: click.Context,
    text: str | None,
    mode: str,
    notify_type: str,
    output: str | None,
) -> None:
    """Test text-to-speech synthesis."""
    import asyncio

    try:
        cfg = load_config_from_ctx(ctx)

        if mode == "notify":
            text = cfg.tts.notify.sounds.get(notify_type, "テスト")
            click.echo(f"Testing TTS notify mode ({notify_type}): {text}")
        else:
            if not text:
                text = "こんにちは、claude-talkのテストです。"
            click.echo(f"Testing TTS: {text}")

        # Create TTS engine
        from claude_talk.tts import EdgeTTSEngine

        engine = EdgeTTSEngine(
            voice=cfg.tts.voice,
            rate=cfg.tts.rate,
            volume=cfg.tts.volume,
        )

        click.echo(f"Using voice: {cfg.tts.voice}")

        async def run_tts() -> None:
            if output:
                # Save to file
                path = await engine.synthesize_to_file(text, output)
                click.echo(f"Audio saved to: {path}")
            else:
                # Synthesize and show info
                result = await engine.synthesize(text)
                click.echo(f"Synthesized {len(result.audio_data)} bytes of audio")

                # Try to play
                click.echo("Playing audio...")
                try:
                    await engine.speak(text)
                    click.echo("Playback complete.")
                except Exception as e:
                    click.echo(f"Playback failed: {e}")
                    click.echo("\nTo play audio, install one of:")
                    click.echo("  - mpv: sudo apt-get install mpv")
                    click.echo("  - ffmpeg: sudo apt-get install ffmpeg")

        asyncio.run(run_tts())

    except FileNotFoundError as e:
        raise click.ClickException(str(e)) from e
    except ValueError as e:
        raise click.ClickException(str(e)) from e
    except Exception as e:
        raise click.ClickException(f"TTS failed: {e}") from e


@main.command("download-model")
@click.option(
    "--language",
    default="ja",
    help="Language code (ja, en)",
)
@click.option(
    "--target-dir",
    type=click.Path(),
    help="Target directory for model",
)
@click.pass_context
def download_model(ctx: click.Context, language: str, target_dir: str | None) -> None:
    """Download Vosk speech recognition model."""
    try:
        from claude_talk.stt.vosk_engine import download_vosk_model, VOSK_MODELS

        if language not in VOSK_MODELS:
            click.echo(f"Unsupported language: {language}")
            click.echo(f"Available languages: {', '.join(VOSK_MODELS.keys())}")
            return

        model_info = VOSK_MODELS[language]
        click.echo(f"Downloading Vosk model for {language}...")
        click.echo(f"Model: {model_info['small']}")
        click.echo(f"URL: {model_info['url']}")
        click.echo("\nThis may take a few minutes...\n")

        path = download_vosk_model(language, target_dir)

        click.echo(f"\nModel downloaded successfully!")
        click.echo(f"Location: {path}")
        click.echo("\nYou can now use the free STT mode.")

    except Exception as e:
        raise click.ClickException(f"Download failed: {e}") from e


@main.command("list-voices")
@click.option(
    "--language",
    default=None,
    help="Filter by language code (ja, en, etc.)",
)
def list_voices(language: str | None) -> None:
    """List available TTS voices."""
    import asyncio

    async def run() -> None:
        from claude_talk.tts import list_voices as get_voices

        voices = await get_voices(language)

        if not voices:
            click.echo("No voices found.")
            return

        click.echo(f"Available voices ({len(voices)}):\n")

        for voice in voices:
            name = voice.get("ShortName", "Unknown")
            locale = voice.get("Locale", "Unknown")
            gender = voice.get("Gender", "Unknown")
            click.echo(f"  {name}")
            click.echo(f"    Locale: {locale}, Gender: {gender}")

    asyncio.run(run())


if __name__ == "__main__":
    main()
