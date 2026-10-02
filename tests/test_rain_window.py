import subprocess
from pathlib import Path

from breathingroom.rain_window import rain_window_supported, render_rain_window


def test_rain_on_a_window_can_be_rendered_here():
    assert rain_window_supported("Rain moving slowly across a large window")
    assert not rain_window_supported("Slow clouds over a quiet field")


def test_rain_window_scrolls_down_without_reversing(tmp_path: Path):
    plate = tmp_path / "plate.jpg"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=0x334455:s=160x90:d=1",
            "-frames:v",
            "1",
            str(plate),
        ],
        check=True,
        capture_output=True,
    )
    output = tmp_path / "rain.mp4"
    result = render_rain_window(plate, output, 1.2, size=(160, 90), fps=8)
    assert result["reversed"] is False
    assert "reverse" not in result["filter_graph"]
    assert "scroll=vertical=" in result["filter_graph"]
    assert 1.0 < result["duration"] < 1.5
    assert min(result["periods_seconds"]) > 10
