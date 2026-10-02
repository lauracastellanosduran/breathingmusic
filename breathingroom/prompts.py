"""ElevenLabs prompts written for a chosen concept. Music is never prompted before a title exists."""

from breathingroom.concepts import Concept
from breathingroom.rules import ENERGY_CURVE, ENERGY_DIRECTION, FORBIDDEN, SECTION_COUNT


def section_prompts(concept: Concept) -> list[dict]:
    curve = ENERGY_CURVE[concept.purpose]
    if len(curve) != SECTION_COUNT:
        raise ValueError(f"{concept.purpose} needs {SECTION_COUNT} energy stages")
    forbidden = "\n".join(FORBIDDEN[concept.purpose])
    prompts = []
    for index, stage in enumerate(curve):
        name = ("A", "B", "C")[index]
        continuation = (
            "This is the opening of one continuous piece. Do not fade in from silence."
            if index == 0
            else "Continue the same piece and the same instrumentation. Do not restart and do not introduce a new theme."
        )
        text = "\n".join(
            (
                f"Instrumental ambient music for this activity: {concept.viewer_situation}.",
                concept.music_direction,
                f"Section {name}: {ENERGY_DIRECTION[concept.purpose][stage]}",
                continuation,
                "Spacious modern production that can stay on for half an hour without asking for attention.",
                forbidden,
            )
        )
        prompts.append({"section": name, "energy": stage, "prompt": text})
    return prompts
