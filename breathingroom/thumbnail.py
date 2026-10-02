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
                "fontsize=58:fontcolor=0xF3F0E8@0.94:"
                "x=84:y=h-148:shadowcolor=0x000000@0.28:shadowx=0:shadowy=2"
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
    rainy = "rain" in concept.visual_world.lower()
    pixels = bytearray(WIDTH * HEIGHT * 3)
    for y in range(HEIGHT):
        blend = y / (HEIGHT - 1)
        row_color = tuple(int(top[channel] * (1 - blend) + bottom[channel] * blend) for channel in range(3))
        row = bytes(row_color) * WIDTH
        start = y * WIDTH * 3
        pixels[start : start + WIDTH * 3] = row
    _bokeh(pixels, 980, 230, 86, light, 0.42)
    _bokeh(pixels, 860, 320, 42, light, 0.28)
    _bokeh(pixels, 1100, 390, 24, (170, 186, 196), 0.22)
    if rainy:
        _rain(pixels)
    else:
        _haze(pixels, light)
    header = f"P6\n{WIDTH} {HEIGHT}\n255\n".encode()
    path.write_bytes(header + pixels)


def _bokeh(pixels: bytearray, cx: int, cy: int, radius: int, color: tuple[int, int, int], strength: float) -> None:
    for y in range(max(0, cy - radius), min(HEIGHT, cy + radius)):
        for x in range(max(0, cx - radius), min(WIDTH, cx + radius)):
            distance = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if distance >= radius:
                continue
            amount = (1 - distance / radius) ** 2 * strength
            index = (y * WIDTH + x) * 3
            for channel in range(3):
                pixels[index + channel] = int(pixels[index + channel] * (1 - amount) + color[channel] * amount)


def _rain(pixels: bytearray) -> None:
    seed = 17
    for _ in range(260):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        x = seed % WIDTH
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        y = seed % HEIGHT
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        length = 16 + seed % 34
        for step in range(length):
            xx = x + step // 9
            yy = y + step
            if not (0 <= xx < WIDTH and 0 <= yy < HEIGHT):
                continue
            amount = 0.22 * (1 - step / length)
            index = (yy * WIDTH + xx) * 3
            for channel in range(3):
                pixels[index + channel] = int(pixels[index + channel] * (1 - amount) + 210 * amount)


def _haze(pixels: bytearray, color: tuple[int, int, int]) -> None:
    for y in range(HEIGHT):
        band = 0.08 * (1 - abs((y / HEIGHT) - 0.45) * 2)
        if band <= 0:
            continue
        for x in range(0, WIDTH, 2):
            index = (y * WIDTH + x) * 3
            for channel in range(3):
                pixels[index + channel] = int(pixels[index + channel] * (1 - band) + color[channel] * band)
