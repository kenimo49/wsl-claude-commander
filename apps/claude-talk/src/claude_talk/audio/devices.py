"""Audio device enumeration and management."""

from __future__ import annotations

from dataclasses import dataclass

import sounddevice as sd


@dataclass
class AudioDevice:
    """Audio device information."""

    index: int
    name: str
    max_input_channels: int
    max_output_channels: int
    default_sample_rate: float
    is_default_input: bool = False
    is_default_output: bool = False

    @property
    def is_input(self) -> bool:
        """Check if device supports input."""
        return self.max_input_channels > 0

    @property
    def is_output(self) -> bool:
        """Check if device supports output."""
        return self.max_output_channels > 0


def list_devices() -> list[AudioDevice]:
    """List all available audio devices.

    Returns:
        List of AudioDevice objects.
    """
    devices = sd.query_devices()
    default_input, default_output = sd.default.device

    result = []
    for i, dev in enumerate(devices):
        result.append(
            AudioDevice(
                index=i,
                name=dev["name"],
                max_input_channels=dev["max_input_channels"],
                max_output_channels=dev["max_output_channels"],
                default_sample_rate=dev["default_samplerate"],
                is_default_input=(i == default_input),
                is_default_output=(i == default_output),
            )
        )

    return result


def list_input_devices() -> list[AudioDevice]:
    """List available input (microphone) devices.

    Returns:
        List of input AudioDevice objects.
    """
    return [d for d in list_devices() if d.is_input]


def list_output_devices() -> list[AudioDevice]:
    """List available output (speaker) devices.

    Returns:
        List of output AudioDevice objects.
    """
    return [d for d in list_devices() if d.is_output]


def get_device(device_id: int | str | None, is_input: bool = True) -> AudioDevice | None:
    """Get a specific audio device by ID or name.

    Args:
        device_id: Device index (int), name/partial name (str), or None for default.
        is_input: Whether to get input or output device.

    Returns:
        AudioDevice if found, None otherwise.
    """
    devices = list_devices()

    if device_id is None:
        # Return default device
        for dev in devices:
            if is_input and dev.is_default_input and dev.is_input:
                return dev
            if not is_input and dev.is_default_output and dev.is_output:
                return dev
        return None

    # Handle string name (partial match, case-insensitive)
    if isinstance(device_id, str):
        device_id_lower = device_id.lower()
        for dev in devices:
            if device_id_lower in dev.name.lower():
                if is_input and dev.is_input:
                    return dev
                if not is_input and dev.is_output:
                    return dev
        return None

    # Handle integer index
    for dev in devices:
        if dev.index == device_id:
            if is_input and dev.is_input:
                return dev
            if not is_input and dev.is_output:
                return dev
    return None


def resolve_device_index(device_id: int | str | None, is_input: bool = True) -> int | None:
    """Resolve device identifier to index for sounddevice.

    Args:
        device_id: Device index (int), name/partial name (str), or None for default.
        is_input: Whether to resolve input or output device.

    Returns:
        Device index for sounddevice, or None for default.
    """
    if device_id is None:
        return None

    if isinstance(device_id, int):
        return device_id

    # String name - find matching device
    device = get_device(device_id, is_input)
    if device:
        return device.index

    return None


def get_default_input_device() -> AudioDevice | None:
    """Get the default input device.

    Returns:
        Default input AudioDevice, or None if not found.
    """
    return get_device(None, is_input=True)


def get_default_output_device() -> AudioDevice | None:
    """Get the default output device.

    Returns:
        Default output AudioDevice, or None if not found.
    """
    return get_device(None, is_input=False)
