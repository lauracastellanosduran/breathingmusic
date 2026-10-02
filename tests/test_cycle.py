import json
from pathlib import Path

from breathingroom.cycle import run_cycle
from breathingroom.library import load
from breathingroom.rules import UPLOAD_STATUS


def test_empty_library_selects_rainy_focus_and_does_not_invent_audio(tmp_path, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    catalog = tmp_path / "library" / "catalog.json"
    result = run_cycle(tmp_path, "2026-10-02", catalog)

    assert result["upload_status"] == UPLOAD_STATUS
    assert result["upload_status"] == "PRIVATE"
    assert result["production_status"] == "blocked_missing_elevenlabs_key"
    assert result["title"] == "Rainy Focus Music for Working and Reading | 30 Min"
    assert result["purpose"] == "FOCUS"
    assert result["artifacts"]["final_video"] is None
    assert result["artifacts"]["audio_master"] is None
    assert "No talking. No interruptions." in result["description"]
    assert "HEAL YOUR BRAIN" not in result["description"]

    cycle = tmp_path / "cycles" / "2026-10-02"
    decision = json.loads((cycle / "decision.json").read_text())
    assert decision["prompts_written_before_audio"] is True
    assert decision["section_prompts"][0]["section"] == "A"
    assert not (cycle / "audio_master.mp3").exists()
    assert not (cycle / "FINAL_VIDEO.mp4").exists()
    assert (cycle / "THUMBNAIL.jpg").exists()
    assert result["artifacts"]["thumbnail"] == "cycles/2026-10-02/THUMBNAIL.jpg"
    assert "Rainy Focus Music for Working and Reading / 30 Min — selected" in (cycle / "SCORECARD.md").read_text()

    qa = json.loads((cycle / "qa_report.json").read_text())
    assert qa["audio"]["ran"] is False
    assert qa["upload_status"] == "PRIVATE"

    held = load(catalog)
    assert held["videos"] == []
    assert held["unpublished_selections"][0]["concept_id"] == "rainy-focus-working-reading"


def test_resume_keeps_the_held_concept_instead_of_switching(tmp_path, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    catalog = tmp_path / "library" / "catalog.json"
    catalog.parent.mkdir(parents=True)
    catalog.write_text(
        json.dumps(
            {
                "videos": [],
                "unpublished_selections": [
                    {
                        "concept_id": "night-rain-wind-down",
                        "date_selected": "2026-09-25",
                        "title": "Night Rain Music for Winding Down | 30 Min",
                        "status": "blocked_missing_elevenlabs_key",
                    }
                ],
            }
        )
    )
    result = run_cycle(tmp_path, "2026-10-02", catalog)
    assert result["title"] == "Night Rain Music for Winding Down | 30 Min"
    assert result["purpose"] == "SLEEP"


def test_ready_master_is_not_regenerated(tmp_path, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    catalog = tmp_path / "library" / "catalog.json"
    catalog.parent.mkdir(parents=True)
    catalog.write_text(
        json.dumps(
            {
                "videos": [],
                "unpublished_selections": [
                    {
                        "concept_id": "rainy-focus-working-reading",
                        "date_selected": "2026-10-02",
                        "title": "Rainy Focus Music for Working and Reading | 30 Min",
                        "status": "ready_for_human_review",
                    }
                ],
            }
        )
    )
    result = run_cycle(tmp_path, "2026-10-09", catalog)
    assert result["production_status"] == "waiting_on_human_review"
    assert result["upload_status"] == "PRIVATE"
    assert not (tmp_path / "cycles" / "2026-10-09" / "audio_master.mp3").exists()
    assert not (tmp_path / "cycles" / "2026-10-09" / "FINAL_VIDEO.mp4").exists()


def test_scorecard_lists_ten_candidates(tmp_path, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    run_cycle(tmp_path, "2026-10-02", tmp_path / "library" / "catalog.json")
    scored = json.loads((tmp_path / "cycles" / "2026-10-02" / "candidates.json").read_text())
    assert len(scored) == 10
    assert all(item["total"] == sum(item["scores"].values()) for item in scored)
    assert any(item["concept_id"] == "rainy-focus-working-reading" and item["total"] >= 75 for item in scored)
