"""Audio capture and playback modules."""

from claude_talk.audio.capture import AudioCapture, AudioRecorder
from claude_talk.audio.devices import (
    AudioDevice,
    get_default_input_device,
    get_default_output_device,
    get_device,
    list_devices,
    list_input_devices,
    list_output_devices,
    resolve_device_index,
)
from claude_talk.audio.playback import AudioPlayer, play_audio_async

__all__ = [
    "AudioCapture",
    "AudioDevice",
    "AudioPlayer",
    "AudioRecorder",
    "get_default_input_device",
    "get_default_output_device",
    "get_device",
    "list_devices",
    "list_input_devices",
    "list_output_devices",
    "play_audio_async",
    "resolve_device_index",
]
