import subprocess
from pathlib import Path

from breathingroom.assemble import assemble
from breathingroom.elevenlabs import compose
from breathingroom.qa import inspect_audio


def _tone(path: Path, frequency: int, duration: float, volume_db: float) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={frequency}:duration={duration}:sample_rate=48000",
            "-af",
            f"volume={volume_db}dB",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "128k",
            str(path),
        ],
        check=True,
        capture_output=True,
    )


def test_three_sections_crossfade_into_one_master(tmp_path: Path):
    sections = []
    for index, volume in enumerate((-6, -14, -10)):
        path = tmp_path / f"section_{index}.mp3"
        _tone(path, 220, 3, volume)
        sections.append(path)
    master = tmp_path / "audio_master.mp3"
    result = assemble(sections, master, crossfade_seconds=0.5, final_fade_seconds=0.4)
    assert master.exists()
    assert 7.5 < result["duration"] < 8.5
    report = inspect_audio(master, duration_min=7.5, duration_max=8.5, window_seconds=0.5, jump_db=8)
    assert report["checks"]["no_clipping"] is True
    assert report["checks"]["no_major_loudness_jumps"] is True
    assert report["checks"]["no_unexpected_silence"] is True
    assert report["vocals"] == "human_review_required"


def test_silence_and_clipping_fail_inspection(tmp_path: Path):
    silent = tmp_path / "gap.mp3"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=220:duration=1:sample_rate=48000",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=48000:cl=mono:d=3",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=220:duration=1:sample_rate=48000",
            "-filter_complex",
            "[0][1][2]concat=n=3:v=0:a=1,volume=-8dB",
            "-c:a",
            "libmp3lame",
            str(silent),
        ],
        check=True,
        capture_output=True,
    )
    silence_report = inspect_audio(silent, duration_min=0, duration_max=20, window_seconds=0.5, silence_seconds=1.5)
    assert silence_report["checks"]["no_unexpected_silence"] is False

    loud = tmp_path / "loud.mp3"
    _tone(loud, 220, 1.5, 0)
    loud_report = inspect_audio(loud, duration_min=0, duration_max=20, window_seconds=0.5)
    assert loud_report["checks"]["no_clipping"] is False


def test_compose_request_forces_instrumental(monkeypatch):
    captured = {}

    class Response:
        def read(self):
            return b"mp3"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = request.data
        captured["headers"] = dict(request.header_items())
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    audio = compose("Instrumental ambient music for quiet work.\nNo vocals.", duration_ms=600000, timeout=12)
    assert audio == b"mp3"
    assert "force_instrumental" in captured["body"].decode()
    assert '"force_instrumental": true' in captured["body"].decode()
    assert "xi-api-key" in {key.lower() for key in captured["headers"]}
    assert "test-key" not in captured["url"]
