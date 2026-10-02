"""Candidate concepts for one production cycle.

Scores other than library gap are editorial judgments about search intent,
channel fit, specificity, repeat use, and distinctiveness. Library gap is
applied when the slate is scored against the catalog.
"""

from dataclasses import dataclass

from breathingroom.rules import SCORE_WEIGHTS


@dataclass(frozen=True)
class Concept:
    id: str
    title: str
    purpose: str
    viewer_situation: str
    search_intent: str
    music_direction: str
    visual_world: str
    energy: str
    thumbnail_text: str
    thumbnail_style: str
    music_profile: str
    search_demand: int
    channel_relevance: int
    specificity: int
    repeat_use: int
    distinctiveness: int
    score_notes: str
    slate: bool = True

    def base_score(self) -> int:
        return (
            self.search_demand
            + self.channel_relevance
            + self.specificity
            + self.repeat_use
            + self.distinctiveness
        )


def _check(concept: Concept) -> None:
    caps = {
        "search_demand": concept.search_demand,
        "channel_relevance": concept.channel_relevance,
        "specificity": concept.specificity,
        "repeat_use": concept.repeat_use,
        "distinctiveness": concept.distinctiveness,
    }
    for name, value in caps.items():
        cap = SCORE_WEIGHTS[name]
        if not isinstance(value, int) or value < 0 or value > cap:
            raise ValueError(f"{concept.id} {name}={value} is outside 0–{cap}")
    words = concept.thumbnail_text.split()
    if not 2 <= len(words) <= 5:
        raise ValueError(f"{concept.id} thumbnail must be 2–5 words")
    if concept.title.isupper():
        raise ValueError(f"{concept.id} title is all caps")


def pool() -> tuple[Concept, ...]:
    concepts = (
        Concept(
            id="rainy-focus-working-reading",
            title="Rainy Focus Music for Working and Reading | 30 Min",
            purpose="FOCUS",
            viewer_situation="Quiet concentrated computer work or reading beside a window while rain falls",
            search_intent="rainy focus music, music for working and reading, rain sounds for studying",
            music_direction=(
                "Warm atmospheric ambient music with restrained soft piano textures and a subtle organic hush. "
                "Stable low-to-medium energy, minimal melodic movement, extremely restrained rhythm, and slow development."
            ),
            visual_world="Rain moving slowly across a large window, soft daylight, muted interior, no people",
            energy="Low-medium",
            thumbnail_text="RAINY FOCUS",
            thumbnail_style="One rainy window, cool daylight, two words, no duration",
            music_profile="Warm pads, restrained soft piano, stable low-medium energy, rain-adjacent texture",
            search_demand=23,
            channel_relevance=24,
            specificity=14,
            repeat_use=15,
            distinctiveness=8,
            score_notes="Work and reading are daily uses. Rain gives the session a specific room without mixing purposes.",
        ),
        Concept(
            id="calm-focus-for-work",
            title="30 Minutes of Calm Focus Music for Work",
            purpose="FOCUS",
            viewer_situation="Quiet concentrated computer work at a desk during the day",
            search_intent="focus music for work, calm music for working",
            music_direction=(
                "Warm atmospheric pads and restrained soft piano. Stable low-to-medium energy, "
                "minimal melody, and almost no rhythm."
            ),
            visual_world="Quiet workspace in soft daylight, slow shadows, no people and no screen glare",
            energy="Low-medium",
            thumbnail_text="QUIET WORK",
            thumbnail_style="Soft daylight desk, no person, two words",
            music_profile="Warm pads, restrained piano, stable low-medium energy",
            search_demand=22,
            channel_relevance=23,
            specificity=12,
            repeat_use=15,
            distinctiveness=6,
            score_notes="Clear work intent and strong repeat use. The room is less specific than a rain session.",
        ),
        Concept(
            id="morning-study-clouds",
            title="Soft Morning Music for Studying | 30 Min",
            purpose="FOCUS",
            viewer_situation="A morning study session before the day gets loud",
            search_intent="morning study music, soft music for studying",
            music_direction=(
                "Pale airy pads and very soft piano. Low-to-medium energy, slow development, "
                "and no rhythmic pulse."
            ),
            visual_world="Slow clouds in soft morning light, wide and quiet, no sun bursts",
            energy="Low-medium",
            thumbnail_text="MORNING STUDY",
            thumbnail_style="Pale morning sky, two words",
            music_profile="Airy pads, soft piano, morning low-medium energy",
            search_demand=20,
            channel_relevance=22,
            specificity=14,
            repeat_use=14,
            distinctiveness=8,
            score_notes="Morning study is a distinct time of day from evening or late-night work.",
        ),
        Concept(
            id="late-night-deep-work",
            title="Late-Night Deep Work Music | 30 Minutes",
            purpose="FOCUS",
            viewer_situation="Late-night deep work when the rest of the room is already quiet",
            search_intent="late night work music, deep work music",
            music_direction=(
                "Darker warm pads and sparse piano. Lower than daytime focus, still steady enough to work, "
                "with no beat and no bright highs."
            ),
            visual_world="A dim window at night with distant soft city light, no traffic rush and no people",
            energy="Low",
            thumbnail_text="DEEP WORK",
            thumbnail_style="Dim night window, two words",
            music_profile="Dark warm pads, sparse piano, low steady energy",
            search_demand=18,
            channel_relevance=23,
            specificity=15,
            repeat_use=12,
            distinctiveness=9,
            score_notes="Specific hour and a darker palette. Smaller search volume than daytime focus.",
        ),
        Concept(
            id="reading-evening-lamp",
            title="Peaceful Background Music for Reading | 30 Minutes",
            purpose="FOCUS",
            viewer_situation="Reading a book in a quiet room",
            search_intent="music for reading, peaceful background music for reading",
            music_direction=(
                "Warm low-energy ambient with soft harmonic movement, almost no rhythm, "
                "and piano that stays in the background."
            ),
            visual_world="A warm interior corner with lamp light and still furniture, no people",
            energy="Low",
            thumbnail_text="READ AND FOCUS",
            thumbnail_style="Warm lamp interior, three words",
            music_profile="Warm low-energy pads, background piano, no rhythm",
            search_demand=21,
            channel_relevance=23,
            specificity=14,
            repeat_use=14,
            distinctiveness=7,
            score_notes="Reading is a precise activity. The sonic world is close to other focus pieces, so distinctiveness stays moderate.",
        ),
        Concept(
            id="evening-unwind-after-work",
            title="Quiet Evening Music to Unwind After Work | 30 Min",
            purpose="RELAX",
            viewer_situation="Decompressing at home after a busy day",
            search_intent="music to unwind after work, quiet evening music",
            music_direction=(
                "Warm spacious pads, gentle organic textures, and slow harmonic movement. "
                "Consistently low energy with no percussion."
            ),
            visual_world="Trees moving slowly at dusk in warm light, no people",
            energy="Low",
            thumbnail_text="EVENING RESET",
            thumbnail_style="Dusk trees, two words",
            music_profile="Warm spacious pads, gentle organic texture, low energy",
            search_demand=20,
            channel_relevance=24,
            specificity=14,
            repeat_use=14,
            distinctiveness=8,
            score_notes="After-work decompression is a Breathing Room use case and is not a focus session.",
        ),
        Concept(
            id="forest-stream-reset",
            title="Forest Stream Music for a Quiet Reset | 30 Min",
            purpose="RELAX",
            viewer_situation="A quiet mental reset during a break",
            search_intent="forest stream music, music for a quiet break",
            music_direction=(
                "Soft pads with a gentle water-like texture. Slow, low energy, and minimal percussion."
            ),
            visual_world="A forest stream moving gently, no rapids and no waterfall",
            energy="Low",
            thumbnail_text="QUIET RESET",
            thumbnail_style="Gentle stream, two words",
            music_profile="Soft pads, water-like texture, low energy",
            search_demand=16,
            channel_relevance=22,
            specificity=13,
            repeat_use=12,
            distinctiveness=9,
            score_notes="The stream is distinctive. The search phrasing is more visual than activity-led.",
        ),
        Concept(
            id="spacious-meditation",
            title="30-Minute Ambient Meditation Music | Slow & Spacious",
            purpose="MEDITATE",
            viewer_situation="Silent sitting meditation without spoken guidance",
            search_intent="ambient meditation music, spacious meditation music",
            music_direction=(
                "Extremely slow evolving warm pads and sustained tones. No beat, no catchy melody, "
                "and no dramatic progression."
            ),
            visual_world="Mist and soft forest light, almost still",
            energy="Very low",
            thumbnail_text="SLOW DOWN",
            thumbnail_style="Mist and forest light, two words",
            music_profile="Extremely slow warm pads, sustained tones, no beat",
            search_demand=19,
            channel_relevance=21,
            specificity=13,
            repeat_use=13,
            distinctiveness=7,
            score_notes="Fits silent sitting. Meditation search often expects a voice, so this stays instrumental on purpose.",
        ),
        Concept(
            id="still-water-sitting",
            title="Still Water Music for Quiet Sitting | 30 Min",
            purpose="MEDITATE",
            viewer_situation="Mindful sitting and quiet reflection",
            search_intent="still water meditation music, music for quiet sitting",
            music_direction=(
                "Minimal sustained tones with very slow evolution. Spacious, consistent, and without drums."
            ),
            visual_world="Still water with faint reflections and no waves",
            energy="Very low",
            thumbnail_text="STILL WATER",
            thumbnail_style="Still water, two words",
            music_profile="Minimal sustained tones, very slow, no drums",
            search_demand=15,
            channel_relevance=21,
            specificity=14,
            repeat_use=12,
            distinctiveness=9,
            score_notes="Specific visual and a still, non-guided sitting practice. Narrower search than general meditation music.",
        ),
        Concept(
            id="night-rain-wind-down",
            title="Night Rain Music for Winding Down | 30 Min",
            purpose="SLEEP",
            viewer_situation="Winding down in a dark room before sleep",
            search_intent="night rain music for sleep, music for winding down",
            music_direction=(
                "Warm dark pads, extremely slow harmonic evolution, and gentle low-frequency texture. "
                "No percussion and no bright high-frequency events."
            ),
            visual_world="Rain at night on a dark window, dim, no lightning and no people",
            energy="Very low",
            thumbnail_text="DEEP REST",
            thumbnail_style="Dark night window, two words",
            music_profile="Warm dark pads, extremely slow, no percussion",
            search_demand=24,
            channel_relevance=20,
            specificity=14,
            repeat_use=14,
            distinctiveness=7,
            score_notes="Sleep-and-rain demand is large. Distinctiveness is limited because this picture is already common.",
        ),
        # Held for a later cycle. Not part of the fresh slate.
        Concept(
            id="rainy-evening-focus",
            title="Rainy Evening Focus Music | 30 Min",
            purpose="FOCUS",
            viewer_situation="Evening computer work while rain continues after dark",
            search_intent="rainy evening focus music, evening work music",
            music_direction=(
                "Warm dark-leaning pads and restrained piano. Low-to-medium energy that stays even, "
                "quieter than a daytime session."
            ),
            visual_world="Rain on a window after sunset, interior lamp dim, distant lights soft, no people",
            energy="Low-medium",
            thumbnail_text="EVENING FOCUS",
            thumbnail_style="Night rain window, two words",
            music_profile="Dark-leaning warm pads, restrained piano, even low-medium energy",
            search_demand=17,
            channel_relevance=23,
            specificity=15,
            repeat_use=13,
            distinctiveness=8,
            score_notes="Adjacent to rainy daytime focus. Use only after that session exists, not instead of it.",
            slate=False,
        ),
        Concept(
            id="quiet-morning-writing",
            title="Quiet Morning Music for Writing | 30 Min",
            purpose="FOCUS",
            viewer_situation="Morning writing at a clear desk",
            search_intent="music for writing, quiet morning writing music",
            music_direction=(
                "Sparse warm pads and a distant soft piano. Stable, unobtrusive, and slow to change."
            ),
            visual_world="A clear desk in pale morning light, paper still, no hands and no people",
            energy="Low-medium",
            thumbnail_text="QUIET WRITING",
            thumbnail_style="Pale desk, two words",
            music_profile="Sparse warm pads, distant piano, stable energy",
            search_demand=17,
            channel_relevance=22,
            specificity=15,
            repeat_use=13,
            distinctiveness=8,
            score_notes="Writing is a different activity from general computer work.",
            slate=False,
        ),
        Concept(
            id="desert-horizon-unwind",
            title="Desert Horizon Music to Unwind | 30 Min",
            purpose="RELAX",
            viewer_situation="A quiet evening reset with nothing else on screen",
            search_intent="desert ambient music, music to unwind",
            music_direction=(
                "Wide warm pads, very slow harmonic movement, and a dry open texture. Low energy, no percussion."
            ),
            visual_world="A still desert horizon in late light, no storms and no people",
            energy="Low",
            thumbnail_text="SLOW HORIZON",
            thumbnail_style="Desert horizon, two words",
            music_profile="Wide warm pads, dry open texture, low energy",
            search_demand=14,
            channel_relevance=20,
            specificity=13,
            repeat_use=11,
            distinctiveness=9,
            score_notes="A different landscape from trees and rain. Weaker direct search intent.",
            slate=False,
        ),
        Concept(
            id="moonlight-wind-down",
            title="Moonlight Music for Winding Down | 30 Min",
            purpose="SLEEP",
            viewer_situation="Preparing for sleep with the lights already low",
            search_intent="music for winding down, moonlight sleep music",
            music_direction=(
                "Very soft dark-warm pads, extremely gradual, with no percussion and no bright highs."
            ),
            visual_world="Moonlight on low-light trees, no clouds racing and no people",
            energy="Very low",
            thumbnail_text="WIND DOWN",
            thumbnail_style="Low moonlight, two words",
            music_profile="Dark-warm pads, extremely gradual, no percussion",
            search_demand=18,
            channel_relevance=21,
            specificity=13,
            repeat_use=13,
            distinctiveness=8,
            score_notes="A sleep session that does not reuse the night-rain picture.",
            slate=False,
        ),
    )
    for concept in concepts:
        _check(concept)
    ids = [concept.id for concept in concepts]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate concept id")
    return concepts
