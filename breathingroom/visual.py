"""Extend one visual world to the length of the master.

Rain, streams, and ocean are not reversed. A hard restart of a short clip is not used.
"""

import subprocess
from pathlib import Path


class VisualError(RuntimeError):
    pass


REVERSIBLE_WORDS = ("cloud", "mist", "fog", "horizon")
DIRECTED_MOTION = ("rain", "stream", "ocean", "waterfall", "wave")


def reverse_allowed(visual_world: str) -> bool:
    text = visual_world.lower()
    if any(word in text for word in DIRECTED_MOTION):
        return False
    return any(word in text for word in REVERSIBLE_WORDS)


def extend_plate(
    source: Path,
    output: Path,
    target_seconds: float,
    visual_world: str,
    allow_reverse: bool = False,
) -> dict:
    if allow_reverse and not reverse_allowed(visual_world):
        raise VisualError(f"reversing is not believable for this picture: {visual_world}")
    source_duration = _duration(source)
    fade = min(2.0, source_duration / 5)
    if fade < 0.3:
        raise VisualError("visual plate is too short to crossfade")
    output.parent.mkdir(parents=True, exist_ok=True)
    unit = output.with_name(output.stem + "-unit.mp4")
    offset = source_duration - fade
    zoom = "scale=iw*1.04:ih*1.04,crop=iw/1.04:ih/1.04,setsar=1"
    reverse = "reverse," if allow_reverse else ""
    graph = (
        f"[0:v]split[base][alt];"
        f"[alt]{reverse}{zoom}setpts=PTS-STARTPTS[zoomed];"
        f"[base]setpts=PTS-STARTPTS[main];"
        f"[main][zoomed]xfade=transition=fade:duration={fade:.3f}:offset={offset:.3f},format=yuv420p[v]"
    )
    _run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-filter_complex",
            graph,
            "-map",
            "[v]",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "20",
            str(unit),
        ]
    )
    _run(
        [
            "ffmpeg",
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            str(unit),
            "-t",
            f"{target_seconds:.3f}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "20",
            "-an",
            str(output),
        ]
    )
    unit.unlink(missing_ok=True)
    duration = _duration(output)
    return {
        "output": str(output),
        "duration": duration,
        "reversed": allow_reverse,
        "source_duration": source_duration,
    }


def _duration(path: Path) -> float:
    result = subprocess.run(
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


def _run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise VisualError(result.stderr[-1500:])
