"""Score a slate and choose one concept, or none."""

from breathingroom.concepts import Concept
from breathingroom.rules import SCORE_THRESHOLD, SCORE_WEIGHTS


def library_gap(concept: Concept, published: list[dict]) -> int:
    same_purpose = [item for item in published if item.get("purpose") == concept.purpose]
    if not same_purpose:
        return SCORE_WEIGHTS["library_gap"]
    same_situation = any(item.get("viewer_situation") == concept.viewer_situation for item in same_purpose)
    same_visual = any(item.get("visual_world") == concept.visual_world for item in same_purpose)
    if same_situation and same_visual:
        return 0
    if same_situation or same_visual:
        return 4
    return 7


def is_near_duplicate(concept: Concept, published: list[dict]) -> bool:
    title = _normalize(concept.title)
    for item in published:
        if _normalize(item.get("title", "")) == title:
            return True
        if item.get("concept_id") == concept.id:
            return True
        same_purpose = item.get("purpose") == concept.purpose
        same_situation = item.get("viewer_situation") == concept.viewer_situation
        same_visual = item.get("visual_world") == concept.visual_world
        if same_purpose and same_situation and same_visual:
            return True
        if item.get("thumbnail_text") == concept.thumbnail_text and same_purpose:
            return True
    return False


def score_concept(concept: Concept, published: list[dict]) -> dict:
    gap = library_gap(concept, published)
    components = {
        "search_demand": concept.search_demand,
        "channel_relevance": concept.channel_relevance,
        "specificity": concept.specificity,
        "repeat_use": concept.repeat_use,
        "distinctiveness": concept.distinctiveness,
        "library_gap": gap,
    }
    return {
        "concept_id": concept.id,
        "title": concept.title,
        "purpose": concept.purpose,
        "viewer_situation": concept.viewer_situation,
        "search_intent": concept.search_intent,
        "music_direction": concept.music_direction,
        "visual_world": concept.visual_world,
        "energy": concept.energy,
        "thumbnail_text": concept.thumbnail_text,
        "thumbnail_style": concept.thumbnail_style,
        "music_profile": concept.music_profile,
        "scores": components,
        "total": sum(components.values()),
        "notes": concept.score_notes,
        "eligible": sum(components.values()) >= SCORE_THRESHOLD,
    }


def generate_slate(published: list[dict]) -> list[Concept]:
    """Ten candidates. Published near-duplicates drop out and backfill replaces them."""

    available = [concept for concept in pool_ordered() if not is_near_duplicate(concept, published)]
    primary = [concept for concept in available if concept.slate]
    backfill = [concept for concept in available if not concept.slate]
    slate = (primary + backfill)[:10]
    return slate


def pool_ordered():
    from breathingroom.concepts import pool

    return pool()


def choose(scored: list[dict], unpublished_id: str | None = None) -> dict | None:
    eligible = [item for item in scored if item["eligible"]]
    if unpublished_id:
        held = [item for item in eligible if item["concept_id"] == unpublished_id]
        if held:
            return held[0]
    if not eligible:
        return None
    return max(eligible, key=lambda item: (item["total"], item["scores"]["specificity"], item["concept_id"]))


def _normalize(title: str) -> str:
    return " ".join(title.lower().replace("|", " ").split())
