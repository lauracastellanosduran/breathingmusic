"""One Friday production cycle.

The title and the viewer situation are fixed before any music request.
Nothing is uploaded. upload_status stays PRIVATE.
"""

import json
import os
from pathlib import Path

from breathingroom.assemble import assemble
from breathingroom.concepts import Concept, pool
from breathingroom.description import description, playlist
from breathingroom.elevenlabs import MissingApiKey, MusicRequestError, compose
from breathingroom.library import active_hold, hold_concept, load, save
from breathingroom.prompts import section_prompts
from breathingroom.qa import extract_frames, extract_samples, inspect_audio, inspect_video
from breathingroom.rain_window import rain_window_supported, render_rain_window
from breathingroom.rules import SECTION_MS, TARGET_DURATION_SECONDS, UPLOAD_STATUS
from breathingroom.score import choose, generate_slate, score_concept
from breathingroom.thumbnail import render
from breathingroom.visual import extend_plate

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "library" / "catalog.json"


def main() -> None:
    date = os.environ.get("CYCLE_DATE") or _today()
    result = run_cycle(ROOT, date)
    print(json.dumps({"date": date, "status": result["production_status"], "title": result.get("title")}, indent=2))


def run_cycle(root: Path, date: str, catalog_path: Path | None = None) -> dict:
    catalog_path = catalog_path or (root / "library" / "catalog.json")
    catalog = load(catalog_path)
    published = catalog["videos"]
    slate = generate_slate(published)
    scored = [score_concept(concept, published) for concept in slate]
    hold = active_hold(catalog)
    if hold and hold.get("status") == "ready_for_human_review":
        return _wait_for_review(root, date, hold)
    selected_row = choose(scored, hold["concept_id"] if hold else None)
    cycle_dir = root / "cycles" / date
    cycle_dir.mkdir(parents=True, exist_ok=True)
    (cycle_dir / "candidates.json").write_text(json.dumps(scored, indent=2) + "\n")

    if selected_row is None:
        decision = {
            "date": date,
            "production_status": "not_produced",
            "reason": "No concept reached 75.",
            "upload_status": UPLOAD_STATUS,
        }
        _write(cycle_dir / "decision.json", decision)
        _write(cycle_dir / "metadata.json", decision)
        _write_scorecard(cycle_dir / "SCORECARD.md", date, scored, None)
        save(catalog_path, catalog)
        return decision

    concept = _by_id(selected_row["concept_id"])
    prompts = section_prompts(concept)
    gate = _design_gate(concept)
    if not gate["proceed"]:
        decision = {
            "date": date,
            "production_status": "not_produced",
            "reason": "The concept does not name a viewer activity.",
            "upload_status": UPLOAD_STATUS,
            "concept_id": concept.id,
        }
        _write(cycle_dir / "decision.json", decision)
        return decision

    decision = _decision(date, concept, selected_row, prompts, gate)
    _write(cycle_dir / "decision.json", decision)
    _write_scorecard(cycle_dir / "SCORECARD.md", date, scored, concept.id)
    render(concept, cycle_dir / "THUMBNAIL.jpg")

    status, detail = _produce(concept, prompts, cycle_dir)
    decision["production_status"] = status
    decision["production_detail"] = detail
    metadata = _metadata(date, concept, status, detail, cycle_dir)
    qa_report = _qa_report(status, detail)
    _write(cycle_dir / "decision.json", decision)
    _write(cycle_dir / "metadata.json", metadata)
    _write(cycle_dir / "qa_report.json", qa_report)
    hold_concept(catalog, concept.id, date, concept.title, status)
    save(catalog_path, catalog)
    return metadata


def _wait_for_review(root: Path, date: str, hold: dict) -> dict:
    """A private master already exists. Do not start a second near-duplicate."""

    cycle_dir = root / "cycles" / date
    metadata_path = cycle_dir / "metadata.json"
    if metadata_path.exists():
        current = json.loads(metadata_path.read_text())
        if current.get("production_status") == "ready_for_human_review":
            return current
    decision = {
        "date": date,
        "upload_status": UPLOAD_STATUS,
        "production_status": "waiting_on_human_review",
        "concept_id": hold.get("concept_id"),
        "title": hold.get("title"),
        "reason": "A private master is already waiting for human review. No second video was started.",
    }
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(cycle_dir / "decision.json", decision)
    _write(cycle_dir / "metadata.json", decision)
    return decision


def _produce(concept: Concept, prompts: list[dict], cycle_dir: Path) -> tuple[str, dict]:
    """Generate music only after the concept file has been written by the caller."""

    detail: dict = {"sections": [item["section"] for item in prompts]}
    try:
        section_paths = []
        for item in prompts:
            section_paths.append(_section_audio(item, cycle_dir))
    except MissingApiKey:
        return "blocked_missing_elevenlabs_key", detail
    except MusicRequestError as error:
        detail["http_status"] = error.status
        detail["error"] = str(error)[:500]
        return "blocked_music_request", detail

    master = cycle_dir / "audio_master.mp3"
    assembly = assemble(section_paths, master)
    detail["assembly"] = assembly
    detail["audio_qa"] = inspect_audio(master)
    detail["samples"] = extract_samples(master, cycle_dir / "qa_samples")
    visual, visual_status = _visual(concept, cycle_dir, assembly["duration"])
    if visual is None:
        return visual_status, detail
    detail["visual"] = visual
    final = cycle_dir / "FINAL_VIDEO.mp4"
    _mux(master, Path(visual["output"]), final)
    detail["final_video"] = str(final)
    detail["video_qa"] = inspect_video(final, cycle_dir / "qa_frames")
    render(concept, cycle_dir / "THUMBNAIL.jpg")
    if not detail["audio_qa"]["passed"] or not detail["video_qa"]["passed"]:
        return "qa_failed", detail
    return "ready_for_human_review", detail


def _section_audio(item: dict, cycle_dir: Path) -> Path:
    path = cycle_dir / f"section_{item['section']}.mp3"
    if path.exists() and path.stat().st_size > 1_000_000:
        duration = _media_duration(path)
        if 480 <= duration <= 620:
            return path
    audio = compose(item["prompt"], SECTION_MS)
    path.write_bytes(audio)
    return path


def _visual(concept: Concept, cycle_dir: Path, duration: float) -> tuple[dict | None, str]:
    plate = os.environ.get("VISUAL_PLATE", "").strip()
    visual_path = cycle_dir / "visual.mp4"
    if visual_path.exists():
        existing = _media_duration(visual_path)
        if existing + 0.25 >= duration:
            return {
                "output": str(visual_path),
                "duration": existing,
                "reversed": False,
                "reused": True,
            }, "ready"
    if plate:
        return (
            extend_plate(
                Path(plate),
                visual_path,
                duration,
                concept.visual_world,
                allow_reverse=False,
            ),
            "ready",
        )
    still = _rain_still()
    if rain_window_supported(concept.visual_world) and still.exists():
        return render_rain_window(still, visual_path, duration), "ready"
    return None, "awaiting_visual_plate"


def _media_duration(path: Path) -> float:
    result = __import__("subprocess").run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def _rain_still() -> Path:
    override = os.environ.get("RAIN_WINDOW_STILL", "").strip()
    if override:
        return Path(override)
    return ROOT / "assets" / "rainy-window-daylight.jpg"


def _mux(audio: Path, video: Path, output: Path) -> None:
    subprocess_run = __import__("subprocess").run
    result = subprocess_run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video),
            "-i",
            str(audio),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1500:])


def _decision(date: str, concept: Concept, scored: dict, prompts: list[dict], gate: dict) -> dict:
    return {
        "date": date,
        "upload_status": UPLOAD_STATUS,
        "concept_id": concept.id,
        "purpose": concept.purpose,
        "viewer_situation": concept.viewer_situation,
        "search_intent": concept.search_intent,
        "working_title": concept.title,
        "music_direction": concept.music_direction,
        "visual_world": concept.visual_world,
        "energy": concept.energy,
        "total_score": scored["total"],
        "scores": scored["scores"],
        "target_duration_seconds": TARGET_DURATION_SECONDS,
        "playlist": playlist(concept),
        "description": description(concept),
        "thumbnail_text": concept.thumbnail_text,
        "prompts_written_before_audio": True,
        "section_prompts": prompts,
        "design_gate": gate,
        "final_questions": {
            "what_is_the_viewer_doing": concept.viewer_situation,
            "why_this_instead_of_generic_ambient": concept.score_notes,
            "music_supports_that_activity": True,
            "visual_supports_the_same_environment": True,
            "comfortable_for_30_minutes": True,
            "interruption_designed_in": False,
        },
    }


def _metadata(date: str, concept: Concept, status: str, detail: dict, cycle_dir: Path) -> dict:
    return {
        "upload_status": UPLOAD_STATUS,
        "production_status": status,
        "video_id": None,
        "date": date,
        "purpose": concept.purpose,
        "viewer_situation": concept.viewer_situation,
        "title": concept.title,
        "duration_target_seconds": TARGET_DURATION_SECONDS,
        "music_profile": concept.music_profile,
        "visual_world": concept.visual_world,
        "thumbnail_style": concept.thumbnail_style,
        "thumbnail_text": concept.thumbnail_text,
        "playlist": playlist(concept),
        "description": description(concept),
        "search_intent": concept.search_intent,
        "picture_note": "One rainy window for the whole session. Rain scrolls downward and is not reversed. The private picture is 1280x720 so the review file can live with the project.",
        "artifacts": {
            "final_video": _repo_path(detail.get("final_video"), cycle_dir),
            "thumbnail": _repo_path(cycle_dir / "THUMBNAIL.jpg", cycle_dir),
            "thumbnail_note": (
                "The rainy window plate, with the use case in two words. Duration stays in the title."
                if _rain_still().exists()
                else "Designed still for the concept. Replace it with a frame from the finished rainy-window picture before publication."
            ),
            "audio_master": _repo_path(cycle_dir / "audio_master.mp3", cycle_dir) if (cycle_dir / "audio_master.mp3").exists() else None,
            "qa_report": _repo_path(cycle_dir / "qa_report.json", cycle_dir),
        },
        "metrics": {
            "impressions": None,
            "ctr": None,
            "views": None,
            "watch_hours": None,
            "average_view_duration": None,
            "average_percentage_viewed": None,
            "subscribers_gained": None,
            "traffic_sources": None,
            "search_terms": None,
        },
    }


def _qa_report(status: str, detail: dict) -> dict:
    audio_qa = detail.get("audio_qa")
    return {
        "production_status": status,
        "upload_status": UPLOAD_STATUS,
        "audio": audio_qa
        or {
            "ran": False,
            "reason": "Music was not generated, so there is nothing to inspect.",
        },
        "video": detail.get("video_qa")
        or {
            "ran": bool(detail.get("final_video")),
            "aspect": "16:9" if detail.get("final_video") else None,
            "reason": detail.get("error"),
        },
        "human_review_required": [
            "sections sound like the same musical world",
            "no unexpected vocals",
            "no harsh frequencies",
            "no abrupt visual cuts",
            "no stock watermark",
            "opening has no permanent title card",
            "ending does not feel like a sudden removal",
        ],
        "sample_times": ["00:00", "05:00", "10:00", "15:00", "20:00", "25:00", "29:30"],
        "frame_times": ["00:05", "05:00", "10:00", "15:00", "20:00", "25:00", "29:30"],
        "samples": detail.get("samples", []),
    }


def _design_gate(concept: Concept) -> dict:
    activity_clear = len(concept.viewer_situation.split()) >= 3
    return {
        "viewer_activity_clear": activity_clear,
        "music_direction_present": bool(concept.music_direction),
        "visual_world_present": bool(concept.visual_world),
        "single_purpose": concept.purpose in {"FOCUS", "RELAX", "MEDITATE", "SLEEP"},
        "interruptions_in_design": False,
        "proceed": activity_clear and bool(concept.music_direction) and bool(concept.visual_world),
    }


def _write_scorecard(path: Path, date: str, scored: list[dict], selected_id: str | None) -> None:
    lines = [
        f"# Ambient cycle {date}",
        "",
        "One purpose per video. A concept is eligible at 75 or above. Nothing here is published.",
        "",
        "| Score | Purpose | Title | Eligible |",
        "| ---: | --- | --- | --- |",
    ]
    ordered = sorted(scored, key=lambda item: item["total"], reverse=True)
    for item in ordered:
        mark = "yes" if item["eligible"] else "no"
        chosen = " — selected" if item["concept_id"] == selected_id else ""
        title = item["title"].replace("|", "/")
        lines.append(f"| {item['total']} | {item['purpose']} | {title}{chosen} | {mark} |")
    if selected_id:
        chosen = next(item for item in scored if item["concept_id"] == selected_id)
        lines.extend(
            [
                "",
                "## Selected",
                "",
                f"Purpose: {chosen['purpose']}",
                "",
                f"Viewer situation: {chosen['viewer_situation']}",
                "",
                f"Working title: {chosen['title']}",
                "",
                f"Music direction: {chosen['music_direction']}",
                "",
                f"Visual world: {chosen['visual_world']}",
                "",
                f"Energy: {chosen['energy']}",
                "",
                chosen["notes"],
                "",
            ]
        )
    else:
        lines.extend(["", "No concept reached 75. Nothing was produced.", ""])
    path.write_text("\n".join(lines))


def _repo_path(path: str | Path | None, cycle_dir: Path) -> str | None:
    if path is None:
        return None
    candidate = Path(path)
    root = cycle_dir.parent.parent
    try:
        return str(candidate.resolve().relative_to(root))
    except ValueError:
        return str(candidate)


def _by_id(concept_id: str) -> Concept:
    for concept in pool():
        if concept.id == concept_id:
            return concept
    raise KeyError(concept_id)


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def _today() -> str:
    from datetime import date

    return date.today().isoformat()
