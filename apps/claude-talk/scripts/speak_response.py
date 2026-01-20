#!/usr/bin/env python3
"""Speak Claude's response if it was triggered by voice input."""

import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from read_response import should_read_response


async def speak(text: str) -> None:
    """Speak text using edge-tts."""
    try:
        from claude_talk.tts import EdgeTTSEngine
        
        engine = EdgeTTSEngine(
            voice="ja-JP-NanamiNeural",
            rate="+10%",  # Slightly faster for responses
        )
        
        await engine.speak(text)
        
    except Exception as e:
        print(f"TTS error: {e}", file=sys.stderr)


def main():
    should_read, response = should_read_response()
    
    if not should_read:
        print("Not a voice input response, skipping.", file=sys.stderr)
        sys.exit(0)
    
    print(f"Reading response: {response[:50]}...", file=sys.stderr)
    
    asyncio.run(speak(response))
    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
