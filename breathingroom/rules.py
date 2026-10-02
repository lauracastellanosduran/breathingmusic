"""Constants taken from the ambient long-form master rules."""

PURPOSES = ("FOCUS", "RELAX", "MEDITATE", "SLEEP")

# ElevenLabs prompt-mode maximum. Sections stay inside the 8–10 minute range.
SECTION_MS = 600_000
SECTION_COUNT = 3
CROSSFADE_SECONDS = 15
FINAL_FADE_SECONDS = 45

# 3 × 10:00 with two 15-second crossfades.
TARGET_DURATION_SECONDS = (SECTION_MS / 1000) * SECTION_COUNT - CROSSFADE_SECONDS * (SECTION_COUNT - 1)
DURATION_MIN_SECONDS = 29 * 60 + 30
DURATION_MAX_SECONDS = 31 * 60

SCORE_WEIGHTS = {
    "search_demand": 25,
    "channel_relevance": 25,
    "specificity": 15,
    "repeat_use": 15,
    "distinctiveness": 10,
    "library_gap": 10,
}
SCORE_THRESHOLD = 75

UPLOAD_STATUS = "PRIVATE"

PLAYLIST_BY_PURPOSE = {
    "FOCUS": "BREATHING ROOM — FOCUS",
    "RELAX": "BREATHING ROOM — RELAX",
    "MEDITATE": "BREATHING ROOM — MEDITATE",
    "SLEEP": "BREATHING ROOM — SLEEP",
}

# Higher rank means more energy. The ending rank must not exceed the opening rank.
ENERGY_RANK = {
    "FOCUS": {"stable": 2, "slightly calmer": 1},
    "RELAX": {"calm": 3, "calmer": 2, "calmest": 1},
    "MEDITATE": {"spacious": 2, "deeper": 1},
    "SLEEP": {"calm": 3, "lower energy": 2, "very low energy": 1},
}

ENERGY_CURVE = {
    "FOCUS": ("stable", "stable", "slightly calmer"),
    "RELAX": ("calm", "calmer", "calmest"),
    "MEDITATE": ("spacious", "deeper", "spacious"),
    "SLEEP": ("calm", "lower energy", "very low energy"),
}

ENERGY_DIRECTION = {
    "FOCUS": {
        "stable": "Stable low-to-medium energy, already in motion, with no introductory swell and no lift in intensity.",
        "slightly calmer": "Slightly calmer than the opening. Do not brighten, do not add instruments, and do not build.",
    },
    "RELAX": {
        "calm": "Calm, warm, and slow from the first moment. No introductory build.",
        "calmer": "Calmer than the opening while staying in the same harmonic world.",
        "calmest": "The calmest part of the piece. Let the texture thin slightly without a resolving cadence.",
    },
    "MEDITATE": {
        "spacious": "Extremely spacious and consistent. Return only to this same openness, never to a brighter or fuller arrangement.",
        "deeper": "Deeper and more minimal than the opening, with fewer events and the same tones.",
    },
    "SLEEP": {
        "calm": "Very low energy, dark and warm, with no percussion and no bright highs.",
        "lower energy": "Lower energy than the opening. Remove any remaining sparkle. Keep the same dark warmth.",
        "very low energy": "Very low energy. Almost still. No new event, no lift, and no melodic goodbye.",
    },
}

FORBIDDEN = {
    "FOCUS": (
        "No vocals.",
        "No catchy lead melody.",
        "No heavy drums.",
        "No sudden transitions.",
        "No dramatic builds.",
        "No cinematic climax.",
    ),
    "RELAX": (
        "No vocals.",
        "No prominent drums.",
        "No dramatic chord changes.",
        "No strong melody.",
        "No sudden transitions.",
        "No climax.",
    ),
    "MEDITATE": (
        "No vocals.",
        "No drums.",
        "No catchy melody.",
        "No dramatic harmonic changes.",
        "No cinematic progression.",
        "No climax.",
    ),
    "SLEEP": (
        "No vocals.",
        "No percussion.",
        "No bright melodic events.",
        "No sudden changes.",
        "No tension.",
        "No climax.",
        "No dramatic ending.",
    ),
}

QA_SAMPLE_TIMES = ("00:00", "05:00", "10:00", "15:00", "20:00", "25:00", "29:30")
QA_FRAME_TIMES = ("00:05", "05:00", "10:00", "15:00", "20:00", "25:00", "29:30")

DESCRIPTION_SIGN_OFF = "Breathing Room — a little space for whatever you're going through."
