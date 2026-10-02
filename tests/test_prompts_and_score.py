from breathingroom.concepts import pool
from breathingroom.prompts import section_prompts
from breathingroom.rules import ENERGY_CURVE, ENERGY_RANK, FORBIDDEN
from breathingroom.score import generate_slate, is_near_duplicate, library_gap, score_concept
from breathingroom.visual import reverse_allowed


def test_energy_never_climbs_at_the_end():
    for purpose, curve in ENERGY_CURVE.items():
        ranks = [ENERGY_RANK[purpose][stage] for stage in curve]
        assert ranks[-1] <= ranks[0]
        assert len(curve) == 3


def test_prompts_are_instrumental_and_stay_in_one_world():
    concept = next(item for item in pool() if item.id == "rainy-focus-working-reading")
    prompts = section_prompts(concept)
    assert [item["energy"] for item in prompts] == ["stable", "stable", "slightly calmer"]
    for item in prompts:
        text = item["prompt"]
        assert "No vocals." in text
        assert concept.viewer_situation in text
        for line in FORBIDDEN["FOCUS"]:
            assert line in text
        assert "lyrics" not in text.lower()
    assert "Do not restart" in prompts[1]["prompt"]
    assert "Do not restart" in prompts[2]["prompt"]


def test_library_gap_shrinks_after_a_purpose_is_published():
    concept = next(item for item in pool() if item.purpose == "FOCUS")
    assert library_gap(concept, []) == 10
    published = [
        {
            "purpose": "FOCUS",
            "viewer_situation": "A different desk",
            "visual_world": "A different room",
            "title": "Some other focus video",
            "concept_id": "other",
            "thumbnail_text": "OTHER SESSION",
        }
    ]
    assert library_gap(concept, published) == 7


def test_near_duplicate_leaves_the_slate_and_backfill_keeps_ten():
    original = next(item for item in pool() if item.id == "rainy-focus-working-reading")
    published = [
        {
            "purpose": original.purpose,
            "viewer_situation": original.viewer_situation,
            "visual_world": original.visual_world,
            "title": original.title,
            "concept_id": original.id,
            "thumbnail_text": original.thumbnail_text,
        }
    ]
    assert is_near_duplicate(original, published)
    slate = generate_slate(published)
    assert len(slate) == 10
    assert original.id not in {item.id for item in slate}
    scored = score_concept(original, published)
    assert scored["scores"]["library_gap"] == 0


def test_rain_is_not_reversed_and_clouds_may_be():
    assert reverse_allowed("Rain moving slowly across a large window") is False
    assert reverse_allowed("Slow clouds in soft morning light") is True
    assert reverse_allowed("A forest stream moving gently") is False
