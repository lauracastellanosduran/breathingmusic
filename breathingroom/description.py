"""Viewer-facing copy. Duration stays in the title. The thumbnail stays short."""

from breathingroom.concepts import Concept
from breathingroom.rules import DESCRIPTION_SIGN_OFF, PLAYLIST_BY_PURPOSE

# Short use-case line, then the atmosphere clause in the description template.
COPY = {
    "rainy-focus-working-reading": (
        "focused work and reading",
        "warm atmospheric music, restrained piano, and a steady low-to-medium energy",
    ),
    "calm-focus-for-work": (
        "focused computer work",
        "warm pads, soft piano, and a stable energy that stays in the background",
    ),
    "morning-study-clouds": (
        "morning studying",
        "pale, airy music and a slow, unobtrusive pace",
    ),
    "late-night-deep-work": (
        "late-night deep work",
        "darker warm music at a low, steady energy",
    ),
    "reading-evening-lamp": (
        "reading",
        "warm, low-energy music and almost no rhythm",
    ),
    "evening-unwind-after-work": (
        "decompressing after work",
        "warm, spacious music that keeps getting a little quieter",
    ),
    "forest-stream-reset": (
        "a quiet reset",
        "soft, slow music and a gentle water-like texture",
    ),
    "spacious-meditation": (
        "silent sitting meditation",
        "extremely slow, spacious music and no beat",
    ),
    "still-water-sitting": (
        "quiet sitting",
        "minimal sustained tones and very slow movement",
    ),
    "night-rain-wind-down": (
        "winding down before sleep",
        "warm, dark music that stays very low and very still",
    ),
    "rainy-evening-focus": (
        "evening focus work",
        "dark-leaning warm music at an even, low-to-medium energy",
    ),
    "quiet-morning-writing": (
        "morning writing",
        "sparse warm music and a distant piano",
    ),
    "desert-horizon-unwind": (
        "unwinding in the evening",
        "wide, warm music with a slow, open texture",
    ),
    "moonlight-wind-down": (
        "winding down before sleep",
        "very soft, dark-warm music with no percussion",
    ),
}


def description(concept: Concept) -> str:
    use_case, atmosphere = COPY[concept.id]
    situation = concept.viewer_situation[0].lower() + concept.viewer_situation[1:]
    return (
        f"A quiet 30-minute ambient session for {use_case}.\n\n"
        f"Designed for {situation}, with {atmosphere}.\n\n"
        "No talking. No interruptions.\n\n"
        f"{DESCRIPTION_SIGN_OFF}"
    )


def playlist(concept: Concept) -> str:
    return PLAYLIST_BY_PURPOSE[concept.purpose]
