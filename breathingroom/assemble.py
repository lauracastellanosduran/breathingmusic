"""Join section files into one continuous master. No hard cuts, no looped repeats."""

import subprocess
from pathlib import Path

from breathingroom.rules import CROSSFADE_SECONDS, FINAL_FADE_SECONDS


class AssembleError(RuntimeError):
    pass


def assemble(
    sections: list[Path],
    output: Path,
    crossfade_seconds: float = CROSSFADE_SECONDS,
    final_fade_seconds: float = FINAL_FADE_SECONDS,
) -> dict:
    if len(sections) != 3:
        raise AssembleError("a 30-minute master is built from exactly 3 sections")
    durations = [_duration(path) for path in sections]
    if any(duration <= crossfade_seconds for duration in durations):
        raise AssembleError("each section must be longer than the crossfade")
    gains = _match_gains(sections)
    total = sum(durations) - crossfade_seconds * (len(sections) - 1)
    fade_start = max(0.0, total - final_fade_seconds)
    output.parent.mkdir(parents=True, exist_ok=True)
    filter_graph = ";".join(
        (
            f"[0:a]volume={gains[0]}dB[a0]",
            f"[1:a]volume={gains[1]}dB[a1]",
            f"[2:a]volume={gains[2]}dB[a2]",
            f"[a0][a1]acrossfade=d={crossfade_seconds}:c1=tri:c2=tri[a01]",
            (
                f"[a01][a2]acrossfade=d={crossfade_seconds}:c1=tri:c2=tri,"
                f"afade=t=out:st={fade_start:.3f}:d={final_fade_seconds}:curve=tri[out]"
            ),
        )
    )
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(sections[0]),
        "-i",
        str(sections[1]),
        "-i",
        str(sections[2]),
        "-filter_complex",
        filter_graph,
        "-map",
        "[out]",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-ac",
        "2",
        str(output),
    ]
    _run(command)
    return {
        "output": str(output),
        "section_durations": durations,
        "gains_db": gains,
        "crossfade_seconds": crossfade_seconds,
        "final_fade_seconds": final_fade_seconds,
        "expected_duration": total,
        "duration": _duration(output),
    }


def _match_gains(sections: list[Path]) -> list[float]:
    means = [_mean_volume(path) for path in sections]
    peaks = [_max_volume(path) for path in sections]
    target = min(means)
    gains = [target - mean for mean in means]
    hottest = max(peak + gain for peak, gain in zip(peaks, gains))
    if hottest > -1.5:
        trim = -1.5 - hottest
        gains = [gain + trim for gain in gains]
    return [round(gain, 2) for gain in gains]


def _mean_volume(path: Path) -> float:
    return _volume_stat(path, "mean_volume")


def _max_volume(path: Path) -> float:
    return _volume_stat(path, "max_volume")


def _volume_stat(path: Path, key: str) -> float:
    result = _run(
        [
            "ffmpeg",
            "-i",
            str(path),
            "-af",
            "volumedetect",
            "-f",
            "null",
            "-",
        ]
    )
    for line in result.stderr.splitlines():
        if key in line:
            return float(line.rsplit(":", 1)[1].replace("dB", "").strip())
    raise AssembleError(f"could not read {key} for {path}")


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


def _run(command: list[str]) -> subprocess.CompletedProcess:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise AssembleError(result.stderr[-1500:])
    return result
