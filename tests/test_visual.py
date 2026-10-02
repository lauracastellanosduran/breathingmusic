import subprocess
from pathlib import Path

import pytest

from breathingroom.visual import VisualError, extend_plate


def test_plate_extension_reaches_the_target_without_reversing_rain(tmp_path: Path):
    source = tmp_path / "plate.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=0x223344:s=320x180:d=3",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(source),
        ],
        check=True,
        capture_output=True,
    )
    output = tmp_path / "visual.mp4"
    world = "Rain moving slowly across a large window"
    with pytest.raises(VisualError):
        extend_plate(source, output, 5, world, allow_reverse=True)
    result = extend_plate(source, output, 5, world, allow_reverse=False)
    assert result["reversed"] is False
    assert 4.8 < result["duration"] < 5.3
