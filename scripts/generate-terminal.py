"""Generate the profile's looping Braille Docker whale banner. Requires Pillow.

Run: python scripts/generate-terminal.py
Override the Windows font defaults with --mono-font and --sans-font.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 1000, 500
COLORS = {
    "background": "#090D17", "panel": "#101624", "border": "#26334A",
    "muted": "#94A3B8", "text": "#E2E8F0", "mint": "#6EE7B7",
    "purple": "#C4B5FD", "blue": "#7DD3FC",
}


def whale_mask(index: int) -> Image.Image:
    """Draw a small code-native silhouette, then sample it into Braille cells."""
    mask = Image.new("L", (170, 124))
    draw = ImageDraw.Draw(mask)
    for x, y in [(85, 4), (37, 27), (61, 27), (85, 27),
                 (13, 50), (37, 50), (61, 50), (85, 50), (109, 50)]:
        draw.rectangle((x, y, x + 16, y + 16), fill=255)
        # Container ribs stay visible in the dense dot pattern.
        for rib in (5, 11):
            draw.line((x + rib, y + 2, x + rib, y + 14), fill=0)

    tail = 4 * math.sin(index * 4 * math.pi / 48)

    def curve(start, control1, control2, end):
        points = []
        for step in range(21):
            t = step / 20
            points.append(tuple((1-t)**3 * start[k] + 3*(1-t)**2*t * control1[k]
                                + 3*(1-t)*t*t * control2[k] + t**3 * end[k]
                                for k in (0, 1)))
        return points

    hull = [(4, 74), (111, 74)]
    hull += curve((111, 74), (126, 74), (121, 54 + tail), (132, 52 + tail))
    hull += curve((132, 52 + tail), (142, 51 + tail), (138, 69), (152, 73))
    hull += [(167, 81), (158, 87)]
    hull += curve((158, 87), (148, 94), (136, 88), (126, 95))
    hull += curve((126, 95), (108, 121), (80, 125), (43, 116))
    hull += curve((43, 116), (18, 111), (1, 93), (4, 74))
    draw.polygon(hull, fill=255)

    mouth = [(12, 89), (98, 89), (112, 85), (138, 83), (122, 93), (113, 97)]
    mouth += curve((113, 97), (102, 113), (74, 119), (45, 110))
    mouth += curve((45, 110), (27, 106), (17, 98), (12, 89))
    draw.polygon(mouth, fill=0)
    if index in (15, 16, 39, 40):
        draw.line((17, 81, 21, 81), fill=0, width=2)
    else:
        draw.ellipse((17, 79, 21, 83), fill=0)
    return mask.resize((100, 72), Image.Resampling.NEAREST)


def braille_text(mask: Image.Image) -> str:
    bits = ((1, 8), (2, 16), (4, 32), (64, 128))
    lines = []
    for y in range(0, mask.height, 4):
        line = ""
        for x in range(0, mask.width, 2):
            value = sum(bits[row][col] for row in range(4) for col in range(2)
                        if mask.getpixel((x + col, y + row)))
            line += chr(0x2800 + value)
        lines.append(line.rstrip(chr(0x2800)))
    return "\n".join(lines) + "\n"


def render_whale(index: int) -> Image.Image:
    """Render Unicode Braille dot positions directly without font dependencies."""
    mask = whale_mask(index)
    art = Image.new("RGBA", (704, 474))
    draw = ImageDraw.Draw(art)
    dot_colors = ("#A7CBE3", "#B5D9EB", "#86B6D3", "#E7D5B3")
    for y in range(mask.height):
        for x in range(mask.width):
            if not mask.getpixel((x, y)):
                continue
            dx = 2 * (x // 2 * 7 + x % 2 * 3 + 2)
            dy = 2 * (y // 4 * 13 + y % 4 * 3 + 2)
            color = dot_colors[(x * 7 + y * 11) % len(dot_colors)]
            draw.ellipse((dx - 1.7, dy - 1.7, dx + 1.7, dy + 1.7), fill=color)
    return art.resize((352, 237), Image.Resampling.LANCZOS)


def add_whale(frame: Image.Image, index: int, origin: tuple[int, int]) -> None:
    phase = 2 * math.pi * index / 48
    whale_x = origin[0] + round(8 * math.sin(phase))
    whale_y = origin[1] + round(4 * math.cos(phase))
    art = render_whale(index)
    frame.paste(art, (whale_x, whale_y), art)
    draw = ImageDraw.Draw(frame)
    # Dotted bubble rings drift away from the nose and rise toward the surface.
    for offset in (0, 16, 32):
        age = ((index + offset) % 48) / 48
        cx = whale_x - 10 - round(20 * age)
        cy = whale_y + 151 - round(75 * age)
        radius = 2 + 2 * age
        for dot in range(6):
            angle = dot * math.pi / 3
            dx, dy = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
            draw.ellipse((dx - .6, dy - .6, dx + .6, dy + .6), fill=COLORS["blue"])


def make_frame(index: int, mono_path: str, sans_path: str) -> Image.Image:
    frame = Image.new("RGB", (WIDTH, HEIGHT), COLORS["background"])
    draw = ImageDraw.Draw(frame)
    mono = ImageFont.truetype(mono_path, 18)
    diagram_font = ImageFont.truetype(mono_path, 24)
    small = ImageFont.truetype(mono_path, 15)
    name_font = ImageFont.truetype(sans_path, 39)
    body_font = ImageFont.truetype(sans_path, 20)

    draw.rounded_rectangle((16, 16, 984, 484), radius=18,
                           fill=COLORS["panel"], outline=COLORS["border"], width=1)
    draw.line((17, 62, 982, 62), fill=COLORS["border"], width=1)
    for x, color in zip((42, 64, 86), ("#F87171", "#FBBF24", "#6EE7B7")):
        draw.ellipse((x - 5, 35, x + 5, 45), fill=color)
    draw.text((115, 30), "techmonoway / backend-lab", font=small, fill=COLORS["muted"])
    draw.text((785, 30), "BRAILLE / DOCKER", font=small, fill=COLORS["mint"])
    draw.text((48, 108), '$ whoami --curious', font=mono, fill=COLORS["mint"])
    draw.text((47, 142), "Ky Tri Nguyen", font=name_font, fill=COLORS["text"])
    draw.text((49, 202), "Backend Engineer / Vietnam", font=body_font, fill=COLORS["blue"])
    draw.text((49, 237), "build thoughtfully. keep learning.", font=mono,
              fill=COLORS["muted"])

    add_whale(frame, index, (576, 76))

    draw.line((48, 326, 952, 326), fill=COLORS["border"], width=1)
    draw.text((49, 342), "REQUEST FLOW / DEMO", font=small, fill=COLORS["muted"])
    diagram = [
        "+---------------+       +---------------+       +---------------+",
        "|      API      | ----> |    SERVICE    | ----> |   DATABASE    |",
        "+---------------+       +---------------+       +---------------+",
    ]
    origin_x, origin_y = 49, 365
    char_width = diagram_font.getlength("M")
    for line_no, line in enumerate(diagram):
        draw.text((origin_x, origin_y + line_no * 26), line, font=diagram_font,
                  fill=COLORS["blue"])

    # Moving packets follow the arrows without flashing the background.
    progress = (index % 24) / 24
    for start_column, color in ((18, COLORS["mint"]), (42, COLORS["purple"])):
        x = origin_x + (start_column + math.floor(progress * 5)) * char_width
        draw.rectangle((x, origin_y + 29, x + char_width - 1, origin_y + 51),
                       fill=COLORS["panel"])
        draw.text((x, origin_y + 26), ">", font=diagram_font, fill=color)

    draw.text((49, 452), "$ build > learn > ship", font=small, fill=COLORS["mint"])
    if (index // 6) % 2 == 0:
        draw.text((275, 452), "_", font=small, fill=COLORS["mint"])
    draw.text((772, 452), "coffee-powered", font=small, fill=COLORS["muted"])
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mono-font", default="C:/Windows/Fonts/consola.ttf")
    parser.add_argument("--sans-font", default="C:/Windows/Fonts/segoeuib.ttf")
    args = parser.parse_args()
    frames = [make_frame(i, args.mono_font, args.sans_font) for i in range(48)]
    # A shared palette keeps text edges and colors stable between frames.
    palette = frames[0].quantize(colors=128)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    output = ROOT / "assets" / "backend-terminal.gif"
    output.parent.mkdir(parents=True, exist_ok=True)
    indexed[0].save(output, save_all=True, append_images=indexed[1:],
                    duration=110, loop=0, optimize=True, disposal=1)
    print(f"Generated {output.name}: {len(indexed)} frames, {output.stat().st_size:,} bytes")
    standalone = []
    for index in range(48):
        frame = Image.new("RGB", (440, 300), COLORS["panel"])
        add_whale(frame, index, (50, 30))
        standalone.append(frame)
    whale_palette = standalone[0].quantize(colors=64)
    whale_frames = [frame.quantize(palette=whale_palette, dither=Image.Dither.NONE)
                    for frame in standalone]
    whale_output = output.with_name("docker-whale-swim.gif")
    whale_frames[0].save(whale_output, save_all=True, append_images=whale_frames[1:],
                         duration=110, loop=0, optimize=True, disposal=1)
    output.with_name("docker-whale-braille.txt").write_text(braille_text(whale_mask(0)), encoding="utf-8")
    print(f"Generated {whale_output.name}: {whale_output.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
