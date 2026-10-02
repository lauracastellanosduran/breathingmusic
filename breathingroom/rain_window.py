"""One rainy window for the whole video.

The plate is an original still. Rain is drawn as seamless textures and scrolled
downward. The picture is never reversed, and it is not a short clip restarted
from the top.
"""

import subprocess
from pathlib import Path

import numpy as np

from breathingroom.visual import VisualError


def rain_window_supported(visual_world: str) -> bool:
    text = visual_world.lower()
    return "rain" in text and "window" in text


def render_rain_window(
    plate: Path,
    output: Path,
    target_seconds: float,
    size: tuple[int, int] = (1280, 720),
    fps: int = 24,
    encoder: list[str] | None = None,
) -> dict:
    if target_seconds <= 0:
        raise VisualError("rain window duration must be positive")
    if not plate.exists():
        raise VisualError(f"rain window plate is missing: {plate}")
    width, height = size
    output.parent.mkdir(parents=True, exist_ok=True)
    work = output.parent / f".{output.stem}-rain"
    work.mkdir(parents=True, exist_ok=True)
    layers = _layers(width, height)
    paths = []
    for index, layer in enumerate(layers):
        path = work / f"layer_{index}.png"
        _write_png(path, layer["image"])
        paths.append(path)
    graph = _graph(
        width,
        height,
        [layer["speed"] for layer in layers],
        fps,
        [int(layer["image"].shape[0]) for layer in layers],
    )
    command = ["ffmpeg", "-y", "-loop", "1", "-framerate", str(fps), "-i", str(plate)]
    for path in paths:
        command.extend(["-loop", "1", "-framerate", str(fps), "-i", str(path)])
    command.extend(
        [
            "-filter_complex",
            graph,
            "-map",
            "[v]",
            "-t",
            f"{target_seconds:.3f}",
            "-an",
            "-r",
            str(fps),
            *(encoder or _default_encoder()),
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    _run(command)
    for path in paths:
        path.unlink(missing_ok=True)
    work.rmdir()
    return {
        "output": str(output),
        "duration": _duration(output),
        "reversed": False,
        "filter_graph": graph,
        "periods_seconds": [round(layer["period"], 3) for layer in layers],
        "source": str(plate),
    }


def _default_encoder() -> list[str]:
    # Capped so a half-hour picture stays under the repository file limit.
    return [
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "32",
        "-maxrate",
        "300k",
        "-bufsize",
        "600k",
        "-pix_fmt",
        "yuv420p",
    ]


def _layers(width: int, height: int) -> list[dict]:
    """Tall seamless maps so one layer does not repeat inside a half hour."""

    specs = (
        {"repeats": 8, "speed": 48, "count": 110, "length": (36, 90), "alpha": (120, 190), "seed": 11},
        {"repeats": 8, "speed": 19, "count": 36, "length": (80, 170), "alpha": (90, 160), "seed": 29},
    )
    layers = []
    for spec in specs:
        texture_height = height * spec["repeats"]
        count = max(1, int(spec["count"] * texture_height / height))
        image = _streaks(
            width,
            texture_height,
            count=count,
            length=spec["length"],
            alpha=spec["alpha"],
            seed=spec["seed"],
        )
        layers.append(
            {
                "image": image,
                "speed": spec["speed"],
                "period": texture_height / spec["speed"],
            }
        )
    return layers


def _streaks(
    width: int,
    height: int,
    count: int,
    length: tuple[int, int],
    alpha: tuple[int, int],
    seed: int,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    image = np.zeros((height, width, 4), dtype=np.uint8)
    for _ in range(count):
        streak_length = int(rng.integers(length[0], length[1]))
        origin_x = int(rng.integers(0, width))
        origin_y = int(rng.integers(0, height))
        strength = int(rng.integers(alpha[0], alpha[1]))
        slant = int(rng.integers(8, 16))
        steps = np.arange(streak_length)
        xs = (origin_x + steps // slant) % width
        ys = (origin_y + steps) % height
        fade = np.linspace(strength, max(8, strength // 5), streak_length).astype(np.uint8)
        color = np.array([232, 236, 238], dtype=np.uint8)
        for offset in (-1, 0, 1):
            columns = (xs + offset) % width
            image[ys, columns, 0:3] = color
            image[ys, columns, 3] = np.maximum(image[ys, columns, 3], fade if offset == 0 else fade // 3)
    return image


def _graph(width: int, height: int, speeds: list[int], fps: int, texture_heights: list[int]) -> str:
    margin_w = max(24, width // 18)
    margin_h = max(16, height // 22)
    parts = [
        (
            f"[0:v]scale={width + margin_w * 2}:{height + margin_h * 2}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height}:"
            f"x='(in_w-{width})/2+{max(4, margin_w // 5)}*sin(t/340)':"
            f"y='(in_h-{height})/2+{max(3, margin_h // 6)}*sin(t/460)',"
            f"fps={fps},setsar=1,format=yuv420p[bg]"
        )
    ]
    previous = "bg"
    for index, (speed, texture_height) in enumerate(zip(speeds, texture_heights)):
        # scroll wraps a seamless texture. Negative moves the streaks downward.
        fraction = speed / (texture_height * fps)
        label = "v" if index == len(speeds) - 1 else f"m{index}"
        parts.append(
            f"[{index + 1}:v]format=rgba,scroll=vertical={-fraction:.8f},"
            f"crop={width}:{height}:0:0,format=rgba[rain{index}]"
        )
        parts.append(
            f"[{previous}][rain{index}]overlay=0:0:format=auto,format=yuv420p[{label}]"
        )
        previous = label
    return ";".join(parts)


def _write_png(path: Path, image: np.ndarray) -> None:
    height, width, channels = image.shape
    if channels != 4:
        raise VisualError("rain texture must be rgba")
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgba",
            "-s",
            f"{width}x{height}",
            "-i",
            "pipe:",
            "-frames:v",
            "1",
            str(path),
        ],
        input=image.tobytes(),
        capture_output=True,
    )
    if result.returncode != 0:
        raise VisualError(result.stderr[-800:].decode("utf-8", errors="replace"))


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
