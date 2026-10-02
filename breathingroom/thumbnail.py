"""Concept thumbnail: one quiet visual and 2–5 words. This is a designed still, not a frame from footage."""

import subprocess
from pathlib import Path

from breathingroom.concepts import Concept

FONT = "/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf"
WIDTH = 1280
HEIGHT = 720

PALETTES = {
    "FOCUS": ((24, 40, 56), (58, 78, 96), (186, 154, 112)),
    "RELAX": ((48, 36, 32), (120, 78, 52), (214, 176, 130)),
    "MEDITATE": ((30, 40, 44), (78, 96, 98), (186, 196, 190)),
    "SLEEP": ((12, 16, 28), (28, 36, 58), (150, 158, 176)),
}


def render(concept: Concept, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    still = path.with_suffix(".still.ppm")
    _write_ppm(still, concept)
    text_file = path.with_suffix(".txt")
    text_file.write_text(concept.thumbnail_text)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(still),
            "-vf",
            (
                f"drawtext=fontfile={FONT}:textfile={text_file}:"
                "fontsize=52:fontcolor=0xF3F0E8@0.94:"
                "x=88:y=h-108:shadowcolor=0x000000@0.35:shadowx=0:shadowy=2"
            ),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(path),
        ],
        check=True,
        capture_output=True,
    )
    still.unlink(missing_ok=True)
    text_file.unlink(missing_ok=True)
    return path


def _write_ppm(path: Path, concept: Concept) -> None:
    top, bottom, light = PALETTES[concept.purpose]
    pixels = bytearray(WIDTH * HEIGHT * 3)
    rainy = "rain" in concept.visual_world.lower()
    if rainy:
        _rain_window(pixels, concept, top, bottom, light)
    else:
        _landscape(pixels, top, bottom, light)
    header = f"P6\n{WIDTH} {HEIGHT}\n255\n".encode()
    path.write_bytes(header + pixels)


def _rain_window(pixels: bytearray, concept: Concept, top: tuple[int, int, int], bottom: tuple[int, int, int], light: tuple[int, int, int]) -> None:
    night = "night" in concept.visual_world.lower() or concept.purpose == "SLEEP"
    wall = (14, 16, 22) if night else (28, 30, 34)
    _fill(pixels, wall)
    x0, y0, x1, y1 = 72, 48, 1208, 548
    frame = (46, 42, 38) if not night else (22, 24, 30)
    _fill_rect(pixels, x0 - 14, y0 - 14, x1 + 14, y1 + 14, frame)
    glass_top = (18, 24, 38) if night else top
    glass_bottom = (10, 14, 24) if night else bottom
    for y in range(y0, y1):
        blend = (y - y0) / (y1 - y0)
        color = tuple(int(glass_top[channel] * (1 - blend) + glass_bottom[channel] * blend) for channel in range(3))
        _fill_rect(pixels, x0, y, x1, y + 1, color)
    glass = (x0, y0, x1, y1)
    if night:
        _bokeh(pixels, 980, 180, 70, light, 0.35, glass)
        _bokeh(pixels, 860, 260, 36, light, 0.22, glass)
    else:
        _bokeh(pixels, 640, 150, 160, (198, 208, 214), 0.18, glass)
    _rain(pixels, x0 + 8, y0 + 8, x1 - 8, y1 - 8)


def _landscape(pixels: bytearray, top: tuple[int, int, int], bottom: tuple[int, int, int], light: tuple[int, int, int]) -> None:
    for y in range(HEIGHT):
        blend = y / (HEIGHT - 1)
        color = tuple(int(top[channel] * (1 - blend) + bottom[channel] * blend) for channel in range(3))
        _fill_rect(pixels, 0, y, WIDTH, y + 1, color)
    _haze(pixels, light)


def _bokeh(
    pixels: bytearray,
    cx: int,
    cy: int,
    radius: int,
    color: tuple[int, int, int],
    strength: float,
    clip: tuple[int, int, int, int] | None = None,
) -> None:
    for y in range(max(0, cy - radius), min(HEIGHT, cy + radius)):
        for x in range(max(0, cx - radius), min(WIDTH, cx + radius)):
            if clip and not (clip[0] <= x < clip[2] and clip[1] <= y < clip[3]):
                continue
            distance = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if distance >= radius:
                continue
            amount = (1 - distance / radius) ** 2 * strength
            index = (y * WIDTH + x) * 3
            for channel in range(3):
                pixels[index + channel] = int(pixels[index + channel] * (1 - amount) + color[channel] * amount)


def _fill(pixels: bytearray, color: tuple[int, int, int]) -> None:
    _fill_rect(pixels, 0, 0, WIDTH, HEIGHT, color)


def _fill_rect(pixels: bytearray, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int]) -> None:
    row = bytes(color) * (x1 - x0)
    width = len(row)
    for y in range(y0, y1):
        start = (y * WIDTH + x0) * 3
        pixels[start : start + width] = row


def _rain(pixels: bytearray, x0: int, y0: int, x1: int, y1: int) -> None:
    seed = 17
    span_x = x1 - x0
    span_y = y1 - y0
    for _ in range(420):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        x = x0 + seed % span_x
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        y = y0 + seed % span_y
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        length = 22 + seed % 48
        for step in range(length):
            xx = x + step // 10
            yy = y + step
            if not (x0 <= xx < x1 and y0 <= yy < y1):
                continue
            amount = 0.45 * (1 - step / length)
            index = (yy * WIDTH + xx) * 3
            for channel in range(3):
                pixels[index + channel] = int(pixels[index + channel] * (1 - amount) + 226 * amount)


def _haze(pixels: bytearray, color: tuple[int, int, int]) -> None:
    for y in range(HEIGHT):
        band = 0.08 * (1 - abs((y / HEIGHT) - 0.45) * 2)
        if band <= 0:
            continue
        for x in range(0, WIDTH, 2):
            index = (y * WIDTH + x) * 3
            for channel in range(3):
                pixels[index + channel] = int(pixels[index + channel] * (1 - band) + color[channel] * band)
