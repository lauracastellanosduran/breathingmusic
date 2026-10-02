"""Automated audio inspection. Hearing the musical world still requires a person."""

import json
import subprocess
import wave
from array import array
from pathlib import Path

from breathingroom.rules import (
    DURATION_MAX_SECONDS,
    DURATION_MIN_SECONDS,
    QA_FRAME_TIMES,
    QA_SAMPLE_TIMES,
)


def inspect_audio(
    path: Path,
    duration_min: float = DURATION_MIN_SECONDS,
    duration_max: float = DURATION_MAX_SECONDS,
    window_seconds: float = 10.0,
    jump_db: float = 6.0,
    silence_seconds: float = 2.0,
    silence_db: float = -60.0,
) -> dict:
    duration = _duration(path)
    peak_db = _max_volume(path)
    windows = _rms_windows(path, window_seconds)
    inspect_until = _inspect_until(duration)
    silence = _silence_runs(windows, window_seconds, silence_db, silence_seconds, inspect_until)
    jumps = _jumps(windows, window_seconds, jump_db, inspect_until)
    checks = {
        "duration_in_range": duration_min <= duration <= duration_max,
        "no_clipping": peak_db < -0.5,
        "no_unexpected_silence": not silence,
        "no_major_loudness_jumps": not jumps,
        "ending_is_present": duration > 1,
    }
    return {
        "path": str(path),
        "duration_seconds": round(duration, 3),
        "peak_db": peak_db,
        "checks": checks,
        "passed": all(checks.values()),
        "silence": silence,
        "loudness_jumps": jumps,
        "vocals": "human_review_required",
        "musical_continuity": "human_review_required",
        "sample_times": list(QA_SAMPLE_TIMES),
    }


def inspect_video(path: Path, frame_dir: Path) -> dict:
    info = _video_info(path)
    frames = extract_frames(path, frame_dir)
    ratio = info["width"] / info["height"] if info["height"] else 0
    checks = {
        "duration_in_range": DURATION_MIN_SECONDS <= info["duration"] <= DURATION_MAX_SECONDS,
        "aspect_16_9": abs(ratio - (16 / 9)) < 0.02,
        "audio_present": info["has_audio"],
        "visual_present": info["has_video"] and bool(frames),
        "no_black_frames": all(frame["y_avg"] > 12 for frame in frames),
    }
    return {
        "ran": True,
        "path": str(path),
        "duration_seconds": round(info["duration"], 3),
        "width": info["width"],
        "height": info["height"],
        "aspect": "16:9" if checks["aspect_16_9"] else f"{info['width']}x{info['height']}",
        "checks": checks,
        "passed": all(checks.values()),
        "frames": frames,
        "frame_times": list(QA_FRAME_TIMES),
        "opening_text": "none",
        "reversed": False,
    }


def extract_frames(path: Path, directory: Path) -> list[dict]:
    directory.mkdir(parents=True, exist_ok=True)
    duration = _duration(path)
    frames = []
    for stamp in QA_FRAME_TIMES:
        start = _stamp_seconds(stamp)
        if start >= duration:
            continue
        target = directory / f"frame_{stamp.replace(':', '')}.jpg"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                stamp,
                "-i",
                str(path),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(target),
            ],
            check=True,
            capture_output=True,
        )
        frames.append({"time": stamp, "path": str(target), "y_avg": _y_avg(target)})
    return frames


def extract_samples(path: Path, directory: Path, seconds: float = 15.0) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    duration = _duration(path)
    written = []
    for stamp in QA_SAMPLE_TIMES:
        start = _stamp_seconds(stamp)
        if start >= duration:
            continue
        target = directory / f"sample_{stamp.replace(':', '')}.mp3"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                stamp,
                "-i",
                str(path),
                "-t",
                str(seconds),
                "-c:a",
                "libmp3lame",
                "-q:a",
                "4",
                str(target),
            ],
            check=True,
            capture_output=True,
        )
        written.append(str(target))
    return written


def _rms_windows(path: Path, window_seconds: float) -> list[float]:
    wav_path = path.with_suffix(".qa.wav")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(path),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(wav_path),
        ],
        check=True,
        capture_output=True,
    )
    levels = []
    try:
        with wave.open(str(wav_path), "rb") as handle:
            rate = handle.getframerate()
            window = int(rate * window_seconds)
            while True:
                frames = handle.readframes(window)
                if not frames:
                    break
                samples = array("h")
                samples.frombytes(frames)
                if not samples:
                    break
                square = sum(sample * sample for sample in samples) / len(samples)
                rms = (square ** 0.5) / 32768
                levels.append(20 * _log10(max(rms, 1e-9)))
    finally:
        wav_path.unlink(missing_ok=True)
    return levels


def _inspect_until(duration: float) -> float:
    """Leave the final fade out of the silence and jump checks on a full-length master."""

    if duration > 120:
        return duration - 60
    return duration


def _silence_runs(windows, window_seconds, silence_db, silence_seconds, inspect_until) -> list[dict]:
    runs = []
    start = None
    for index, level in enumerate(windows):
        at = index * window_seconds
        if at >= inspect_until:
            break
        if level <= silence_db:
            if start is None:
                start = at
        elif start is not None:
            if at - start >= silence_seconds:
                runs.append({"start": start, "end": at})
            start = None
    if start is not None and inspect_until - start >= silence_seconds:
        runs.append({"start": start, "end": inspect_until})
    return runs


def _jumps(windows, window_seconds, jump_db, inspect_until) -> list[dict]:
    found = []
    for index in range(1, len(windows)):
        at = index * window_seconds
        if at >= inspect_until:
            break
        delta = abs(windows[index] - windows[index - 1])
        if delta >= jump_db:
            found.append({"at": at, "delta_db": round(delta, 2)})
    return found


def _max_volume(path: Path) -> float:
    result = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    for line in result.stderr.splitlines():
        if "max_volume" in line:
            return float(line.rsplit(":", 1)[1].replace("dB", "").strip())
    raise RuntimeError(f"could not read peak for {path}")


def _video_info(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,width,height",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    width = 0
    height = 0
    has_video = False
    has_audio = False
    for stream in payload.get("streams", []):
        if stream.get("codec_type") == "video":
            has_video = True
            width = int(stream.get("width") or 0)
            height = int(stream.get("height") or 0)
        if stream.get("codec_type") == "audio":
            has_audio = True
    return {
        "duration": float(payload["format"]["duration"]),
        "width": width,
        "height": height,
        "has_video": has_video,
        "has_audio": has_audio,
    }


def _y_avg(path: Path) -> float:
    result = subprocess.run(
        [
            "ffmpeg",
            "-i",
            str(path),
            "-vf",
            "signalstats,metadata=print:file=-",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    for line in result.stderr.splitlines() + result.stdout.splitlines():
        if "YAVG" in line:
            return float(line.rsplit("=", 1)[1])
    raise RuntimeError(f"could not read brightness for {path}")


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


def _stamp_seconds(stamp: str) -> float:
    minutes, seconds = stamp.split(":")
    return int(minutes) * 60 + int(seconds)


def _log10(value: float) -> float:
    import math

    return math.log10(value)
