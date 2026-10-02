"""ElevenLabs Music API. Prompt mode with force_instrumental, which the API only guarantees on prompts."""

import json
import os
import urllib.error
import urllib.request

from breathingroom.rules import SECTION_MS

COMPOSE_URL = "https://api.elevenlabs.io/v1/music?output_format=mp3_48000_192"
DEFAULT_MODEL = "music_v2_5"


class MissingApiKey(RuntimeError):
    pass


class MusicRequestError(RuntimeError):
    def __init__(self, status: int, detail: str):
        super().__init__(f"ElevenLabs music request failed with HTTP {status}: {detail}")
        self.status = status


def api_key() -> str:
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key:
        raise MissingApiKey("ELEVENLABS_API_KEY is not set")
    return key


def compose(prompt: str, duration_ms: int = SECTION_MS, model_id: str | None = None, timeout: int = 900) -> bytes:
    if not 3000 <= duration_ms <= 600_000:
        raise ValueError("music_length_ms must be between 3000 and 600000")
    body = {
        "prompt": prompt,
        "music_length_ms": duration_ms,
        "model_id": model_id or os.environ.get("ELEVENLABS_MODEL_ID", DEFAULT_MODEL),
        "force_instrumental": True,
    }
    request = urllib.request.Request(
        COMPOSE_URL,
        data=json.dumps(body).encode(),
        headers={
            "xi-api-key": api_key(),
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            audio = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read(500).decode("utf-8", errors="replace")
        raise MusicRequestError(error.code, detail) from None
    if not audio:
        raise MusicRequestError(200, "empty audio body")
    return audio
