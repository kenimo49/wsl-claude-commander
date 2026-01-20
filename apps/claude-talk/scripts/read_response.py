#!/usr/bin/env python3
"""Read Claude's response if last user message was voice input."""

import json
import sys
from pathlib import Path


def get_latest_session_file() -> Path | None:
    """Find the latest session file."""
    claude_dir = Path.home() / ".claude" / "projects"
    
    if not claude_dir.exists():
        return None
    
    # Find all session files
    session_files = []
    for project_dir in claude_dir.iterdir():
        if project_dir.is_dir():
            for f in project_dir.glob("*.jsonl"):
                if not f.name.startswith("agent-"):
                    session_files.append(f)
    
    if not session_files:
        return None
    
    # Return most recently modified
    return max(session_files, key=lambda f: f.stat().st_mtime)


def get_last_messages(session_file: Path, count: int = 10) -> list[dict]:
    """Get last N messages from session file."""
    messages = []
    
    with open(session_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                messages.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    return messages[-count:]


def extract_text_content(message: dict) -> str:
    """Extract text content from message."""
    if 'message' not in message:
        return ""

    content = message['message'].get('content', [])

    # Content can be a string or a list
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                texts.append(item.get('text', ''))
        return '\n'.join(texts)

    return ""


def find_voice_input_response() -> tuple[bool, str]:
    """Find the most recent voice input and its response across all sessions.

    Returns:
        (found, response_text)
    """
    claude_dir = Path.home() / ".claude" / "projects"

    if not claude_dir.exists():
        return False, ""

    # Find all session files
    session_files = []
    for project_dir in claude_dir.iterdir():
        if project_dir.is_dir():
            for f in project_dir.glob("*.jsonl"):
                if not f.name.startswith("agent-"):
                    session_files.append(f)

    if not session_files:
        return False, ""

    # Search all recently modified sessions (last 5 minutes)
    import time
    now = time.time()
    recent_threshold = 5 * 60  # 5 minutes

    best_match = None
    best_timestamp = 0

    for session_file in session_files:
        if now - session_file.stat().st_mtime > recent_threshold:
            continue

        messages = get_last_messages(session_file, 30)

        # Find voice input user message and following assistant response
        for i, msg in enumerate(messages):
            if msg.get('type') != 'user':
                continue

            user_text = extract_text_content(msg)
            if not user_text.startswith('[音声入力]'):
                continue

            # Found voice input, look for assistant response after it
            timestamp = msg.get('timestamp', '')
            if isinstance(timestamp, str):
                # Parse ISO timestamp
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    ts = dt.timestamp()
                except:
                    ts = 0
            else:
                ts = timestamp / 1000 if timestamp > 1e12 else timestamp

            if ts <= best_timestamp:
                continue

            # Find assistant response with text after this message
            for j in range(i + 1, len(messages)):
                if messages[j].get('type') == 'assistant':
                    response_text = extract_text_content(messages[j])
                    if response_text:
                        best_match = response_text
                        best_timestamp = ts
                        break
                elif messages[j].get('type') == 'user':
                    # Next user message, stop searching
                    break

    if best_match:
        return True, best_match

    return False, ""


def should_read_response() -> tuple[bool, str]:
    """Check if we should read the response and return it.

    Returns:
        (should_read, response_text)
    """
    return find_voice_input_response()


def main():
    should_read, response = should_read_response()
    
    if should_read:
        # Truncate long responses
        max_chars = 500
        if len(response) > max_chars:
            response = response[:max_chars] + "... 以下省略"
        
        print(response)
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
